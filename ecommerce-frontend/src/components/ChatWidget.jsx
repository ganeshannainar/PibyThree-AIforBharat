import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { chatAPI } from '../services/api';

const PLACEHOLDER_IMAGE = 'https://via.placeholder.com/300x200?text=No+Image';

const ChatWidget = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        if (isOpen && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isOpen]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!inputValue.trim() || isLoading) return;

        const userMessage = inputValue.trim();
        setInputValue('');

        // Add user message
        setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
        setIsLoading(true);

        try {
            const response = await chatAPI.sendMessage(userMessage);
            const { answer, data, sql_query } = response.data;

            // Add bot response with products
            setMessages(prev => [...prev, {
                type: 'bot',
                content: answer,
                products: data || [],
                sqlQuery: sql_query
            }]);
        } catch (error) {
            console.error('Chat error:', error);
            setMessages(prev => [...prev, {
                type: 'bot',
                content: 'Sorry, I encountered an error. Please try again.',
                products: []
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const getDisplayPrice = (product) => {
        if (product.is_dynamic_pricing_active && product.dynamic_price) {
            return product.dynamic_price;
        }
        return product.price * (1 - (product.discount_percentage || 0) / 100);
    };

    const renderProductCard = (product) => {
        const displayPrice = getDisplayPrice(product);
        const hasDiscount = product.is_dynamic_pricing_active
            ? (product.dynamic_price && product.base_price && product.dynamic_price < product.base_price)
            : (product.discount_percentage > 0);

        return (
            <div key={product.id} className="chat-product-card">
                <img
                    src={product.thumbnail || PLACEHOLDER_IMAGE}
                    alt={product.title}
                    className="chat-product-image"
                    onError={(e) => { e.target.src = PLACEHOLDER_IMAGE; }}
                />
                <div className="chat-product-info">
                    <h4>{product.title}</h4>
                    <p className="chat-product-brand">{product.brand}</p>
                    <div className="chat-product-price">
                        {hasDiscount && product.base_price && (
                            <span className="chat-product-original-price">${(product.base_price || product.price).toFixed(2)}</span>
                        )}
                        <span className="chat-product-current-price">${displayPrice.toFixed(2)}</span>
                    </div>
                    <div className="chat-product-meta">
                        <span className="chat-product-rating">⭐ {(product.rating || 0).toFixed(1)}</span>
                        <span className={`chat-product-stock ${product.stock === 0 ? 'out-of-stock' : ''}`}>
                            {product.stock > 0 ? `${product.stock} in stock` : 'Out of stock'}
                        </span>
                    </div>
                    <Link to={`/products/${product.id}`} className="chat-product-link">
                        View Details →
                    </Link>
                </div>
            </div>
        );
    };

    return (
        <>
            {/* Floating Chat Button */}
            <button
                className={`chat-fab ${isOpen ? 'hidden' : ''}`}
                onClick={() => setIsOpen(true)}
                aria-label="Open chat"
            >
                <svg viewBox="0 0 24 24" fill="currentColor" width="28" height="28">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z" />
                </svg>
            </button>

            {/* Chat Window */}
            {isOpen && (
                <div className="chat-window">
                    <div className="chat-header">
                        <div className="chat-header-info">
                            <div className="chat-avatar">
                                <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
                                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" />
                                </svg>
                            </div>
                            <div>
                                <h3>Shopping Assistant</h3>
                                <p>Ask me about products</p>
                            </div>
                        </div>
                        <button
                            className="chat-close-btn"
                            onClick={() => setIsOpen(false)}
                            aria-label="Close chat"
                        >
                            <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
                                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
                            </svg>
                        </button>
                    </div>

                    <div className="chat-messages">
                        {messages.length === 0 && (
                            <div className="chat-welcome">
                                <div className="chat-welcome-icon">🛒</div>
                                <h4>Welcome!</h4>
                                <p>How can I help you find products today?</p>
                                <div className="chat-suggestions">
                                    <button onClick={() => setInputValue('Show me all products')}>
                                        Show me all products
                                    </button>
                                    <button onClick={() => setInputValue('What are the top rated products?')}>
                                        Top rated products
                                    </button>
                                    <button onClick={() => setInputValue('Find products under $50')}>
                                        Products under $50
                                    </button>
                                </div>
                            </div>
                        )}

                        {messages.map((message, index) => (
                            <div key={index} className={`chat-message ${message.type}`}>
                                {message.type === 'bot' && (
                                    <div className="chat-message-avatar">
                                        <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" />
                                        </svg>
                                    </div>
                                )}
                                <div className="chat-message-content">
                                    <p>{message.content}</p>
                                    {message.products && message.products.length > 0 && (
                                        <div className="chat-products-grid">
                                            {message.products.slice(0, 6).map(renderProductCard)}
                                            {message.products.length > 6 && (
                                                <div className="chat-more-products">
                                                    +{message.products.length - 6} more products found
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}

                        {isLoading && (
                            <div className="chat-message bot">
                                <div className="chat-message-avatar">
                                    <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" />
                                    </svg>
                                </div>
                                <div className="chat-message-content">
                                    <div className="chat-typing-indicator">
                                        <span></span>
                                        <span></span>
                                        <span></span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    <form className="chat-input-container" onSubmit={handleSubmit}>
                        <input
                            ref={inputRef}
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder="Ask about products..."
                            disabled={isLoading}
                            className="chat-input"
                        />
                        <button
                            type="submit"
                            disabled={!inputValue.trim() || isLoading}
                            className="chat-send-btn"
                            aria-label="Send message"
                        >
                            <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
                                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                            </svg>
                        </button>
                    </form>
                </div>
            )}
        </>
    );
};

export default ChatWidget;
