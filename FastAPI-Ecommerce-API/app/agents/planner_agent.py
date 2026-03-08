"""
Planner Agent - Entry point that analyzes queries and creates execution plans.
All queries go through planner first, which generates a plan for orchestrator to execute.
"""
import logging
import json
import re
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from app.workflows.state import AgentState
from app.core.llm import llm


logger = logging.getLogger(__name__)

# CLAUDE_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"

SYSTEM_PROMPT = """You are the Planner Agent for an e-commerce multi-agent system.
Your job is to analyze every user query and create an execution plan.

AVAILABLE AGENTS:

1. PRODUCT_SEARCH_AGENT:
   - Tools: execute_product_search
   - Use for: Searching products, finding items, browsing catalog
   - Examples: "show me laptops", "find moisturizers", "search for phones under $500"

2. TRANSACTION_AGENT:
   - Tools: add_to_cart, remove_from_cart, place_order, view_cart, view_orders, compare_prices
   - Use for: Cart operations, checkout, orders, price comparisons
   - Examples: "add to cart", "checkout", "compare prices with Amazon", "view my cart"

3. REVIEW_AGENT:
   - Tools: query_reviews
   - Use for: Product reviews and feedback questions
   - Examples: "what do reviews say?", "is this product good?"

4. CHAT_AGENT:
   - Tools: None (conversational)
   - Use for: Greetings, help, general questions about the store
   - Examples: "hi", "hello", "what can you do?"

ALWAYS return a plan with a "steps" array. For single-intent queries, return one step.
For multi-intent queries, return multiple steps in execution order.

EXAMPLES:

Single-intent "show me laptops":
{
  "steps": [
    {"step_id": 1, "agent": "product_search_agent", "description": "Search for laptops", "query_for_agent": "show me laptops"}
  ],
  "reason": "Simple product search"
}

Single-intent "hello":
{
  "steps": [
    {"step_id": 1, "agent": "chat_agent", "description": "Respond to greeting", "query_for_agent": "hello"}
  ],
  "reason": "Greeting"
}

Multi-intent "search for laptops and add the best one to cart":
{
  "steps": [
    {"step_id": 1, "agent": "product_search_agent", "description": "Search for laptops", "query_for_agent": "show me laptops"},
    {"step_id": 2, "agent": "transaction_agent", "description": "Add first result to cart", "query_for_agent": "add the first product to cart"}
  ],
  "reason": "Search then add to cart"
}

Multi-intent "compare prices with Amazon and add to cart":
{
  "steps": [
    {"step_id": 1, "agent": "transaction_agent", "description": "Compare prices", "query_for_agent": "compare prices with Amazon"},
    {"step_id": 2, "agent": "transaction_agent", "description": "Add to cart", "query_for_agent": "add to cart"}
  ],
  "reason": "Price comparison then cart add"
}

RULES:
1. ALWAYS return a steps array with at least one step
2. Each step needs: step_id, agent, description, query_for_agent
3. query_for_agent should be a clear instruction for that agent
4. Order steps logically (search before add, etc.)

Return ONLY valid JSON, no additional text.
"""


# def get_planner_model():
#     """Initialize ChatBedrock model for planner agent."""
#     return ChatBedrock(
#         model_id=CLAUDE_MODEL_ID,
#         region_name="us-east-1",
#         model_kwargs={"max_tokens": 1024}
#     )


# _planner_model = None


# def get_model():
#     """Get or create the planner model."""
#     global _planner_model
#     if _planner_model is None:
#         _planner_model = get_planner_model()
#     return _planner_model


def planner_agent(state: AgentState) -> AgentState:
    """
    Entry point for all queries. Analyzes and creates an execution plan.
    The plan always has a 'steps' array that the orchestrator will execute.
    """
    user_query = state["user_query"]
    
    logger.info(f"Planner analyzing query: '{user_query}'")

    try:
        # model = get_model()
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"User Query: {user_query}")
        ]
        
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            plan = json.loads(json_match.group(0))
        else:
            raise ValueError("No JSON in planner response")

        # Ensure steps array exists
        if "steps" not in plan:
            raise ValueError("Plan missing 'steps' array")

        logger.info(f"Planner created plan with {len(plan.get('steps', []))} step(s)")

        return {
            **state,
            "execution_plan": plan,
            "original_query": user_query,  # Preserve for context
            "current_step": 0,
            "step_results": []
        }

    except Exception as e:
        logger.error(f"Planner error: {e}")
        # Fallback: single step to chat agent
        return {
            **state,
            "execution_plan": {
                "steps": [
                    {"step_id": 1, "agent": "chat_agent", "description": "Handle query", "query_for_agent": user_query}
                ],
                "reason": f"Fallback due to error: {str(e)}"
            },
            "original_query": user_query,
            "current_step": 0,
            "step_results": []
        }

