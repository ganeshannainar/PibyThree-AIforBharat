import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ordersAPI } from '../services/api';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedOrder, setExpandedOrder] = useState(null);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await ordersAPI.getAll(1, 50);
      setOrders(response.data.data || []);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
    setLoading(false);
  };

  const handleCancelOrder = async (orderId) => {
    if (!window.confirm('Are you sure you want to cancel this order?')) return;
    
    try {
      await ordersAPI.cancel(orderId);
      fetchOrders();
      alert('Order cancelled successfully');
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to cancel order');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: '#f39c12',
      confirmed: '#3498db',
      shipped: '#9b59b6',
      delivered: '#27ae60',
      cancelled: '#e74c3c'
    };
    return colors[status] || '#7f8c8d';
  };

  if (loading) {
    return <div className="loading">Loading orders...</div>;
  }

  return (
    <div className="orders-page">
      <h1>My Orders</h1>
      
      {orders.length === 0 ? (
        <div className="cart-empty">
          <p>You haven't placed any orders yet</p>
          <Link to="/products">Start Shopping</Link>
        </div>
      ) : (
        <div className="orders-list">
          {orders.map(order => (
            <div key={order.id} className="order-card">
              <div className="order-header" onClick={() => setExpandedOrder(expandedOrder === order.id ? null : order.id)}>
                <div className="order-info">
                  <h3>Order #{order.id}</h3>
                  <p className="order-date">
                    {new Date(order.created_at).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
                <div className="order-meta">
                  <span 
                    className="order-status"
                    style={{ backgroundColor: getStatusColor(order.status) }}
                  >
                    {order.status.toUpperCase()}
                  </span>
                  <span className="order-total">${order.total_amount.toFixed(2)}</span>
                </div>
                <span className="expand-icon">{expandedOrder === order.id ? '▼' : '▶'}</span>
              </div>
              
              {expandedOrder === order.id && (
                <div className="order-details">
                  <h4>Order Items</h4>
                  <table className="order-items-table">
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>Price</th>
                        <th>Discount</th>
                        <th>Quantity</th>
                        <th>Subtotal</th>
                      </tr>
                    </thead>
                    <tbody>
                      {order.order_items.map(item => {
                        // Calculate effective price from subtotal for accuracy
                        const effectiveUnitPrice = item.quantity > 0 
                          ? item.subtotal / item.quantity 
                          : item.product_price;
                        const totalDiscount = (item.discount_amount || 0) * item.quantity;
                        
                        return (
                          <tr key={item.id}>
                            <td>{item.product_title}</td>
                            <td>${effectiveUnitPrice.toFixed(2)}</td>
                            <td>
                              {item.discount_percentage > 0 ? (
                                <div className="order-discount-info">
                                  <span className="discount-badge">{item.discount_percentage}% OFF</span>
                                  <span className="discount-savings">-${totalDiscount.toFixed(2)}</span>
                                </div>
                              ) : (
                                <span className="no-discount">—</span>
                              )}
                            </td>
                            <td>{item.quantity}</td>
                            <td>${item.subtotal.toFixed(2)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                    <tfoot>
                      {(() => {
                        const originalTotal = order.order_items.reduce((sum, item) => 
                          sum + (item.product_price * item.quantity), 0);
                        const totalSavings = originalTotal - order.total_amount;
                        return (
                          <>
                            {totalSavings > 0 && (
                              <tr className="savings-row">
                                <td colSpan="4">Discount Savings</td>
                                <td className="savings-amount">-${totalSavings.toFixed(2)}</td>
                              </tr>
                            )}
                            <tr className="total-row">
                              <td colSpan="4"><strong>Total</strong></td>
                              <td><strong>${order.total_amount.toFixed(2)}</strong></td>
                            </tr>
                          </>
                        );
                      })()}
                    </tfoot>
                  </table>
                  
                  {(order.status === 'pending' || order.status === 'confirmed') && (
                    <div className="order-actions">
                      <button 
                        onClick={() => handleCancelOrder(order.id)}
                        className="btn btn-danger"
                      >
                        Cancel Order
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Orders;
