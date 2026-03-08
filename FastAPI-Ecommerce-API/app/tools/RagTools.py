"""
RAG (Retrieval Augmented Generation) tools for product reviews search.
Uses ChromaDB for vector storage with HuggingFace embeddings.
"""
import os
from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


class ProductReviewsRAGSystem:
    """RAG system for searching product reviews and recommendations"""
    
    def __init__(self, chroma_path: str = None):
        """
        Initialize RAG system with existing ChromaDB.
        
        Args:
            chroma_path: Path to ChromaDB persist directory
        """
        self.retriever = None
        self.vectorstore = None
        
        # Default path
        if chroma_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            chroma_path = os.path.join(base_dir, "database", "chroma_db")
        
        self.chroma_path = chroma_path
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """Initialize the vector store from existing ChromaDB"""
        try:
            if not os.path.exists(self.chroma_path):
                print(f"⚠️ ChromaDB not found at: {self.chroma_path}")
                print("Run 'python scripts/generate_reviews_and_ingest.py' to create it.")
                return
            
            # Initialize embeddings
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            
            # Load existing ChromaDB
            self.vectorstore = Chroma(
                persist_directory=self.chroma_path,
                embedding_function=embeddings,
                collection_name="product_reviews"
            )
            
            self.retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": 5}
            )
            
            # Test collection
            collection = self.vectorstore._collection
            count = collection.count()
            print(f"✅ RAG system initialized with {count} documents from ChromaDB")
            
        except Exception as e:
            print(f"❌ RAG System initialization failed: {e}")
            import traceback
            traceback.print_exc()
    
    def search(self, query: str, k: int = 5) -> list:
        """
        Search for relevant product reviews.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        if not self.retriever:
            return []
        
        try:
            results = self.retriever.invoke(query)
            return results[:k]
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def search_with_scores(self, query: str, k: int = 5) -> list:
        """
        Search with similarity scores.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of (document, score) tuples
        """
        if not self.vectorstore:
            return []
        
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def format_results_for_llm(self, results: list) -> str:
        """Format search results for LLM consumption"""
        if not results:
            return "No relevant product reviews found."
        
        formatted = []
        for i, doc in enumerate(results, 1):
            meta = doc.metadata
            formatted.append(f"""
Review {i}:
Product: {meta.get('product_title', 'Unknown')}
Brand: {meta.get('product_brand', 'Unknown')}
Rating: {meta.get('rating', 'N/A')}/5
Verified: {'Yes' if meta.get('verified_purchase') else 'No'}
---
{doc.page_content}
""")
        
        return "\n".join(formatted)


# Global instance (lazy initialization)
_rag_system = None


def get_rag_system() -> ProductReviewsRAGSystem:
    """Get or create RAG system instance"""
    global _rag_system
    if _rag_system is None:
        _rag_system = ProductReviewsRAGSystem()
    return _rag_system


@tool
def product_reviews_search_tool(query: str) -> str:
    """
    Search product reviews to find recommendations and customer feedback.
    Use this tool when users ask about product quality, recommendations,
    or want to know what other customers think about products.
    
    Args:
        query: Natural language search query about products
        
    Returns:
        Relevant product reviews and customer feedback
    """
    rag = get_rag_system()
    results = rag.search(query, k=5)
    return rag.format_results_for_llm(results)


# For backwards compatibility
def initialize_rag_system():
    """Initialize and return RAG system"""
    return get_rag_system()

