"""
Product Search Agent - Handles product discovery and information retrieval.
Converted to React agent using LangGraph's create_react_agent with tool binding.
"""
import logging
import json
import re
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from langchain_aws import ChatBedrock
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from app.workflows.state import AgentState
from app.tools.product_search_tools import execute_product_search, set_db_session, execute_product_search_raw
from app.core.llm import llm

logger = logging.getLogger(__name__)

# CLAUDE_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"


def get_schema_context() -> str:
    return """
DATABASE SCHEMA:

Table: products
- id (INTEGER, PRIMARY KEY)
- title (STRING)
- description (STRING)
- price (INTEGER)
- base_price (FLOAT)
- discount_percentage (FLOAT)
- rating (FLOAT)
- stock (INTEGER)
- brand (STRING)
- thumbnail (STRING)
- images (ARRAY of STRING)
- category_id (INTEGER)
- is_published (BOOLEAN)
- is_dynamic_pricing_active (BOOLEAN)
- dynamic_price (FLOAT)
- created_at (TIMESTAMP)

Table: categories
- id (INTEGER, PRIMARY KEY)
- name (STRING)


IMPORTANT SQL RULES:
1. ONLY generate SELECT queries - no INSERT, UPDATE, DELETE, DROP, etc.
2. Always JOIN products with categories to get category name
3. Use ILIKE for case-insensitive text matching (PostgreSQL)
4. Select ALL product fields needed for product cards: id, title, description, price, discount_percentage, rating, stock, brand, thumbnail, categories.name as category_name
5. Filter by is_published = true to show only published products
6. Limit results to 20 products maximum
7. Use ORDER BY for better relevance (rating DESC, price ASC, etc.)

SEARCH STRATEGY GUIDELINES:

**Generalized Search Logic:**
- For BROAD queries (1-2 words like "face products", "moisturizers"), use OR logic across multiple fields
- For SPECIFIC queries (brand + type like "cerave moisturizer"), use AND logic for precision
- Always search in: category name, product title, AND product description
- Use relevance scoring with CASE statements to rank results

**Query Pattern Examples:**

BROAD QUERY - "face products":
Use OR logic to cast a wide net:
```sql
WHERE (
    c.name ILIKE '%face%' OR 
    c.name ILIKE '%facial%' OR
    c.name ILIKE '%skin%' OR
    p.title ILIKE '%face%' OR
    p.description ILIKE '%face%'
)
ORDER BY p.rating DESC
```

MEDIUM QUERY - "moisturizers" or "face moisturizers":
Use OR logic with relevance scoring:
```sql
SELECT ..., 
    (CASE 
        WHEN p.title ILIKE '%moisturizer%' AND p.title ILIKE '%face%' THEN 10
        WHEN p.title ILIKE '%moisturizer%' THEN 8
        WHEN c.name ILIKE '%moisturizer%' THEN 6
        WHEN p.description ILIKE '%moisturizer%' THEN 4
        ELSE 0
    END) as relevance_score
WHERE (
    c.name ILIKE '%moisturizer%' OR
    c.name ILIKE '%cream%' OR
    p.title ILIKE '%moisturizer%' OR
    p.title ILIKE '%lotion%' OR
    p.description ILIKE '%moisturizer%'
)
ORDER BY relevance_score DESC, p.rating DESC
```

SPECIFIC QUERY - "cerave face moisturizer":
Use AND logic for exact matching:
```sql
WHERE (
    (p.title ILIKE '%cerave%' OR p.brand ILIKE '%cerave%')
    AND (p.title ILIKE '%moisturizer%' OR p.description ILIKE '%moisturizer%')
    AND (p.title ILIKE '%face%' OR c.name ILIKE '%face%' OR p.description ILIKE '%face%')
)
ORDER BY p.rating DESC
```

**Keyword Expansion:**
Expand user keywords to related terms:
- "moisturizer" → "moisturizer", "cream", "lotion", "hydrating"
- "face" → "face", "facial", "skin"
- "laptop" → "laptop", "notebook", "computer"
- "phone" → "phone", "smartphone", "mobile"

EXAMPLE QUERIES:

User: "show me face products"
SQL: SELECT p.id, p.title, p.description, p.price, p.discount_percentage, p.rating, p.stock, p.brand, p.thumbnail, c.name as category_name FROM products p JOIN categories c ON p.category_id = c.id WHERE (c.name ILIKE '%face%' OR c.name ILIKE '%facial%' OR c.name ILIKE '%skin%' OR p.title ILIKE '%face%' OR p.description ILIKE '%face%') AND p.is_published = true ORDER BY p.rating DESC LIMIT 20

User: "moisturizers"
SQL: SELECT p.id, p.title, p.description, p.price, p.discount_percentage, p.rating, p.stock, p.brand, p.thumbnail, c.name as category_name, (CASE WHEN p.title ILIKE '%moisturizer%' THEN 10 WHEN c.name ILIKE '%moisturizer%' THEN 8 WHEN p.description ILIKE '%moisturizer%' THEN 6 ELSE 0 END) as relevance_score FROM products p JOIN categories c ON p.category_id = c.id WHERE (c.name ILIKE '%moisturizer%' OR c.name ILIKE '%cream%' OR c.name ILIKE '%lotion%' OR p.title ILIKE '%moisturizer%' OR p.description ILIKE '%moisturizer%') AND p.is_published = true ORDER BY relevance_score DESC, p.rating DESC LIMIT 20

User: "cerave moisturizer for face"
SQL: SELECT p.id, p.title, p.description, p.price, p.discount_percentage, p.rating, p.stock, p.brand, p.thumbnail, c.name as category_name FROM products p JOIN categories c ON p.category_id = c.id WHERE ((p.title ILIKE '%cerave%' OR p.brand ILIKE '%cerave%') AND (p.title ILIKE '%moisturizer%' OR p.description ILIKE '%moisturizer%') AND (p.title ILIKE '%face%' OR c.name ILIKE '%face%' OR p.description ILIKE '%face%')) AND p.is_published = true ORDER BY p.rating DESC LIMIT 20

User: "laptops under $1000"
SQL: SELECT p.id, p.title, p.description, p.price, p.discount_percentage, p.rating, p.stock, p.brand, p.thumbnail, c.name as category_name FROM products p JOIN categories c ON p.category_id = c.id WHERE (p.title ILIKE '%laptop%' OR p.title ILIKE '%notebook%' OR c.name ILIKE '%laptop%' OR c.name ILIKE '%computer%') AND p.price < 1000 AND p.is_published = true ORDER BY p.rating DESC LIMIT 20

"""


SYSTEM_PROMPT = f"""You are an ecommerce Product Search Agent.

Your job is to help users find products by generating SQL queries and executing them using the execute_product_search tool.

WORKFLOW:
1. When user asks for products, generate a valid SQL SELECT query based on their request
2. Use the execute_product_search tool to run the query
3. Respond with a friendly message about the results

{get_schema_context()}

CRITICAL RULES:
- Always use the execute_product_search tool to search for products
- Generate valid SELECT SQL queries only
- Include all required fields for product cards
- Be friendly in your responses
"""


# def get_product_search_model():
#     """Initialize ChatBedrock model for product search agent."""
#     return ChatBedrock(
#         model_id=CLAUDE_MODEL_ID,
#         region_name="us-east-1",
#         model_kwargs={"max_tokens": 1024}
#     )


def create_product_search_react_agent():
    """Create a React agent for product search with SQL execution tool."""
    # model = get_product_search_model()
    # Bind the product search tool
    tools = [execute_product_search]
    agent = create_react_agent(llm, tools=tools)
    return agent


# Create global agent instance
_product_search_agent = None


def get_product_search_agent():
    """Get or create the product search React agent."""
    global _product_search_agent
    if _product_search_agent is None:
        _product_search_agent = create_product_search_react_agent()
    return _product_search_agent


def product_search_agent(state: AgentState) -> AgentState:
    """Handles product search using React agent with ChatBedrock and tools."""
    user_query = state["user_query"]
    db: Session = state["db_session"]
    fetched_items = state.get("currently_fetched_items") or []

    logger.info(f"Product search agent processing: '{user_query}'")
    
    # Set db session for tool access
    set_db_session(db)

    try:
        agent = get_product_search_agent()
        
        # Build context message
        context_msg = f"User Query: {user_query}"
        if fetched_items:
            context_msg += f" | Currently Displayed Items: {json.dumps(fetched_items)}"
        
        # Prepare messages with system prompt
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=context_msg)
        ]
        
        # Invoke the React agent
        result = agent.invoke({"messages": messages})
        
        # Extract response and data from agent output
        final_response = "Searching our catalog..."
        products = []
        sql_query = None
        
        if result and "messages" in result:
            for msg in result["messages"]:
                # Log tool calls
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_name = tool_call.get("name")
                        tool_args = tool_call.get("args")
                        logger.info(f"Using Agent: product_search_agent | Tool Call: {tool_name} | Args: {tool_args}")

                # Extract tool results (product data)
                if hasattr(msg, 'type') and msg.type == "tool":
                    try:
                        tool_result = json.loads(msg.content)
                        if tool_result.get("success") and tool_result.get("products"):
                            products = tool_result["products"]
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                # Get the final AI response
                if hasattr(msg, 'type') and msg.type == "ai" and hasattr(msg, 'content'):
                    if isinstance(msg.content, str) and msg.content:
                        final_response = msg.content
                    
                    # Check for tool calls to extract SQL
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            if tool_call.get("name") == "execute_product_search":
                                sql_query = tool_call.get("args", {}).get("sql")
        
        if not products:
            final_response = "No products found for your search."

        return {
            **state,
            "response": final_response,
            "sql_query": sql_query,
            "data": products,
            "currently_fetched_items": products,
            "agent_used": "product_search_agent"
        }

    except Exception as e:
        logger.error(f"Product search agent error: {e}")
        return {
            **state,
            "response": "I'm having trouble searching for products right now.",
            "data": [],
            "agent_used": "product_search_agent"
        }
