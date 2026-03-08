import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { productsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';

const ProductDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { addToCart } = useCart();
  
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(null);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    fetchProduct();
  }, [id]);

  const fetchProduct = async () => {
    try {
      const response = await productsAPI.getById(id);
      setProduct(response.data.data);
      setSelectedImage(response.data.data.thumbnail);
    } catch (error) {
      console.error('Error fetching product:', error);
      navigate('/products');
    }
    setLoading(false);
  };

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    setAdding(true);
    const result = await addToCart(product.id, quantity);
    if (result.success) {
      alert(`Added ${quantity} item(s) to cart!`);
    } else {
      alert(result.error);
    }
    setAdding(false);
  };

  if (loading) {
    return <div className="loading">Loading product...</div>;
  }

  if (!product) {
    return <div className="loading">Product not found</div>;
  }

  return (
    <div className="product-detail">
      <div className="product-detail-images">
        <img 
          src={selectedImage || product.thumbnail || 'https://via.placeholder.com/500x400?text=No+Image'} 
          alt={product.title}
          className="product-detail-image"
          onError={(e) => {
            if (e.target.src !== 'https://via.placeholder.com/500x400?text=No+Image') {
              e.target.src = 'https://via.placeholder.com/500x400?text=No+Image';
            }
          }}
        />
        {product.images && product.images.length > 0 && (
          <div className="product-images-gallery">
            <img 
              src={product.thumbnail}
              alt="Thumbnail"
              className={selectedImage === product.thumbnail ? 'active' : ''}
              onClick={() => setSelectedImage(product.thumbnail)}
              onError={(e) => { e.target.style.display = 'none'; }}
            />
            {product.images.map((img, index) => (
              <img 
                key={index}
                src={img}
                alt={`${product.title} ${index + 1}`}
                className={selectedImage === img ? 'active' : ''}
                onClick={() => setSelectedImage(img)}
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            ))}
          </div>
        )}
      </div>

      <div className="product-detail-info">
        <h1>{product.title}</h1>
        <p className="product-brand">Brand: {product.brand}</p>
        <p className="product-rating">⭐ {product.rating.toFixed(1)} / 5</p>
        
        {/* Dynamic pricing display */}
        {product.is_dynamic_pricing_active && product.dynamic_price ? (
          <div className="product-price-container">
            <p className="product-price">
              ${product.dynamic_price.toFixed(2)}
              {product.discount_percentage > 0 && (
                <span className="product-discount"> -{product.discount_percentage}% OFF</span>
              )}
            </p>
            {product.dynamic_price < product.base_price && (
              <p className="product-original-price">
                <span className="strikethrough">${(product.base_price || product.price).toFixed(2)}</span>
                <span className="savings-badge">
                  Save ${((product.base_price || product.price) - product.dynamic_price).toFixed(2)}!
                </span>
              </p>
            )}
          </div>
        ) : (
          <p className="product-price">
            ${product.price.toFixed(2)}
            {product.discount_percentage > 0 && (
              <span className="product-discount"> -{product.discount_percentage}% OFF</span>
            )}
          </p>
        )}

        <p className="product-description">{product.description}</p>

        <p className={`product-stock ${product.stock === 0 ? 'out-of-stock' : ''}`}>
          {product.stock > 0 ? `${product.stock} items in stock` : 'Out of stock'}
        </p>

        {product.category && (
          <p style={{ color: '#7f8c8d', marginBottom: '20px' }}>
            Category: {product.category.name}
          </p>
        )}

        {product.stock > 0 && (
          <>
            <div className="quantity-selector">
              <button 
                onClick={() => setQuantity(q => Math.max(1, q - 1))}
                disabled={quantity <= 1}
              >
                -
              </button>
              <span>{quantity}</span>
              <button 
                onClick={() => setQuantity(q => Math.min(product.stock, q + 1))}
                disabled={quantity >= product.stock}
              >
                +
              </button>
            </div>

            <button 
              onClick={handleAddToCart} 
              className="btn btn-success"
              disabled={adding}
              style={{ width: '100%', padding: '15px', fontSize: '16px' }}
            >
              {adding ? 'Adding...' : `Add to Cart - $${((product.is_dynamic_pricing_active && product.dynamic_price ? product.dynamic_price : product.price) * quantity).toFixed(2)}`}
            </button>
          </>
        )}

        <button 
          onClick={() => navigate('/products')} 
          className="btn btn-secondary"
          style={{ width: '100%', marginTop: '15px' }}
        >
          ← Back to Products
        </button>
      </div>
    </div>
  );
};

export default ProductDetail;
