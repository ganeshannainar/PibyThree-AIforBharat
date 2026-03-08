import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { chatAPI, promotionsAPI, priceComparisonAPI, ordersAPI, productsAPI } from '../services/api'; // Import APIs
import { useCart } from '../context/CartContext'; // Import useCart
import { useAuth } from '../context/AuthContext'; // Import useAuth
import './AIStylistChat.css';

/**
 * Left Panel Mode Constants
 * Controls what content is displayed in the left panel
 */
export const LEFT_PANEL_MODES = {
    WELCOME: 'WELCOME',
    KNOWLEDGE_BASE: 'KNOWLEDGE_BASE',
    CAROUSEL: 'CAROUSEL', // New mode for promotions
    CART: 'CART', // New mode for cart view
    ORDER_SUCCESS: 'ORDER_SUCCESS', // New mode for order confirmation
    PAST_ORDERS: 'PAST_ORDERS', // Added mode for past orders
};

/**
 * ChatLauncher - Floating trigger button (bottom-right)
 */
const ChatLauncher = ({ onClick, isVisible }) => {
    const [isHovered, setIsHovered] = useState(false);

    if (!isVisible) return null;

    return (
        <button
            className="chat-launcher"
            onClick={onClick}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            aria-label="Open AI Shopping Assistant"
        >
            <span className="chat-launcher-icon">💬</span>
            <span className="chat-launcher-pulse"></span>
            {isHovered && (
                <span className="chat-launcher-tooltip">AI Assistant</span>
            )}
        </button>
    );
};

/**
 * PromotionCarousel - Displays active promotions
 */
const PromotionCarousel = () => {
    const [promotions, setPromotions] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchPromotions = async () => {
            try {
                const response = await promotionsAPI.getCarousel(5);
                // API returns { success, promotions: [], total } or just active items list directly? 
                // Based on promotions.py: get_active_promotions returns List[PromotionCarouselItem] directly if called internally, 
                // but via API it likely returns { success, promotions, ... } or list. 
                // Checking api.js: returns api.get(...) result.
                // Let's handle generic list response.
                const data = response.data;
                const items = Array.isArray(data) ? data : (data.promotions || []);
                setPromotions(items);
            } catch (error) {
                console.error("Failed to fetch promotions", error);
            } finally {
                setLoading(false);
            }
        };
        fetchPromotions();
    }, []);

    useEffect(() => {
        if (promotions.length <= 1) return;
        const interval = setInterval(() => {
            setCurrentIndex((prev) => (prev + 1) % promotions.length);
        }, 5000); // Auto-rotate every 5s
        return () => clearInterval(interval);
    }, [promotions.length]);

    if (loading) return <div className="promo-loading">Loading deals...</div>;
    if (promotions.length === 0) return (
        <div className="panel-welcome">
            <h2>Welcome</h2>
            <p>AI Shopping Assistant</p>
            <div className="capabilities-list">
                <h4>I can help you with:</h4>
                <ul>
                    <li>🔍 Find products by name</li>
                    <li>⭐ Discover top-rated items</li>
                    <li>💰 Find deals and discounts</li>
                </ul>
            </div>
        </div>
    );

    const promo = promotions[currentIndex];

    return (
        <div className="promo-carousel">
            <div className="promo-header">
                <h3>🔥 Hot Deals</h3>
                <div className="promo-indicators">
                    {promotions.map((_, idx) => (
                        <span
                            key={idx}
                            className={`indicator ${idx === currentIndex ? 'active' : ''}`}
                            onClick={() => setCurrentIndex(idx)}
                        />
                    ))}
                </div>
            </div>

            <div className="promo-card">
                <div className="promo-image-container">
                    <img
                        src={promo.promotion_image_url || promo.product_thumbnail}
                        alt={promo.product_title}
                        className="promo-image"
                    />
                    <span className="promo-badge">-{Math.round(promo.discount_percentage)}%</span>
                </div>
                <div className="promo-content">
                    <h4>{promo.headline}</h4>
                    <p className="promo-tagline">{promo.tagline}</p>
                    <div className="promo-price-row">
                        <span className="promo-original">${promo.original_price.toFixed(2)}</span>
                        <span className="promo-dynamic">${promo.dynamic_price.toFixed(2)}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

/**
 * ChatCart - Displays items currently in cart
 */
const ChatCart = ({ onCheckoutSuccess }) => {
    const { cart, checkout, loading } = useCart();
    const [isCheckingOut, setIsCheckingOut] = useState(false);

    if (!cart || !cart.cart_items || cart.cart_items.length === 0) {
        return (
            <div className="chat-cart-empty">
                <span className="cart-icon-large">🛒</span>
                <p>Your cart is empty</p>
                <small>Add items from the chat!</small>
            </div>
        );
    }

    const total = cart.cart_items.reduce((sum, item) => {
        // Calculate price (handling dynamic price if available in item logic, but usually cart has unit_price)
        // Assuming cart item structure has product details or we might need to fetch them.
        // For simplicity, using cart properties if available. 
        // Note: The cart context/API might populate product details differently.
        return sum + (item.quantity * (item.price || 0));
    }, 0);

    const handleCheckout = async () => {
        setIsCheckingOut(true);
        const result = await checkout();
        setIsCheckingOut(false);
        if (result.success) {
            onCheckoutSuccess();
        } else {
            alert("Checkout Failed: " + result.error);
        }
    };

    return (
        <div className="chat-cart">
            <h3>🛒 Your Cart ({cart.cart_items.length})</h3>
            <div className="chat-cart-items">
                {cart.cart_items.map((item, idx) => (
                    <div key={idx} className="chat-cart-item">
                        <div className="chat-cart-thumb">
                            {/* Ideally verify if product object exists on item */}
                            {item.product?.thumbnail ? (
                                <img src={item.product.thumbnail} alt={item.product.title} />
                            ) : (
                                <span className="placeholder-thumb">🛍️</span>
                            )}
                        </div>
                        <div className="chat-cart-details">
                            <div className="chat-cart-title">{item.product?.title || `Product #${item.product_id}`}</div>
                            <div className="chat-cart-meta">
                                Qty: {item.quantity}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
            <div className="chat-cart-footer">
                <button
                    className="btn-place-order"
                    onClick={handleCheckout}
                    disabled={isCheckingOut || loading}
                >
                    {isCheckingOut ? 'Placing Order...' : '✨ Place Order Now'}
                </button>
                <button className="btn-view-cart text-link" onClick={() => window.location.href = '/cart'}>
                    View Full Cart
                </button>
            </div>
        </div>
    );
};

/**
 * OrderSuccess - Displays success message after checkout
 */
const OrderSuccess = ({ onContinueShopping, onShowOrders }) => {
    return (
        <div className="order-success-panel">
            <div className="success-icon">🎉</div>
            <h3>Order Placed!</h3>
            <p>Your order has been successfully placed.</p>

            <div className="success-actions">
                <button className="btn-past-orders" onClick={onShowOrders}>
                    View Past Orders
                </button>
                <button className="btn-continue-shopping" onClick={onContinueShopping}>
                    Continue Shopping
                </button>
            </div>
        </div>
    );
};

/**
 * PastOrdersList - Displays past orders in the left panel
 */
const PastOrdersList = ({ onSelectOrder }) => {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchOrders = async () => {
            try {
                const response = await ordersAPI.getAll(1, 10);
                setOrders(response.data.data || []);
            } catch (error) {
                console.error("Failed to fetch orders", error);
            } finally {
                setLoading(false);
            }
        };
        fetchOrders();
    }, []);

    if (loading) return <div className="panel-loading">Loading orders...</div>;
    if (orders.length === 0) return <div className="panel-empty">No orders yet.</div>;

    return (
        <div className="past-orders-panel">
            <h3>📦 Past Orders</h3>
            <div className="orders-summary-list">
                {orders.map(order => (
                    <div key={order.id} className="order-summary-item" onClick={() => onSelectOrder(order.id)}>
                        <div className="order-summary-header">
                            <span className="order-id">#{order.id}</span>
                            <span className="order-status-badge" data-status={order.status}>{order.status}</span>
                        </div>
                        <div className="order-summary-meta">
                            <span>{new Date(order.created_at).toLocaleDateString()}</span>
                            <span className="order-amount">${order.total_amount.toFixed(2)}</span>
                        </div>
                    </div>
                ))}
            </div>
            <button className="btn-view-all-orders" onClick={() => window.location.href = '/orders'}>
                Go to Orders Page
            </button>
        </div>
    );
};

/**
 * PriceComparisonCard - Displays prices from different platforms
 */
const PriceComparisonCard = ({ data, onProductClick }) => {
    if (!data) return null;

    return (
        <div className="price-comparison-card">
            <div className="comparison-header">
                {data.thumbnail && <img src={data.thumbnail} alt={data.product_name} className="comparison-thumb" />}
                <h4>Price Comparison: {data.product_name}</h4>
            </div>
            <div className="comparison-platforms">
                <div className="platform-row our-platform">
                    <span className="platform-name">Our Store</span>
                    <span className="platform-price">{data.our_price ? `$${data.our_price.toFixed(2)}` : 'N/A'}</span>
                    {data.our_price ? (
                        <button
                            className="platform-link-btn"
                            onClick={() => onProductClick({ id: data.our_url?.split('/').pop(), title: data.product_name, price: data.our_price, thumbnail: data.thumbnail })}
                        >
                            View Item
                        </button>
                    ) : (
                        <span className="platform-link-disabled">Best Value</span>
                    )}
                </div>

                {data.amazon_best && (
                    <div className="platform-row amazon">
                        <span className="platform-name">Amazon</span>
                        <span className="platform-price">{data.amazon_best.price}</span>
                        <a href={data.amazon_best.link} target="_blank" rel="noopener noreferrer" className="platform-link">Visit Amazon</a>
                    </div>
                )}

                {data.walmart_best && (
                    <div className="platform-row walmart">
                        <span className="platform-name">Walmart</span>
                        <span className="platform-price">{data.walmart_best.price}</span>
                        <a href={data.walmart_best.link} target="_blank" rel="noopener noreferrer" className="platform-link">Visit Walmart</a>
                    </div>
                )}
            </div>
        </div>
    );
};

/**
 * OrderDetailView - Displays order details in the chat workspace
 */
const OrderDetailView = ({ orderId }) => {
    const [order, setOrder] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchOrderDetails = async () => {
            try {
                const response = await ordersAPI.getById(orderId);
                setOrder(response.data.data);
            } catch (error) {
                console.error("Failed to fetch order details", error);
            } finally {
                setLoading(false);
            }
        };
        fetchOrderDetails();
    }, [orderId]);

    if (loading) return <div className="detail-loading">Loading order details...</div>;
    if (!order) return <div className="detail-error">Order not found.</div>;

    return (
        <div className="order-detail-view">
            <div className="order-detail-header">
                <h3>Order #{order.id}</h3>
                <span className="order-status-large" data-status={order.status}>{order.status.toUpperCase()}</span>
            </div>
            <div className="order-items-detail">
                {order.order_items.map((item, idx) => (
                    <div key={idx} className="order-item-row">
                        <div className="item-name">{item.product_title}</div>
                        <div className="item-meta">
                            <span>{item.quantity} x ${item.product_price.toFixed(2)}</span>
                            <span className="item-subtotal">${item.subtotal.toFixed(2)}</span>
                        </div>
                    </div>
                ))}
            </div>
            <div className="order-detail-footer">
                <div className="total-label">Total Amount Paid</div>
                <div className="total-value">${order.total_amount.toFixed(2)}</div>
            </div>
            <p className="order-date-full">Placed on {new Date(order.created_at).toLocaleString()}</p>
        </div>
    );
};

/**
 * ProductDetailView - Displays full product details within the chat interface
 */
/**
 * ProductDetailView - Displays full product details within the chat interface
 */
const ProductDetailView = ({ product, onAddToCart }) => {
    const [comparisonData, setComparisonData] = useState(null);
    const [loadingComparison, setLoadingComparison] = useState(false);
    const [showComparison, setShowComparison] = useState(false);

    if (!product) return null;

    const price = (product.is_dynamic_pricing_active && product.dynamic_price)
        ? product.dynamic_price
        : (product.price || 0) * (1 - (product.discount_percentage || 0) / 100);

    const handleCheckPrices = async () => {
        if (comparisonData) {
            setShowComparison(true);
            return;
        }

        setLoadingComparison(true);
        setShowComparison(true);
        try {
            const response = await priceComparisonAPI.compare(product.title);
            setComparisonData(response.data);
        } catch (error) {
            console.error("Failed to fetch price comparison", error);
        } finally {
            setLoadingComparison(false);
        }
    };

    return (
        <div className="product-detail-view">
            <div className="detail-content">
                <div className="detail-image-container">
                    <img
                        src={product.thumbnail || 'https://via.placeholder.com/300x300?text=No+Image'}
                        alt={product.title}
                        className="detail-image"
                    />
                    {product.discount_percentage > 0 && (
                        <div className="detail-badge">-{Math.round(product.discount_percentage)}%</div>
                    )}
                </div>
                <div className="detail-info">
                    <div className="detail-header">
                        <h3 className="detail-title">{product.title}</h3>
                        <p className="detail-brand">{product.brand}</p>
                    </div>

                    <div className="detail-price-row">
                        <span className="detail-price">${price.toFixed(2)}</span>
                        {product.discount_percentage > 0 && (
                            <span className="detail-original-price">${product.price?.toFixed(2)}</span>
                        )}
                    </div>

                    <div className="detail-rating">
                        {'⭐'.repeat(Math.round(product.rating || 0))}
                        <span className="rating-text">({product.rating?.toFixed(1) || 'No ratings'})</span>
                    </div>

                    <p className="detail-description">{product.description || 'No description available.'}</p>

                    <div className="detail-actions">
                        <button
                            className="btn-add-to-cart-large"
                            onClick={() => onAddToCart(product.id)}
                        >
                            Add to Cart 🛒
                        </button>
                        <button
                            className="btn-check-prices"
                            onClick={handleCheckPrices}
                            disabled={loadingComparison}
                            style={{
                                marginTop: '10px',
                                backgroundColor: '#f0f0f0',
                                color: '#333',
                                border: '1px solid #ccc',
                                width: '100%'
                            }}
                        >
                            {loadingComparison ? 'Checking External Prices...' : '🔍 Compare with Amazon & Walmart'}
                        </button>
                    </div>

                    {showComparison && (
                        <div className="price-comparison-results" style={{ marginTop: '20px', borderTop: '1px solid #eee', paddingTop: '15px' }}>
                            {loadingComparison ? (
                                <p>Searching specifically for "{product.title}"...</p>
                            ) : comparisonData ? (
                                <PriceComparisonCard
                                    data={{
                                        product_name: product.title,
                                        thumbnail: product.thumbnail,
                                        our_price: price,
                                        our_url: `/products/${product.id}`,
                                        amazon_best: comparisonData.amazon_best,
                                        walmart_best: comparisonData.walmart_best
                                    }}
                                    onProductClick={() => { }}
                                />
                            ) : (
                                <p>Could not fetch comparison data.</p>
                            )}
                        </div>
                    )}

                    <div className="detail-meta">
                        <div className="meta-item">
                            <span className="meta-label">Availability:</span>
                            <span className={`meta-value ${product.stock > 0 ? 'text-green' : 'text-red'}`}>
                                {product.stock > 0 ? 'In Stock' : 'Out of Stock'}
                            </span>
                        </div>
                        {product.category_id && (
                            <div className="meta-item">
                                <span className="meta-label">Category ID:</span>
                                <span className="meta-value">{product.category_id}</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

/**
 * LeftPanel - Context Rail (30% width)
 * Displays different content based on leftPanelMode
 */
const LeftPanel = ({ mode, setMode }) => {
    return (
        <aside className="ai-left-panel">
            <div className="left-panel-content">
                {mode === LEFT_PANEL_MODES.WELCOME && (
                    <div className="panel-welcome">
                        <h2>Welcome</h2>
                        <p>AI Shopping Assistant</p>
                        <div className="capabilities-list">
                            <h4>I can help you with:</h4>
                            <ul>
                                <li>🔍 Find products by name, category, or price</li>
                                <li>⭐ Discover top-rated items</li>
                                <li>💰 Find deals and discounts</li>
                                <li>📦 Check product availability</li>
                                <li>🛒 Get personalized recommendations</li>
                            </ul>
                        </div>
                    </div>
                )}
                {mode === LEFT_PANEL_MODES.KNOWLEDGE_BASE && (
                    <div className="panel-knowledge-base">
                        <h3>Knowledge Base</h3>
                        <p>Connected to product database</p>
                        <div className="data-sources">
                            <div className="source-item">✓ Products Catalog</div>
                            <div className="source-item">✓ Categories</div>
                            <div className="source-item">✓ Pricing Data</div>
                            <div className="source-item">✓ Inventory Status</div>
                        </div>
                    </div>
                )}
                {mode === LEFT_PANEL_MODES.CAROUSEL && <PromotionCarousel />}
                {mode === LEFT_PANEL_MODES.CART && (
                    <ChatCart onCheckoutSuccess={() => setMode(LEFT_PANEL_MODES.ORDER_SUCCESS)} />
                )}
                {mode === LEFT_PANEL_MODES.ORDER_SUCCESS && (
                    <OrderSuccess
                        onContinueShopping={() => setMode(LEFT_PANEL_MODES.CAROUSEL)}
                        onShowOrders={() => setMode(LEFT_PANEL_MODES.PAST_ORDERS)}
                    />
                )}
                {mode === LEFT_PANEL_MODES.PAST_ORDERS && (
                    <PastOrdersList onSelectOrder={(id) => setMode(id)} /> // Temporary: logic to show order details
                )}
            </div>
        </aside>
    );
};

/**
 * RightPanel - Chat Workspace (70% width)
 * Contains the chat stream and input area
 */
const RightPanel = ({ conversationHistory, onSendMessage, onClose, isLoading, onProductClick, viewMode, selectedProduct, onBackToChat, onAddToCart, onViewOrder }) => {
    const [inputValue, setInputValue] = useState('');
    const chatStreamRef = useRef(null);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        if (chatStreamRef.current && viewMode === 'CHAT') {
            chatStreamRef.current.scrollTop = chatStreamRef.current.scrollHeight;
        }
    }, [conversationHistory, viewMode]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (inputValue.trim() && !isLoading) {
            onSendMessage(inputValue.trim());
            setInputValue('');
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    if (viewMode === 'PRODUCT_DETAIL' && selectedProduct) {
        return (
            <main className="ai-right-panel">
                <header className="right-panel-header" style={{ justifyContent: 'space-between' }}>
                    <button className="btn-back-header" onClick={onBackToChat}>
                        ← Back
                    </button>
                    <h2>Product Details</h2>
                    <button className="btn-close" onClick={onClose}>
                        Close
                    </button>
                </header>
                <ProductDetailView
                    product={selectedProduct}
                    onAddToCart={onAddToCart}
                />
            </main>
        );
    }
    if (viewMode === 'ORDER_DETAIL' && selectedProduct) {
        return (
            <main className="ai-right-panel">
                <header className="right-panel-header" style={{ justifyContent: 'space-between' }}>
                    <button className="btn-back-header" onClick={onBackToChat}>
                        ← Back
                    </button>
                    <h2>Order Details</h2>
                    <button className="btn-close" onClick={onClose}>
                        Close
                    </button>
                </header>
                <OrderDetailView
                    orderId={selectedProduct}
                />
            </main>
        );
    }

    return (
        <main className="ai-right-panel">
            <header className="right-panel-header">
                <button className="btn-close" onClick={onClose}>
                    Close Chat
                </button>
                <h2>AI Shopping Assistant</h2>
            </header>
            <div className="chat-stream" ref={chatStreamRef}>
                {conversationHistory.length === 0 ? (
                    <div className="chat-welcome">
                        <div className="chat-welcome-icon">🛍️</div>
                        <h3>How can I help you today?</h3>
                        <p>Ask me about products, styles, recommendations, or anything else!</p>
                        <div className="chat-suggestions">
                            <button className="suggestion-chip" onClick={() => onSendMessage("What are the top rated products?")}>
                                Top rated products
                            </button>
                            <button className="suggestion-chip" onClick={() => onSendMessage("Show me products under $50")}>
                                Products under $50
                            </button>
                            <button className="suggestion-chip" onClick={() => onSendMessage("What electronics do you have?")}>
                                Electronics
                            </button>
                        </div>
                    </div>
                ) : (
                    <>
                        {conversationHistory.map((message) => (
                            <div key={message.id} className={`chat-message ${message.type}`}>
                                <div className="message-avatar">
                                    {message.type === 'user' ? '👤' : '💬'}
                                </div>
                                <div className="message-content">
                                    <div className="message-text" dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }} />

                                    {/* Order Button - shown below "order placed" message */}
                                    {message.data && message.data.some(d => d.action === 'cart_updated' && d.type === 'place_order') && (
                                        <div className="order-action-row">
                                            <button
                                                className="btn-view-order-details"
                                                onClick={() => onViewOrder(message.data.find(d => d.type === 'place_order').order_id)}
                                            >
                                                📄 View Order Details
                                            </button>
                                        </div>
                                    )}

                                    {message.data && message.data.length > 0 && (
                                        <div className="message-data-container">
                                            {/* Specialized Card for Price Comparison */}
                                            {message.data.find(d => d.action === 'price_comparison') && (
                                                <PriceComparisonCard
                                                    data={message.data.find(d => d.action === 'price_comparison')}
                                                    onProductClick={onProductClick}
                                                />
                                            )}

                                            {/* Product Grid - Filtered to exclude utility data */}
                                            <div className="message-products-grid">
                                                {message.data
                                                    .filter(item => !['cart_updated', 'price_comparison'].includes(item.action))
                                                    .slice(0, 6)
                                                    .map((product, idx) => (
                                                        <div
                                                            key={idx}
                                                            className="product-card-chat"
                                                        >
                                                            <div
                                                                className="product-card-chat-click-area"
                                                                onClick={() => onProductClick(product)}
                                                            >
                                                                <img
                                                                    src={product.thumbnail || 'https://via.placeholder.com/100x100?text=No+Image'}
                                                                    alt={product.title}
                                                                    className="product-card-chat-image"
                                                                    onError={(e) => { e.target.src = 'https://via.placeholder.com/100x100?text=No+Image'; }}
                                                                />
                                                                <div className="product-card-chat-info">
                                                                    <strong className="product-card-chat-title">{product.title}</strong>
                                                                    <span className="product-card-chat-brand">{product.brand}</span>
                                                                    <div className="product-card-chat-price-row">
                                                                        <span className="product-card-chat-price">
                                                                            ${(product.is_dynamic_pricing_active && product.dynamic_price
                                                                                ? product.dynamic_price
                                                                                : product.price * (1 - (product.discount_percentage || 0) / 100)
                                                                            ).toFixed(2)}
                                                                        </span>
                                                                        {product.rating && <span className="product-card-chat-rating">⭐ {product.rating.toFixed(1)}</span>}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                            <button
                                                                className="btn-chat-add-to-cart"
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    onProductClick(product, true); // true indicates add to cart
                                                                }}
                                                            >
                                                                Add to Cart 🛒
                                                            </button>
                                                        </div>
                                                    ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="chat-message assistant">
                                <div className="message-avatar">
                                    💬
                                </div>
                                <div className="message-content">
                                    <div className="typing-indicator">
                                        <span></span>
                                        <span></span>
                                        <span></span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
            <form className="chat-input-area" onSubmit={handleSubmit}>
                <div className="input-wrapper">
                    <textarea
                        className="chat-input"
                        placeholder="Ask me anything about products, styles, or recommendations..."
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        rows={1}
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        className="send-button"
                        disabled={!inputValue.trim() || isLoading}
                    >
                        <span className="send-icon">➤</span>
                    </button>
                </div>
                <p className="input-hint">Press Enter to send, Shift+Enter for new line</p>
            </form>
        </main>
    );
};

/**
 * Format message content - convert markdown-like syntax to HTML
 */
function formatMessage(content) {
    if (!content) return '';

    // Convert **bold** to <strong>
    let formatted = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Convert *italic* to <em>
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Convert newlines to <br>
    formatted = formatted.replace(/\n/g, '<br>');

    // Convert bullet lists (- item)
    formatted = formatted.replace(/^- (.*)$/gm, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    return formatted;
}

/**
 * AIStylistChat - Main Component
 * Dual-Pane Layout: 30% Left Panel, 70% Right Panel
 */
const AIStylistChat = () => {
    const navigate = useNavigate();

    // ========== ESSENTIAL STATE ==========

    // useAuth hook for global authentication state
    const { isAuthenticated, loading: isCheckingAuth } = useAuth();

    // Controls overlay visibility
    const [isChatOpen, setIsChatOpen] = useState(false);

    // Stores all messages in the conversation
    const [conversationHistory, setConversationHistory] = useState([]);

    // Controls the Left Panel content - default to CAROUSEL
    const [leftPanelMode, setLeftPanelMode] = useState(LEFT_PANEL_MODES.CAROUSEL);

    // Controls the Right Panel content - CHAT, PRODUCT_DETAIL, or ORDER_DETAIL
    const [rightPanelMode, setRightPanelMode] = useState('CHAT');
    const [selectedProduct, setSelectedProduct] = useState(null);

    // Access Cart Context
    const { addToCart, refreshCart } = useCart();

    // Loading state for API calls
    const [isLoading, setIsLoading] = useState(false);

    const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

    // ========== HANDLERS ==========

    const handleOpenChat = useCallback(() => {
        setIsChatOpen(true);
    }, []);

    const handleCloseChat = useCallback(() => {
        setIsChatOpen(false);
    }, []);

    const handleProductClick = useCallback((productOrId, isAddToCart = false) => {
        // If productOrId is an object (product data), use it. If it's an ID, we might need to find it or fetch it.
        // For 'Add to Cart', we need ID. For 'View', we prefer the object to avoid fetch, but if ID passed we need to handle.
        // Currently onProductClick is called with product.id.
        // We should update the call site to pass the whole product object if possible, or we search in history.

        // However, the caller `onProductClick(product.id)` in render map passes ID. 
        // Let's modify the Caller to pass the whole product object first.
        // Wait, I can't modify the caller easily in this replace block without logic change.
        // I'll update the render logic later. For now, let's assume we can find the product in conversationHistory?
        // Actually, let's look at `handleProductClick` signature. It receives `productId`.
        // We need to change the caller in `RightPanel` to pass the product object.

        // But for now, let's assume I will change the caller. 
        // Logic: if isAddToCart, do cart logic.
        // If view, switch mode.

        if (isAddToCart) {
            // Check if productOrId is object or ID
            const id = typeof productOrId === 'object' ? productOrId.id : productOrId;
            addToCart(id, 1).then(() => {
                setLeftPanelMode(LEFT_PANEL_MODES.CART);
            });
        } else {
            // View Mode
            if (typeof productOrId === 'object') {
                setSelectedProduct(productOrId);
                setRightPanelMode('PRODUCT_DETAIL');
            } else {
                // Determine logic if ID is passed.
                // For this implementation plan, we'll try to ensure object is passed.
                // Fallback: navigate as before? No, user wants in-chat. 
                // We'll trust the caller to be updated.
            }
        }
    }, [addToCart]);

    // Corrected `handleProductClick` that accepts product object or ID. 
    // To make it robust without changing caller yet (caller passes ID), we need to find the product.
    // But since I'm updating the caller in the same file (RightPanel), I can ensure object is passed.

    const handleProductClickWrapper = useCallback(async (product, isAddToCart = false) => {
        let fullProduct = product;

        // If only ID is provided (e.g. from comparison card), fetch full details
        if (typeof product === 'object' && product.id && !product.description) {
            try {
                console.log("Fetching full product details for ID:", product.id);
                const res = await productsAPI.getById(product.id);
                if (res.data && res.data.data) {
                    fullProduct = res.data.data;
                }
            } catch (err) {
                console.error("Failed to fetch full product details", err);
            }
        } else if (typeof product === 'string' || typeof product === 'number') {
            // If just an ID was passed
            try {
                const res = await productsAPI.getById(product);
                if (res.data && res.data.data) {
                    fullProduct = res.data.data;
                }
            } catch (err) {
                console.error("Failed to fetch product by ID", err);
            }
        }

        if (isAddToCart) {
            if (fullProduct && fullProduct.id) {
                addToCart(fullProduct.id, 1).then(() => {
                    setLeftPanelMode(LEFT_PANEL_MODES.CART);
                });
            }
        } else if (fullProduct) {
            setSelectedProduct(fullProduct);
            setRightPanelMode('PRODUCT_DETAIL');
        }
    }, [addToCart]);

    const handleBackToChat = useCallback(() => {
        setRightPanelMode('CHAT');
        setSelectedProduct(null);
    }, []);

    // Handle ESC key to close chat
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'Escape' && isChatOpen) {
                handleCloseChat();
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [isChatOpen, handleCloseChat]);

    // Handle click on overlay background to close
    const handleOverlayClick = useCallback((e) => {
        if (e.target.classList.contains('ai-stylist-overlay')) {
            handleCloseChat();
        }
    }, [handleCloseChat]);

    const handleSendMessage = useCallback(async (content) => {
        // Add user message immediately
        const userMessage = {
            id: Date.now(),
            type: 'user',
            content,
            timestamp: new Date().toISOString(),
        };

        setConversationHistory(prev => [...prev, userMessage]);
        setIsLoading(true);
        setLeftPanelMode(LEFT_PANEL_MODES.KNOWLEDGE_BASE);

        try {
            // Find the most recent assistant message with product data
            const lastAssistantMessage = [...conversationHistory].reverse().find(m => m.type === 'assistant' && m.data && m.data.length > 0);
            const currentlyFetchedItems = lastAssistantMessage ? lastAssistantMessage.data : [];

            // Call the RAG chat API with currently_fetched_items
            const response = await chatAPI.sendMessage(content, currentlyFetchedItems);
            const data = response.data;

            const assistantMessage = {
                id: Date.now() + 1,
                type: 'assistant',
                content: data.answer,
                timestamp: new Date().toISOString(),
                data: data.data, // Include product data if available
                sql_query: data.sql_query, // For debugging
            };

            setConversationHistory(prev => [...prev, assistantMessage]);

            // Check if cart was updated by the agent
            if (data.data && data.data.some(item => item.action === 'cart_updated')) {
                refreshCart();
                // If order was placed, show promotions; otherwise show cart
                const orderPlaced = data.data.some(item => item.action === 'cart_updated' && item.type === 'place_order');
                if (orderPlaced) {
                    setLeftPanelMode(LEFT_PANEL_MODES.CAROUSEL);
                } else {
                    setLeftPanelMode(LEFT_PANEL_MODES.CART);
                }
            }
        } catch (error) {
            console.error('Chat API error:', error);

            let errorContent = "I'm sorry, I encountered an error while processing your request. Please try again.";

            // Check for rate limit error (429)
            if (error.response?.status === 429 || error.response?.data?.detail?.includes('rate limit')) {
                errorContent = "⏳ The AI service is currently busy. Please wait a moment and try again.";
            } else if (error.response?.status === 500) {
                errorContent = "🔧 There was an issue processing your request. The AI might be temporarily unavailable.";
            }

            const errorMessage = {
                id: Date.now() + 1,
                type: 'assistant',
                content: errorContent,
                timestamp: new Date().toISOString(),
            };

            setConversationHistory(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    }, [conversationHistory, isAuthenticated, LEFT_PANEL_MODES.KNOWLEDGE_BASE]);

    // ========== RENDER ==========

    // Don't render anything while checking auth
    if (isCheckingAuth) {
        return null; // Or a spinner if you prefer
    }

    // Handle user trying to open chat
    const handleOpenChatWithAuth = () => {
        if (!isAuthenticated) {
            setIsLoginModalOpen(true);
            return;
        }
        handleOpenChat();
    };

    return (
        <>
            {/* Floating Launcher Button - Always show */}
            <ChatLauncher
                onClick={handleOpenChatWithAuth}
                isVisible={!isChatOpen}
            />

            {/* Login Prompt Modal */}
            {isLoginModalOpen && (
                <div className="ai-stylist-overlay" onClick={(e) => {
                    if (e.target.classList.contains('ai-stylist-overlay')) {
                        setIsLoginModalOpen(false);
                    }
                }}>
                    <div className="login-prompt-modal" style={{
                        background: 'white',
                        padding: '30px',
                        borderRadius: '12px',
                        textAlign: 'center',
                        maxWidth: '400px',
                        width: '90%',
                        boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
                        position: 'relative',
                        margin: 'auto',
                        top: '50%',
                        transform: 'translateY(-50%)'
                    }}>
                        <button
                            onClick={() => setIsLoginModalOpen(false)}
                            style={{
                                position: 'absolute',
                                right: '15px',
                                top: '15px',
                                background: 'none',
                                border: 'none',
                                fontSize: '20px',
                                cursor: 'pointer',
                                color: '#666'
                            }}
                        >
                            ×
                        </button>
                        <div style={{ fontSize: '48px', marginBottom: '15px' }}>🔒</div>
                        <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>Login Required</h3>
                        <p style={{ margin: '0 0 25px 0', color: '#666', lineHeight: '1.5' }}>
                            Please sign in to chat with our AI Stylist and get personalized recommendations.
                        </p>
                        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                            <button
                                onClick={() => {
                                    setIsLoginModalOpen(false);
                                    navigate('/login');
                                }}
                                style={{
                                    background: '#000',
                                    color: 'white',
                                    border: 'none',
                                    padding: '12px 24px',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    fontSize: '16px',
                                    fontWeight: '500'
                                }}
                            >
                                Sign In
                            </button>
                            <button
                                onClick={() => setIsLoginModalOpen(false)}
                                style={{
                                    background: '#f5f5f5',
                                    color: '#333',
                                    border: 'none',
                                    padding: '12px 24px',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    fontSize: '16px',
                                    fontWeight: '500'
                                }}
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Full-screen Overlay with Dual-Pane Layout */}
            {isChatOpen && isAuthenticated && (
                <div className="ai-stylist-overlay" onClick={handleOverlayClick}>
                    <div className="ai-stylist-container">
                        {/* Left Panel - 30% width */}
                        <LeftPanel
                            mode={leftPanelMode}
                            setMode={(m) => {
                                if (typeof m === 'number') {
                                    // If ID is passed from PastOrdersList
                                    setSelectedProduct(m);
                                    setRightPanelMode('ORDER_DETAIL');
                                } else {
                                    setLeftPanelMode(m);
                                }
                            }}
                        />

                        {/* Right Panel - 70% width */}
                        <RightPanel
                            conversationHistory={conversationHistory}
                            onSendMessage={handleSendMessage}
                            onClose={handleCloseChat}
                            isLoading={isLoading}
                            onProductClick={handleProductClickWrapper}
                            viewMode={rightPanelMode}
                            selectedProduct={selectedProduct}
                            onBackToChat={handleBackToChat}
                            onAddToCart={(id) => addToCart(id, 1).then(() => setLeftPanelMode(LEFT_PANEL_MODES.CART))}
                            onViewOrder={(orderId) => {
                                setSelectedProduct(orderId);
                                setRightPanelMode('ORDER_DETAIL');
                            }}
                        />
                    </div>
                </div>
            )}
        </>
    );
};

export default AIStylistChat;
