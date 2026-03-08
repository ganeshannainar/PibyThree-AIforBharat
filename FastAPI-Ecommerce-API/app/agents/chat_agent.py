"""
Chat Agent - Handles greetings and general conversation.
Converted to React agent using LangGraph's create_react_agent.
"""
import logging
import json
from typing import Any, Dict
from langchain_aws import ChatBedrock
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from app.workflows.state import AgentState
from app.core.llm import llm

logger = logging.getLogger(__name__)

# CLAUDE_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"

SYSTEM_PROMPT = """You are a friendly and helpful e-commerce assistant. 
Your role is to greet users, explain your capabilities, and handle general conversation that isn't specifically about searching for products, making transactions, or reading reviews.

Capabilities you can mention:
- Searching for products in our catalog.
- Comparing prices with Amazon and Walmart.
- Managing your shopping cart and placing orders.
- Analyzing product reviews.

Keep your responses concise, warm, and professional. 
If the user asks for something outside your scope, kindly guide them towards your e-commerce capabilities."""


# def get_chat_model():
#     """Initialize ChatBedrock model for chat agent."""
#     return ChatBedrock(
#         model_id=CLAUDE_MODEL_ID,
#         region_name="us-east-1",
#         model_kwargs={"max_tokens": 1024}
#     )


def create_chat_react_agent():
    """Create a React agent for chat with no tools (pure conversation)."""
    # model = get_chat_model()
    # Chat agent has no tools - it's for pure conversation
    agent = create_react_agent(llm, tools=[])
    return agent


# Create global agent instance
_chat_agent = None


def get_chat_agent():
    """Get or create the chat React agent."""
    global _chat_agent
    if _chat_agent is None:
        _chat_agent = create_chat_react_agent()
    return _chat_agent


def chat_agent(state: AgentState) -> AgentState:
    """Handles general conversation using React agent with ChatBedrock."""
    user_query = state["user_query"]
    
    logger.info(f"Chat agent processing: '{user_query}'")

    try:
        agent = get_chat_agent()
        
        # Prepare messages with system prompt
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_query)
        ]
        
        # Invoke the React agent
        result = agent.invoke({"messages": messages})
        
        # Extract the response from the agent output
        final_response = ""
        if result and "messages" in result:
            # Get the last AI message
            for msg in reversed(result["messages"]):
                if hasattr(msg, 'content') and msg.type == "ai":
                    final_response = msg.content
                    break
        
        if not final_response:
            final_response = "Hello! I'm here to help you with your shopping needs. What can I do for you today?"

        return {
            **state,
            "response": final_response,
            "data": [],
            "agent_used": "chat_agent"
        }

    except Exception as e:
        logger.error(f"Chat agent error: {e}")
        return {
            **state,
            "response": "Hello! I'm here to help you with your shopping needs. What can I do for you today?",
            "data": [],
            "agent_used": "chat_agent"
        }
