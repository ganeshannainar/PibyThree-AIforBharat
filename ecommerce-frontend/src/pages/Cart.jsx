import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { ordersAPI } from '../services/api';

const Cart = () => {
  const { cart, loading, updateCartItem, removeFromCart, clearCart, refreshCart } = useCart();
  const [placingOrder, setPlacingOrder] = useState(false);
  const [orderPlaced, setOrderPlaced] = useState(false);
  const [placedOrder, setPlacedOrder] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    refreshCart();
  }, [refreshCart]);

  const handleQuantityChange = async (productId, newQuantity) => {
    await updateCartItem(productId, newQuantity);
  };

  const handleRemoveItem = async (productId) => {
    if (window.confirm('Remove this item from cart?')) {
      await removeFromCart(productId);
    }
  };

  const handleClearCart = async () => {
    if (window.confirm('Clear entire cart?')) {
      await clearCart();
    }
  };

  const handlePlaceOrder = async () => {
    if (!window.confirm('Place this order?')) return;

    setPlacingOrder(true);
    try {
      const response = await ordersAPI.create();
      const order = response.data?.data || response.data;
      await refreshCart();
      setPlacedOrder(order);
      setOrderPlaced(true);
    } catch (error) {
      console.error('Place order error:', error);
      alert(error.response?.data?.detail || 'Failed to place order');
    }
    setPlacingOrder(false);
  };

  if (loading) {
    return <div className="loading">Loading cart...</div>;
  }

  // Order Placed Success Screen
  if (orderPlaced && placedOrder) {
    return (
      <div className="cart-page">
        <div className="order-success-screen">
          <div className="success-icon">✓</div>
          <h1>Your Order Has Been Placed!</h1>
          <p className="success-message">
            Thank you for shopping with us. Your order has been successfully placed.
          </p>
          <div className="order-info-card">
            <div className="order-info-row">
              <span className="label">Order ID:</span>
              <span className="value">#{placedOrder.id}</span>
            </div>
            <div className="order-info-row">
              <span className="label">Total Amount:</span>
              <span className="value">${placedOrder.total_amount?.toFixed(2) || '0.00'}</span>
            </div>
            <div className="order-info-row">
              <span className="label">Status:</span>
              <span className="value status-badge">{placedOrder.status || 'Pending'}</span>
            </div>
          </div>
          <p className="confirmation-note">
            A confirmation email will be sent to you shortly.
          </p>
          <div className="success-actions">
            <button onClick={() => navigate('/orders')} className="btn btn-primary">
              View My Orders
            </button>
            <Link to="/products" className="btn btn-secondary">
              Continue Shopping
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!cart || !cart.cart_items || cart.cart_items.length === 0) {
    return (
      <div className="cart-page">
        <h1>Shopping Cart</h1>
        <div className="cart-empty">
          <p>Your cart is empty</p>
          <Link to="/products" className="btn btn-primary">Continue Shopping</Link>
        </div>
      </div>
    );
  }

  // Calculate totals from cart items (recalculate in frontend to ensure correctness)
  // Use dynamic_price when is_dynamic_pricing_active, otherwise use price
  const getEffectivePrice = (product) => {
    if (product?.is_dynamic_pricing_active && product?.dynamic_price) {
      return product.dynamic_price;
    }
    return product?.price || 0;
  };

  const originalTotal = cart.cart_items.reduce((sum, item) => {
    const price = getEffectivePrice(item.product);
    return sum + (price * item.quantity);
  }, 0);

  // Calculate discounted total properly: price * (1 - discount/100) * quantity
  const discountedTotal = cart.cart_items.reduce((sum, item) => {
    const price = getEffectivePrice(item.product);
    const discount = item.product?.discount_percentage || 0;
    const discountedPrice = price * (1 - discount / 100);
    return sum + (discountedPrice * item.quantity);
  }, 0);

  const totalSavings = originalTotal - discountedTotal;
  const totalAmount = discountedTotal;

  return (
    <div className="cart-page">
      <h1>Shopping Cart</h1>

      <div className="cart-content">
        <div className="cart-items">
          <div className="cart-header">
            <span className="col-product">Product</span>
            <span className="col-price">Price</span>
            <span className="col-discount">Discount</span>
            <span className="col-quantity">Quantity</span>
            <span className="col-subtotal">Subtotal</span>
            <span className="col-action">Action</span>
          </div>

          {cart.cart_items.map(item => {
            const product = item.product || {};
            // Use dynamic price when active, otherwise use base price
            const price = getEffectivePrice(product);
            const discount = product.discount_percentage || 0;
            const discountAmount = price * (discount / 100);
            const itemOriginalTotal = price * item.quantity;
            const itemDiscountSavings = discountAmount * item.quantity;

            return (
              <div key={item.id} className="cart-item">
                <div className="col-product">
                  <img
                    src={product.thumbnail || 'https://via.placeholder.com/80x80?text=No+Image'}
                    alt={product.title || 'Product'}
                    className="cart-item-image"
                    onError={(e) => {
                      if (e.target.src !== 'https://via.placeholder.com/80x80?text=No+Image') {
                        e.target.src = 'https://via.placeholder.com/80x80?text=No+Image';
                      }
                    }}
                  />
                  <div className="cart-item-info">
                    <h4>{product.title || 'Unknown Product'}</h4>
                    <p className="cart-item-brand">{product.brand || ''}</p>
                  </div>
                </div>

                <div className="col-price">
                  <span className="label">Price:</span>
                  <span className="value">${price.toFixed(2)}</span>
                </div>

                <div className="col-discount">
                  <span className="label">Discount:</span>
                  {discount > 0 ? (
                    <div className="discount-info">
                      <span className="discount-badge">{discount}% OFF</span>
                      <span className="discount-amount">-${discountAmount.toFixed(2)}</span>
                    </div>
                  ) : (
                    <span className="no-discount">None</span>
                  )}
                </div>

                <div className="col-quantity">
                  <span className="label">Qty:</span>
                  <div className="quantity-controls">
                    <button
                      onClick={() => handleQuantityChange(item.product_id, item.quantity - 1)}
                      disabled={item.quantity <= 1}
                    >
                      −
                    </button>
                    <span className="qty-value">{item.quantity}</span>
                    <button
                      onClick={() => handleQuantityChange(item.product_id, item.quantity + 1)}
                      disabled={product.stock && item.quantity >= product.stock}
                    >
                      +
                    </button>
                  </div>
                </div>

                <div className="col-subtotal">
                  <span className="label">Subtotal:</span>
                  <span className="value">${(item.subtotal || 0).toFixed(2)}</span>
                </div>

                <div className="col-action">
                  <button
                    onClick={() => handleRemoveItem(item.product_id)}
                    className="btn-remove"
                    title="Remove item"
                  >
                    🗑️ Remove
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        <div className="cart-summary">
          <h3>Order Summary</h3>

          <div className="summary-row">
            <span>Subtotal ({cart.cart_items.length} items):</span>
            <span>${originalTotal.toFixed(2)}</span>
          </div>

          {totalSavings > 0 && (
            <div className="summary-row savings">
              <span>Discount Savings:</span>
              <span className="savings-amount">-${totalSavings.toFixed(2)}</span>
            </div>
          )}

          <div className="summary-row">
            <span>Shipping:</span>
            <span className="free-shipping">FREE</span>
          </div>

          <div className="summary-divider"></div>

          <div className="summary-row total">
            <span>Total:</span>
            <span>${totalAmount.toFixed(2)}</span>
          </div>

          {totalSavings > 0 && (
            <div className="savings-banner">
              🎉 You're saving ${totalSavings.toFixed(2)} on this order!
            </div>
          )}

          <div className="cart-actions">
            <button onClick={handleClearCart} className="btn btn-secondary">
              Clear Cart
            </button>
            <button
              onClick={handlePlaceOrder}
              className="btn btn-success btn-place-order"
              disabled={placingOrder}
            >
              {placingOrder ? 'Placing Order...' : '🛒 Place Order'}
            </button>
          </div>

          <Link to="/products" className="continue-shopping">
            ← Continue Shopping
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Cart;
