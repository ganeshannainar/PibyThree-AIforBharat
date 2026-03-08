"""
Review Agent - Analyzes product reviews and sentiment.
Converted to React agent using LangGraph's create_react_agent with tool binding.
"""
import logging
import json
from typing import List, Dict, Any
from langchain_aws import ChatBedrock
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from app.workflows.state import AgentState
from app.tools.RagTools import product_reviews_search_tool
from app.core.llm import llm

logger = logging.getLogger(__name__)

# CLAUDE_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"

SYSTEM_PROMPT = """You are a Review Analysis Agent for an e-commerce store. Your job is to help users understand product reviews and customer feedback.

AVAILABLE TOOLS:
1. product_reviews_search_tool: Search for relevant product reviews using semantic search

WORKFLOW:
1. When a user asks about reviews, use the product_reviews_search_tool to find relevant reviews
2. Analyze the reviews found and summarize the key insights
3. Provide a helpful response about sentiment, pros/cons, and recommendations

RESPONSE GUIDELINES:
- Focus on sentiment: Is the product well-received?
- Highlight key pros and cons mentioned in reviews
- Provide a clear recommendation if possible
- Keep responses concise (3-4 sentences)
- Be helpful and friendly

Examples of queries you handle:
- "What do people say about this moisturizer?"
- "Is this laptop good based on reviews?"
- "Are there any complaints about this product?"
- "What are the best-reviewed products?"
"""


# def get_review_model():
#     """Initialize ChatBedrock model for review agent."""
#     return ChatBedrock(
#         model_id=CLAUDE_MODEL_ID,
#         region_name="us-east-1",
#         model_kwargs={"max_tokens": 1024}
#     )


def create_review_react_agent():
    """Create a React agent for review analysis with RAG tool."""
    # model = get_review_model()
    # Bind the review search tool
    tools = [product_reviews_search_tool]
    agent = create_react_agent(llm, tools=tools)
    return agent


# Create global agent instance
_review_agent = None


def get_review_agent():
    """Get or create the review React agent."""
    global _review_agent
    if _review_agent is None:
        _review_agent = create_review_react_agent()
    return _review_agent


def review_analysis_agent(state: AgentState) -> AgentState:
    """
    Analyzes product reviews and sentiment using React agent.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with review analysis
    """
    user_query = state["user_query"]
    
    logger.info(f"Review agent processing: '{user_query}'")
    
    try:
        agent = get_review_agent()
        
        # Prepare messages with system prompt
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_query)
        ]
        
        # Invoke the React agent
        result = agent.invoke({"messages": messages})
        
        # Extract response from agent output
        final_response = "I couldn't find any reviews matching your query. Please try asking about specific products or features."
        products_mentioned = []
        
        if result and "messages" in result:
            for msg in result["messages"]:
                # Log tool calls
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_name = tool_call.get("name")
                        tool_args = tool_call.get("args")
                        logger.info(f"Using Agent: review_agent | Tool Call: {tool_name} | Args: {tool_args}")

                # Extract tool results (review data for context)
                if hasattr(msg, 'type') and msg.type == "tool":
                    # The tool returns formatted review text
                    pass
                
                # Get the final AI response
                if hasattr(msg, 'type') and msg.type == "ai" and hasattr(msg, 'content'):
                    if isinstance(msg.content, str) and msg.content:
                        final_response = msg.content

        return {
            **state,
            "response": final_response,
            "data": [],  # Return empty data to show only textual output
            "agent_used": "review_agent"
        }
        
    except Exception as e:
        logger.error(f"Review agent error: {e}")
        return {
            **state,
            "response": "I encountered an error while analyzing reviews. Please try again.",
            "data": [],
            "agent_used": "review_agent"
        }
