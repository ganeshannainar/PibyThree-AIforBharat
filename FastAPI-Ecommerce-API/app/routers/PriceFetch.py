from fastapi import APIRouter, HTTPException, Depends
from serpapi import GoogleSearch
from dotenv import load_dotenv
import os
from typing import List, Dict, Any

load_dotenv()

router = APIRouter(
    prefix="/price-comparison",
    tags=["Price Comparison"]
)

# Get API key from environment
API_KEY = os.getenv("SERP_API_KEY")

def search_amazon(product_query: str) -> List[Dict[str, Any]]:
    """Search for products on Amazon"""
    if not API_KEY:
        print("Error: SERP_API_KEY not found")
        return []
        
    try:
        params = {
            "engine": "amazon",
            "amazon_domain": "amazon.com",
            "k": product_query,
            "api_key": API_KEY,
            "language":"en_US",
            "device":"desktop"
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        products = []
        for item in results.get("organic_results", []):
            try:
                price_raw = item.get("price")
                # Basic header/cleaning if needed, but keeping it simple for now
                products.append({
                    "title": item.get("title", "N/A"),
                    "price": price_raw if price_raw else "N/A",
                    "rating": item.get("rating", "N/A"),
                    "reviews": item.get("reviews", "N/A"),
                    "link": item.get("link", "N/A"),
                    "source": "Amazon"
                })
            except Exception as e:
                continue
        
        return products
    except Exception as e:
        print(f"Error searching Amazon: {e}")
        return []

def search_walmart(product_query: str) -> List[Dict[str, Any]]:
    """Search for products on Walmart"""
    if not API_KEY:
        print("Error: SERP_API_KEY not found")
        return []

    try:
        params = {
            "engine": "walmart",
            "query": product_query,
            "api_key": API_KEY
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        products = []
        for item in results.get("organic_results", []):
            try:
                primary_offer = item.get("primary_offer", {})
                price_raw = primary_offer.get("offer_price")
                
                products.append({
                    "title": item.get("title", "N/A"),
                    "price": f"${price_raw}" if price_raw else "N/A",
                    "rating": item.get("rating", "N/A"),
                    "reviews": item.get("reviews_count", "N/A"),
                    "link": item.get("product_page_url", "N/A"),
                    "source": "Walmart"
                })
            except Exception as e:
                continue
        
        return products
    except Exception as e:
        print(f"Error searching Walmart: {e}")
        return []

@router.get("/{product_query}")
async def get_price_comparison(product_query: str):
    """
    Compare prices between Amazon and Walmart for a given product query
    """
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Server configuration error: SERP_API_KEY missing")

    # Fetch in parallel could be better, but sequential is safer for now
    amazon_results = search_amazon(product_query)
    walmart_results = search_walmart(product_query)
    
    # Simple "Best Deal" logic
    best_deals = []
    
    # Helper to parse price
    def parse_price(price_str):
        if not price_str or price_str == "N/A":
            return float('inf')
        try:
            return float(str(price_str).replace('$', '').replace(',', ''))
        except:
            return float('inf')

    all_products = amazon_results + walmart_results
    
    # Filter valid prices and sort
    valid_products = [p for p in all_products if parse_price(p['price']) != float('inf')]
    valid_products.sort(key=lambda x: parse_price(x['price']))
    
    # Get top 1 for each source
    amazon_best = next((p for p in amazon_results), None)
    walmart_best = next((p for p in walmart_results), None)

    return {
        "product_query": product_query,
        "amazon_best": amazon_best,
        "walmart_best": walmart_best,
        "best_deal": valid_products[0] if valid_products else None
    }
