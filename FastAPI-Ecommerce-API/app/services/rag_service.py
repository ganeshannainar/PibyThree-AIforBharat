from app.tools.RagTools import get_rag_system
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ReviewRAGService:
    def __init__(self):
        self.rag_system = get_rag_system()
        
    def search_reviews(self, query: str, k: int = 5):
        """Search for relevant reviews."""
        return self.rag_system.search(query, k=k)

    def filter_products(self, sql_products: List[Dict[str, Any]], query: str, top_k_reviews: int = 10) -> List[Dict[str, Any]]:
        """
        Filters/Ranks SQL products based on RAG review relevancy.
        """
        # Get relevant reviews for the query
        relevant_docs = self.search_reviews(query, k=top_k_reviews)
        
        if not relevant_docs:
            return sql_products
            
        relevant_product_titles = set()
        for doc in relevant_docs:
            p_title = doc.metadata.get("product_title")
            if p_title:
                relevant_product_titles.add(p_title.lower())
        
        if not relevant_product_titles:
            return sql_products
            
        # Filter SQL results
        filtered_products = []
        for prod in sql_products:
            title = prod.get('title', '').lower()
            if any(p_title in title or title in p_title for p_title in relevant_product_titles):
                filtered_products.append(prod)
                
        if not filtered_products:
            logger.info("RAG filter resulted in empty set. Returning original SQL results.")
            return sql_products
            
        return filtered_products

# Global instance
rag_service = ReviewRAGService()
