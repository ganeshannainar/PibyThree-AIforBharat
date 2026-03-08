"""
Transaction Agent - Handles cart operations, orders, and pricing queries.
Converted to React agent using LangGraph's create_react_agent with tool binding.
"""
import logging
import json
from typing import Any, Dict, List
from sqlalchemy import text
from sqlalchemy.orm import Session
from langchain_aws import ChatBedrock
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from app.workflows.state import AgentState
from app.models.models import Cart, Product
from app.tools.cart_tools import (
    add_to_cart, remove_from_cart, place_order, view_cart, view_orders,
    set_cart_context
)
from app.tools.price_tools import compare_prices
from app.core.llm import llm

logger = logging.getLogger(__name__)

# CLAUDE_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"

SYSTEM_PROMPT = """You are a Transaction Agent for an e-commerce store. Your job is to handle cart operations, orders, and price inquiries using the available tools.

AVAILABLE TOOLS:
1. add_to_cart: Add products to the user's shopping cart
2. remove_from_cart: Remove products from the cart by name
3. place_order: Checkout and place an order from the cart
4. view_cart: View current cart contents
5. view_orders: View order history
6. compare_prices: Compare prices with Amazon and Walmart

WORKFLOW:
1. Understand what the user wants to do (add, remove, checkout, compare prices, etc.)
2. Use the appropriate tool to perform the action
3. Respond with a friendly confirmation message

IMPORTANT:
- If user says "add it to cart" without specifying what, use the first item from currently_fetched_items
- Be helpful and confirm actions with clear messages
- For price comparisons, always provide the product name to search

Be friendly and helpful in your responses!"""


# def get_transaction_model():
#     """Initialize ChatBedrock model for transaction agent."""
#     return ChatBedrock(
#         model_id=CLAUDE_MODEL_ID,
#         region_name="us-east-1",
#         model_kwargs={"max_tokens": 1024}
#     )


def create_transaction_react_agent():
    """Create a React agent for transactions with cart and price tools."""
    # model = get_transaction_model()
    # Bind all transaction-related tools
    tools = [add_to_cart, remove_from_cart, place_order, view_cart, view_orders, compare_prices]
    agent = create_react_agent(llm, tools=tools)
    return agent


# Create global agent instance
_transaction_agent = None


def get_transaction_agent():
    """Get or create the transaction React agent."""
    global _transaction_agent
    if _transaction_agent is None:
        _transaction_agent = create_transaction_react_agent()
    return _transaction_agent


def transactional_agent(state: AgentState) -> AgentState:
    """Handles cart operations, orders, and pricing queries using React agent."""
    user_query = state["user_query"]
    user_id = state.get("user_id")
    db: Session = state["db_session"]
    fetched_items = state.get("currently_fetched_items") or []

    logger.info(f"Transaction agent processing: '{user_query}'")

    # Set context for cart tools
    set_cart_context(db, user_id, fetched_items)

    try:
        agent = get_transaction_agent()
        
        # Build context message
        context_msg = f"User Query: {user_query}"
        if fetched_items:
            context_msg += f"\nCurrently Displayed Items: {json.dumps(fetched_items[:3])}"  # Limit for context
        if not user_id:
            context_msg += "\nNote: User is NOT logged in. They must log in for cart operations."
        
        # Prepare messages with system prompt
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=context_msg)
        ]
        
        # Invoke the React agent
        result = agent.invoke({"messages": messages})
        
        # Extract response and data from agent output
        final_response = "I'm on it!"
        result_data = []
        
        if result and "messages" in result:
            for msg in result["messages"]:
                # Log tool calls
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_name = tool_call.get("name")
                        tool_args = tool_call.get("args")
                        logger.info(f"Using Agent: transaction_agent | Tool Call: {tool_name} | Args: {tool_args}")

                # Extract tool results
                if hasattr(msg, 'type') and msg.type == "tool":
                    try:
                        tool_result = json.loads(msg.content)
                        if tool_result.get("success"):
                            # Handle price comparison first to populate our_price
                            if tool_result.get("amazon_best") or tool_result.get("walmart_best"):
                                tool_result["action"] = "price_comparison"
                                tool_result["our_price"] = None
                                # Map product_query to product_name for frontend compatibility
                                tool_result["product_name"] = tool_result.get("product_query")
                                
                                # Try to find our price
                                product_name = tool_result.get("product_query")
                                if product_name:
                                    # Try exact/partial match from query to title
                                    product = db.query(Product).filter(Product.title.ilike(f"%{product_name}%")).first()
                                    
                                    # Fallback: check if the product title is contained IN the query
                                    if not product:
                                        stmt = text("SELECT * FROM products WHERE :query ILIKE '%' || title || '%' ORDER BY length(title) DESC LIMIT 1")
                                        result = db.execute(stmt, {"query": product_name})
                                        row = result.first()
                                        if row:
                                            product = db.query(Product).get(row.id)

                                    if product:
                                        tool_result["our_price"] = product.dynamic_price if (product.is_dynamic_pricing_active and product.dynamic_price) else product.price * (1 - (product.discount_percentage or 0) / 100)
                                        tool_result["our_url"] = f"/products/{product.id}"
                                        tool_result["thumbnail"] = product.thumbnail
                            
                            # Append the (potentially modified) tool_result
                            if tool_result.get("action"):
                                result_data.append(tool_result)
                                
                            # Handle cart/orders specific formatting if needed (though they usually rely on 'action' too)
                            if tool_result.get("items") and not tool_result.get("action"):
                                # Ensure cart action is set if missing
                                pass 

                            # Handle cart view
                            if tool_result.get("items"):
                                result_data = [{
                                    "id": i["id"],
                                    "title": i["title"],
                                    "quantity": i["quantity"],
                                    "price": i["price"]
                                } for i in tool_result["items"]]
                            # Handle orders view
                            if tool_result.get("orders"):
                                result_data = tool_result["orders"]
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                # Get the final AI response
                if hasattr(msg, 'type') and msg.type == "ai" and hasattr(msg, 'content'):
                    if isinstance(msg.content, str) and msg.content:
                        final_response = msg.content

        return {
            **state,
            "response": final_response,
            "data": result_data,
            "agent_used": "transaction_agent"
        }

    except Exception as e:
        logger.error(f"Transaction agent error: {e}")
        return {
            **state,
            "response": "I encountered an error while processing your transaction request. Please try again.",
            "data": [],
            "agent_used": "transaction_agent"
        }
