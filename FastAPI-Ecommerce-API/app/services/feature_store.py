"""
Feature Store Service for caching user and product data.
Provides in-memory caching with TTL-based expiration.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from threading import Lock
from sqlalchemy.orm import Session
from app.models.models import User, Product

logger = logging.getLogger(__name__)


class FeatureStore:
    """In-memory feature store with TTL-based expiration."""
    
    def __init__(self, default_ttl_seconds: int = 3600):
        """
        Initialize the feature store.
        
        Args:
            default_ttl_seconds: Time-to-live for cached items (default: 1 hour)
        """
        self.default_ttl = default_ttl_seconds
        self._user_cache: Dict[int, Dict[str, Any]] = {}
        self._product_cache: Dict[int, Dict[str, Any]] = {}
        self._lock = Lock()
        logger.info(f"Feature store initialized with TTL={default_ttl_seconds}s")
    
    def _is_expired(self, cached_item: Dict[str, Any]) -> bool:
        """Check if a cached item has expired."""
        if "expires_at" not in cached_item:
            return True
        return datetime.now() > cached_item["expires_at"]
    
    def get_user_info(self, user_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """
        Get user information from cache or database.
        
        Args:
            user_id: User ID to fetch
            db: Database session
            
        Returns:
            Dictionary with user info (id, full_name, email) or None
        """
        with self._lock:
            # Check cache first
            if user_id in self._user_cache:
                cached = self._user_cache[user_id]
                if not self._is_expired(cached):
                    logger.debug(f"Cache HIT for user_id={user_id}")
                    return cached["data"]
                else:
                    logger.debug(f"Cache EXPIRED for user_id={user_id}")
                    del self._user_cache[user_id]
        
        # Cache miss - fetch from database
        logger.debug(f"Cache MISS for user_id={user_id}, fetching from DB")
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"User not found: user_id={user_id}")
                return None
            
            user_data = {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "username": user.username
            }
            
            # Cache the result
            self.cache_user_info(user_id, user_data)
            return user_data
            
        except Exception as e:
            logger.error(f"Error fetching user_id={user_id}: {e}")
            return None
    
    def cache_user_info(self, user_id: int, user_data: Dict[str, Any]) -> None:
        """
        Cache user information.
        
        Args:
            user_id: User ID
            user_data: User data dictionary
        """
        with self._lock:
            self._user_cache[user_id] = {
                "data": user_data,
                "expires_at": datetime.now() + timedelta(seconds=self.default_ttl)
            }
            logger.debug(f"Cached user_id={user_id}")
    
    def get_product_info(self, product_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """
        Get product information from cache or database.
        
        Args:
            product_id: Product ID to fetch
            db: Database session
            
        Returns:
            Dictionary with product info or None
        """
        with self._lock:
            # Check cache first
            if product_id in self._product_cache:
                cached = self._product_cache[product_id]
                if not self._is_expired(cached):
                    logger.debug(f"Cache HIT for product_id={product_id}")
                    return cached["data"]
                else:
                    logger.debug(f"Cache EXPIRED for product_id={product_id}")
                    del self._product_cache[product_id]
        
        # Cache miss - fetch from database
        logger.debug(f"Cache MISS for product_id={product_id}, fetching from DB")
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                logger.warning(f"Product not found: product_id={product_id}")
                return None
            
            product_data = {
                "id": product.id,
                "title": product.title,
                "description": product.description,
                "price": product.price,
                "brand": product.brand,
                "thumbnail": product.thumbnail,
                "rating": product.rating,
                "stock": product.stock
            }
            
            # Cache the result
            self.cache_product_info(product_id, product_data)
            return product_data
            
        except Exception as e:
            logger.error(f"Error fetching product_id={product_id}: {e}")
            return None
    
    def cache_product_info(self, product_id: int, product_data: Dict[str, Any]) -> None:
        """
        Cache product information.
        
        Args:
            product_id: Product ID
            product_data: Product data dictionary
        """
        with self._lock:
            self._product_cache[product_id] = {
                "data": product_data,
                "expires_at": datetime.now() + timedelta(seconds=self.default_ttl)
            }
            logger.debug(f"Cached product_id={product_id}")
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._user_cache.clear()
            self._product_cache.clear()
            logger.info("Feature store cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        with self._lock:
            return {
                "users_cached": len(self._user_cache),
                "products_cached": len(self._product_cache)
            }


# Global singleton instance
feature_store = FeatureStore()
