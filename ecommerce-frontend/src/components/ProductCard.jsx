import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { useState } from 'react';

const PLACEHOLDER_IMAGE = 'https://via.placeholder.com/300x200?text=No+Image';

const ProductCard = ({ product }) => {
  const { isAuthenticated } = useAuth();
  const { addToCart } = useCart();
  const [imgSrc, setImgSrc] = useState(product.thumbnail || PLACEHOLDER_IMAGE);
  const [imgError, setImgError] = useState(false);

  const handleAddToCart = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) {
      alert('Please login to add items to cart');
      return;
    }
    const result = await addToCart(product.id, 1);
    if (result.success) {
      alert('Added to cart!');
    } else {
      alert(result.error);
    }
  };

  const handleImageError = () => {
    if (!imgError) {
      setImgError(true);
      setImgSrc(PLACEHOLDER_IMAGE);
    }
  };

  // Calculate display price based on dynamic pricing
  const getDisplayPrice = () => {
    if (product.is_dynamic_pricing_active && product.dynamic_price) {
      return product.dynamic_price;
    }
    // Apply regular discount
    return product.price * (1 - product.discount_percentage / 100);
  };

  const getOriginalPrice = () => {
    if (product.is_dynamic_pricing_active && product.dynamic_price) {
      return product.base_price || product.price;
    }
    return product.price;
  };

  const getDiscountPercentage = () => {
    if (product.is_dynamic_pricing_active && product.dynamic_price && product.base_price) {
      return ((product.base_price - product.dynamic_price) / product.base_price * 100).toFixed(0);
    }
    return product.discount_percentage;
  };

  const displayPrice = getDisplayPrice();
  const originalPrice = getOriginalPrice();
  const discountPct = getDiscountPercentage();
  const hasDiscount = product.is_dynamic_pricing_active ? 
    (product.dynamic_price && product.base_price && product.dynamic_price < product.base_price) : 
    (product.discount_percentage > 0);

  return (
    <div className="product-card">
      <img 
        src={imgSrc} 
        alt={product.title}
        className="product-image"
        onError={handleImageError}
      />
      <div className="product-info">
        <h3>{product.title}</h3>
        <p className="product-brand">{product.brand}</p>
        <div className="product-price-container">
          {hasDiscount && (
            <span className="product-original-price">${originalPrice.toFixed(2)}</span>
          )}
          <span className="product-price">${displayPrice.toFixed(2)}</span>
          {hasDiscount && (
            <span className="product-discount">-{discountPct}%</span>
          )}
        </div>
        <p className="product-rating">⭐ {product.rating.toFixed(1)}</p>
        <p className={`product-stock ${product.stock === 0 ? 'out-of-stock' : ''}`}>
          {product.stock > 0 ? `${product.stock} in stock` : 'Out of stock'}
        </p>
        <div className="product-actions">
          <Link to={`/products/${product.id}`} className="btn btn-secondary">
            View Details
          </Link>
          <button 
            onClick={handleAddToCart} 
            className="btn btn-primary"
            disabled={product.stock === 0}
          >
            Add to Cart
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;
