from pydantic import BaseModel
from typing import List, Optional, Any ,Dict


class AgentResponse(BaseModel):
    """Base model for agent responses"""
    answer: str
    data: Optional[List[Any]] = []
    sql_query: Optional[str] = None
    agent_used: str

class ChatRequest(BaseModel):
    """Request model for the chat endpoint"""
    query: str
    currently_fetched_items: Optional[List[Dict[str, Any]]] = []

class ChatResponse(BaseModel):
    """Response model for the chat endpoint"""
    answer: str
    data: Optional[List[Any]] = []
    sql_query: Optional[str] = None
    agent_used: str
    greeting: Optional[str] = None
    currently_fetched_items: Optional[List[Dict[str, Any]]] = []
