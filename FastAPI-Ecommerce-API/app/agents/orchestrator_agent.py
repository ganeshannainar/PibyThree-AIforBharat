"""
Orchestrator Agent - Executes plans by routing to appropriate agents.
Handles both single-intent and multi-intent plans from the planner.
"""
import logging
import json
from typing import Any, Dict, List
from app.workflows.state import AgentState

logger = logging.getLogger(__name__)


def orchestrator_agent(state: AgentState) -> AgentState:
    """
    Orchestrates execution of plans from the planner.
    
    For single-intent: Routes to a single agent, then on return collects result and ends.
    For multi-intent: Routes sequentially to each agent, collecting results after each.
    """
    execution_plan = state.get("execution_plan", {})
    current_step = state.get("current_step", 0)
    step_results = state.get("step_results") or []
    
    # Get steps from plan
    steps = execution_plan.get("steps", [])
    
    logger.info(f"Orchestrator: step {current_step + 1}/{len(steps)}")
    
    # If we have results from a previous agent execution, collect them
    if state.get("response") and current_step > 0:
        step_results = _collect_step_result(state, step_results, current_step)
    
    # Check if we've completed all steps
    if current_step >= len(steps):
        logger.info("All steps completed, aggregating results")
        return _aggregate_results(state, step_results)
    
    # Get the current step to execute
    step = steps[current_step]
    agent = step.get("agent", "chat_agent")
    query_for_agent = step.get("query_for_agent", state.get("original_query", state["user_query"]))
    
    logger.info(f"Executing step {current_step + 1}: {step.get('description')} using {agent}")
    
    # Update state for the agent to execute
    return {
        **state,
        "user_query": query_for_agent,  # Query for this specific step
        "route": agent,
        "current_step_info": step,
        "current_step": current_step + 1,  # Increment for next iteration
        "step_results": step_results
    }


def _collect_step_result(state: AgentState, step_results: List, current_step: int) -> List:
    """Collects the result from the last executed agent."""
    step_result = {
        "step_id": current_step,
        "agent": state.get("agent_used"),
        "response": state.get("response"),
        "data": state.get("data"),
        "sql_query": state.get("sql_query")
    }
    step_results.append(step_result)
    logger.info(f"Collected result from step {current_step}: {state.get('agent_used')}")
    return step_results


def _aggregate_results(state: AgentState, step_results: List) -> AgentState:
    """Aggregates results from all executed steps into a final response."""
    logger.info(f"Aggregating {len(step_results)} step results")
    
    responses = []
    all_data = []
    
    for result in step_results:
        if result.get("response"):
            responses.append(result["response"])
        if result.get("data"):
            all_data.extend(result["data"] if isinstance(result["data"], list) else [result["data"]])
    
    aggregated_response = " ".join(responses) if responses else "I've completed your request."
    
    logger.info(f"Aggregated response: {aggregated_response[:100]}...")
    
    return {
        **state,
        "response": aggregated_response,
        "data": all_data,
        "aggregated_response": aggregated_response,
        "aggregated_data": all_data,
        "agent_used": "orchestrator",
        "route": "END"  # Signal to end workflow
    }


def get_next_route(state: AgentState) -> str:
    """
    Determines the next route in the workflow.
    Called as a conditional edge after orchestrator.
    """
    execution_plan = state.get("execution_plan", {})
    current_step = state.get("current_step", 0)
    steps = execution_plan.get("steps", [])
    
    # If all steps done, end
    if current_step > len(steps):
        logger.info("All steps complete, ending workflow")
        return "END"
    
    # Get the route from orchestrator's decision
    route = state.get("route", "END")
    
    # Validate route
    valid_routes = ["chat_agent", "product_search_agent", "transaction_agent", "review_agent", "END"]
    if route not in valid_routes:
        logger.warning(f"Unknown route: {route}, defaulting to chat_agent")
        return "chat_agent"
    
    logger.info(f"Routing to: {route}")
    return route

