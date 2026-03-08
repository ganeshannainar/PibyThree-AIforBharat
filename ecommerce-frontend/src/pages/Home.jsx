import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { productsAPI, promotionsAPI } from '../services/api';
import ProductCard from '../components/ProductCard';
import './Home.css';

const Home = () => {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [promotions, setPromotions] = useState([]);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [loading, setLoading] = useState(true);
  const [autoPlay, setAutoPlay] = useState(true);
  const slideInterval = useRef(null);

  useEffect(() => {
    fetchFeaturedProducts();
    fetchPromotions();
  }, []);

  // Auto-play carousel
  useEffect(() => {
    if (autoPlay && promotions.length > 1) {
      slideInterval.current = setInterval(() => {
        setCurrentSlide(prev => (prev + 1) % promotions.length);
      }, 5000); // Change slide every 5 seconds
    }
    return () => {
      if (slideInterval.current) clearInterval(slideInterval.current);
    };
  }, [autoPlay, promotions.length]);

  const fetchFeaturedProducts = async () => {
    try {
      const response = await productsAPI.getAll(1, 8);
      setFeaturedProducts(response.data.data || []);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
    setLoading(false);
  };

  const fetchPromotions = async () => {
    try {
      const response = await promotionsAPI.getCarousel(5);
      setPromotions(response.data.promotions || []);
    } catch (error) {
      console.error('Error fetching promotions:', error);
    }
  };

  const nextSlide = () => {
    setCurrentSlide(prev => (prev + 1) % promotions.length);
  };

  const prevSlide = () => {
    setCurrentSlide(prev => (prev - 1 + promotions.length) % promotions.length);
  };

  const goToSlide = (index) => {
    setCurrentSlide(index);
  };

  const handleMouseEnter = () => setAutoPlay(false);
  const handleMouseLeave = () => setAutoPlay(true);

  const renderPromoCarousel = () => {
    if (promotions.length === 0) {
      // No promotions - don't show hero section
      return null;
    }

    return (
      <div
        className="promo-carousel"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        <div className="carousel-container">
          <div
            className="carousel-track"
            style={{ transform: `translateX(-${currentSlide * 100}%)` }}
          >
            {promotions.map((promo, index) => (
              <div key={promo.id} className="carousel-slide">
                <div className="promo-banner">
                  <div className="promo-image-container">
                    <img
                      src={promo.promotion_image_url || promo.product_thumbnail}
                      alt={promo.product_title}
                      className="promo-image"
                      onError={(e) => {
                        e.target.src = 'https://via.placeholder.com/600x400?text=Special+Offer';
                      }}
                    />
                    {promo.original_price > promo.dynamic_price && (
                      <div className="promo-overlay">
                        <div className="promo-discount-badge">
                          {promo.discount_percentage.toFixed(0)}% OFF
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="promo-content">
                    <div className="promo-headline">{promo.headline}</div>
                    <h2 className="promo-product-title">{promo.product_title}</h2>
                    <p className="promo-brand">{promo.product_brand} • {promo.category_name}</p>
                    <div className="promo-pricing">
                      {promo.original_price > promo.dynamic_price && (
                        <span className="promo-original-price">${promo.original_price.toFixed(2)}</span>
                      )}
                      <span className="promo-dynamic-price">${promo.dynamic_price.toFixed(2)}</span>
                      {promo.original_price > promo.dynamic_price && (
                        <span className="promo-savings">Save ${promo.savings_amount.toFixed(2)}</span>
                      )}
                    </div>
                    <p className="promo-tagline">{promo.tagline}</p>
                    <Link to={`/products/${promo.product_id}`} className="btn btn-primary promo-cta">
                      Shop Now
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Navigation Arrows */}
        {promotions.length > 1 && (
          <>
            <button className="carousel-arrow carousel-prev" onClick={prevSlide}>
              ‹
            </button>
            <button className="carousel-arrow carousel-next" onClick={nextSlide}>
              ›
            </button>
          </>
        )}

        {/* Dots Indicator */}
        {promotions.length > 1 && (
          <div className="carousel-dots">
            {promotions.map((_, index) => (
              <button
                key={index}
                className={`carousel-dot ${index === currentSlide ? 'active' : ''}`}
                onClick={() => goToSlide(index)}
              />
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="home-page">
      {renderPromoCarousel()}

      <div className="featured-section">
        <h2>Featured Products</h2>
        {loading ? (
          <div className="loading">Loading products...</div>
        ) : featuredProducts.length > 0 ? (
          <div className="products-grid">
            {featuredProducts.map(product => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        ) : (
          <p style={{ textAlign: 'center', color: '#7f8c8d' }}>
            No products available yet. Check back soon!
          </p>
        )}
      </div>

      {featuredProducts.length > 0 && (
        <div style={{ textAlign: 'center', marginTop: '20px' }}>
          <Link to="/products" className="btn btn-secondary" style={{ display: 'inline-block', width: 'auto' }}>
            View All Products
          </Link>
        </div>
      )}
    </div>
  );
};

export default Home;
