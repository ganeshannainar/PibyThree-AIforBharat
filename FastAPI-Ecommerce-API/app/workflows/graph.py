"""
LangGraph workflow for multi-agent system.
Simplified flow: Planner → Orchestrator → Agents
"""
import logging
from langgraph.graph import StateGraph, END
from app.workflows.state import AgentState

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """
    Builds and compiles the LangGraph workflow.
    
    Flow:
    - Entry: planner → orchestrator
    - Orchestrator routes to: chat_agent | product_search_agent | transaction_agent | review_agent
    - Agents return to: orchestrator (if more steps) or END
    """
    # Import agents here to avoid circular imports
    from app.agents.planner_agent import planner_agent
    from app.agents.orchestrator_agent import orchestrator_agent, get_next_route
    from app.agents.chat_agent import chat_agent
    from app.agents.product_search_agent import product_search_agent
    from app.agents.review_agent import review_analysis_agent
    from app.agents.transaction_agent import transactional_agent

    # Create graph with AgentState
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("planner", planner_agent)
    graph.add_node("orchestrator", orchestrator_agent)
    graph.add_node("chat_agent", chat_agent)
    graph.add_node("product_search_agent", product_search_agent)
    graph.add_node("review_agent", review_analysis_agent)
    graph.add_node("transaction_agent", transactional_agent)
    
    # Set entry point
    graph.set_entry_point("planner")
    
    # Planner always goes to orchestrator
    graph.add_edge("planner", "orchestrator")
    
    # Orchestrator routes to agents based on current step, or END if complete
    graph.add_conditional_edges(
        "orchestrator",
        get_next_route,
        {
            "chat_agent": "chat_agent",
            "product_search_agent": "product_search_agent",
            "transaction_agent": "transaction_agent",
            "review_agent": "review_agent",
            "END": END
        }
    )
    
    # All agents return to orchestrator
    graph.add_edge("chat_agent", "orchestrator")
    graph.add_edge("product_search_agent", "orchestrator")
    graph.add_edge("transaction_agent", "orchestrator")
    graph.add_edge("review_agent", "orchestrator")
    
    logger.info("LangGraph workflow built: planner → orchestrator → agents")
    return graph


# Build and compile the graph
workflow_graph = build_graph()
app = workflow_graph.compile()

logger.info("Multi-agent workflow compiled and ready")
