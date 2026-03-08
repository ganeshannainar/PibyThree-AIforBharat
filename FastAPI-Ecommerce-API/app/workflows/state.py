"""
State definition for the multi-agent workflow.
"""
from typing import TypedDict, Dict, Any, List, Optional


class AgentState(TypedDict):
    """State that flows through the multi-agent system with planner-orchestrator flow."""
    
    # Input
    user_query: str
    original_query: str  # Preserve original query during orchestration
    user_id: Optional[int]
    db_session: Any  # SQLAlchemy Session
    
    # Routing
    route: Optional[str]  # Which agent to route to
    
    # Execution Plan (from Planner)
    execution_plan: Optional[Dict[str, Any]]  # Generated execution plan
    current_step: Optional[int]  # Current step being executed (0-indexed)
    step_results: Optional[List[Dict[str, Any]]]  # Results from each completed step
    current_step_info: Optional[Dict[str, Any]]  # Info about current step being executed
    
    # Output
    response: Optional[str]  # Natural language response
    data: Optional[List[Any]]  # Structured data (e.g., product list)
    sql_query: Optional[str]  # SQL query used (for transparency)
    agent_used: Optional[str]  # Which agent handled the request
    greeting: Optional[str]  # Personalized greeting
    currently_fetched_items: Optional[List[Dict[str, Any]]]  # Items currently displayed to user
    
    # Aggregated results (for multi-intent)
    aggregated_response: Optional[str]  # Final aggregated response
    aggregated_data: Optional[List[Any]]  # Combined data from all steps


__all__ = ['AgentState']
