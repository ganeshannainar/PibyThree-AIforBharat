"""
Product Search Tools - Handles SQL execution and formatting for product queries.
Converted to LangChain @tool format for use with React agents.
"""
import logging
from typing import List, Dict, Any
from langchain_core.tools import tool
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Store db session for tool access (set by agent before invoking)
_db_session: Session = None


def set_db_session(db: Session):
    """Set the database session for tool access."""
    global _db_session
    _db_session = db


def get_db_session() -> Session:
    """Get the current database session."""
    global _db_session
    return _db_session


@tool
def execute_product_search(sql: str) -> str:
    """
    Safely executes a SELECT SQL query to search for products in the database.
    Use this tool when you need to find products based on user search criteria.
    
    Args:
        sql: A valid SELECT SQL query to search products. Must start with SELECT.
    
    Returns:
        JSON string of product results or error message.
    """
    import json
    
    db = get_db_session()
    if not db:
        return json.dumps({"error": "Database session not available"})
    
    if not sql:
        return json.dumps({"error": "No SQL query provided"})
        
    # Security check: Only allow SELECT
    if not sql.lower().strip().startswith("select"):
        logger.warning(f"Rejected non-SELECT SQL: {sql}")
        return json.dumps({"error": "Only SELECT queries are allowed"})

    try:
        logger.info(f"Executing product search SQL: {sql}")
        db_result = db.execute(text(sql))
        keys = db_result.keys()
        rows = [dict(zip(keys, row)) for row in db_result.fetchall()]
        
        logger.info(f"SQL execution found {len(rows)} results")
        return json.dumps({"success": True, "products": rows, "count": len(rows)})
    except Exception as e:
        logger.error(f"SQL execution failed in execute_product_search: {e}")
        return json.dumps({"error": str(e)})


def execute_product_search_raw(db: Session, sql: str) -> List[Dict[str, Any]]:
    """
    Legacy function for backwards compatibility.
    Safely executes a SELECT query and returns formatted rows.
    """
    if not sql:
        return []
        
    # Security check: Only allow SELECT
    if not sql.lower().strip().startswith("select"):
        logger.warning(f"Rejected non-SELECT SQL: {sql}")
        return []

    try:
        logger.info(f"Executing product search SQL: {sql}")
        db_result = db.execute(text(sql))
        keys = db_result.keys()
        rows = [dict(zip(keys, row)) for row in db_result.fetchall()]
        
        logger.info(f"SQL execution found {len(rows)} results")
        return rows
    except Exception as e:
        logger.error(f"SQL execution failed in execute_product_search: {e}")
        return []


def format_product_results(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Standardizes product data for frontend consumption.
    """
    # Currently we return the database rows which already match the expected schema
    # But this is a placeholder for future formatting needs
    return products
