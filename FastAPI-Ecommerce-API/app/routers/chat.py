# import google.generativeai as genai
from google import genai
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security.http import HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.config import settings
from app.core.security import get_current_user, auth_scheme
from app.models.models import User
import logging
from typing import Optional, List, Any

# Import multi-agent system
from app.workflows.graph import app as agent_app
from app.services.feature_store import feature_store
import os

# Configure logging
logger = logging.getLogger(__name__)

# Configure Gemini
CHAT_API_KEY = settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

# Create Gemini client (NEW SDK)
gemini_client = genai.Client(api_key=CHAT_API_KEY) if CHAT_API_KEY else None


# CHAT_API_KEY = settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
# genai.configure(api_key=CHAT_API_KEY)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


from app.schemas.agents import ChatRequest, ChatResponse


def generate_personalized_greeting(user: User) -> str:
    """
    Generates a personalized greeting for the user.
    
    Args:
        user: User model instance
        
    Returns:
        Personalized greeting string
    """
    # Use username or first name from full_name
    username = user.username
    full_name = user.full_name
    first_name = full_name.split()[0] if full_name else username
    
    greetings = [
        f"Hello {first_name}! How can I help you today?",
        f"Hi {first_name}! What can I assist you with?",
        f"Welcome back, {first_name}! What are you looking for?",
        f"Hey {first_name}! Ready to find something amazing?",
    ]
    
    # Simple rotation based on user_id
    return greetings[user.id % len(greetings)]


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
    db: Session = Depends(get_db)
):
    """
    Multi-agent chat endpoint with personalized greetings.
    Requires authentication.
    
    The supervisor routes queries to specialized agents:
    - Chat Agent: General conversation and help
    - Product Search Agent: Specific product discovery
    - Review Agent: Review analysis and sentiment
    - Transaction Agent: Cart, orders, and pricing
    
    Args:
        request: ChatRequest with query
        token: JWT authentication token
        db: Database session
        
    Returns:
        ChatResponse with answer, data, and metadata
    """
    # Get authenticated user ID from token
    user_id = get_current_user(token)
    
    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_query = request.query
    logger.info(f"Chat request: query='{user_query}', user_id={user_id}, username={user.username}")
    
    # Generate personalized greeting with username
    greeting = generate_personalized_greeting(user)
    logger.info(f"Generated greeting for user {user.username}")
    
    # Prepare initial state for multi-agent system
    initial_state = {
        "user_query": user_query,
        "user_id": user_id,
        "db_session": db,
        "route": None,
        "response": None,
        "data": None,
        "sql_query": None,
        "agent_used": None,
        "greeting": greeting,
        "currently_fetched_items": request.currently_fetched_items or []
    }
    
    try:
        # Run the multi-agent workflow
        logger.info("Invoking multi-agent workflow")
        final_state = agent_app.invoke(initial_state)
        
        logger.info(f"Workflow completed. Agent used: {final_state.get('agent_used')}")
        logger.info(f"Products found in final state: {len(final_state.get('data', []))}")
        if final_state.get("data"):
            logger.info(f"First product sample: {final_state.get('data')[0]}")
        
        return ChatResponse(
            answer=final_state.get("response", "I couldn't process your request."),
            sql_query=final_state.get("sql_query"),
            data=final_state.get("data", []),
            agent_used=final_state.get("agent_used"),
            greeting=greeting,
            currently_fetched_items=final_state.get("currently_fetched_items", [])
        )
        
    except Exception as e:
        logger.error(f"Multi-agent workflow error: {e}", exc_info=True)
        return ChatResponse(
            answer="I'm sorry, I encountered an error processing your request. Please try again.",
            sql_query=None,
            data=[],
            agent_used="error",
            greeting=greeting
        )
