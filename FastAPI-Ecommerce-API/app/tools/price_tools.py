"""
Price Comparison Tool - Integration with PriceFetch.py logic.
Converted to LangChain @tool format for use with React agents.
"""
import logging
import json
from typing import Dict, Any
from langchain_core.tools import tool
from app.routers.PriceFetch import search_amazon, search_walmart

logger = logging.getLogger(__name__)


@tool
def compare_prices(product_query: str) -> str:
    """
    Compares prices for a product across Amazon and Walmart.
    Use this when the user wants to compare prices with external stores.
    
    Args:
        product_query: The product name or description to search for.
    
    Returns:
        JSON string with price comparison results from Amazon and Walmart.
    """
    try:
        # Reusing logic from PriceFetch.py
        amazon_results = search_amazon(product_query)
        walmart_results = search_walmart(product_query)
        
        def parse_price(price_str):
            if not price_str or price_str == "N/A":
                return float('inf')
            try:
                return float(str(price_str).replace('$', '').replace(',', ''))
            except:
                return float('inf')

        all_products = amazon_results + walmart_results
        valid_products = [p for p in all_products if parse_price(p['price']) != float('inf')]
        valid_products.sort(key=lambda x: parse_price(x['price']))
        
        amazon_best = amazon_results[0] if amazon_results else None
        walmart_best = walmart_results[0] if walmart_results else None
        best_deal = valid_products[0] if valid_products else None
        
        return json.dumps({
            "success": True,
            "product_query": product_query,
            "amazon_best": amazon_best,
            "walmart_best": walmart_best,
            "best_deal": best_deal,
            "sources_found": len(valid_products),
            "action": "price_comparison"
        })
    except Exception as e:
        logger.error(f"Error in compare_prices: {e}")
        return json.dumps({"success": False, "message": str(e)})


# Legacy function for backwards compatibility
def compare_prices_tool(product_query: str) -> Dict[str, Any]:
    """Legacy function - use compare_prices tool instead."""
    result = json.loads(compare_prices.invoke({"product_query": product_query}))
    return result
