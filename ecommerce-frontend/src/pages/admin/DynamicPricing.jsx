import { useState, useEffect, Component } from 'react';
import { dynamicPricingAPI } from '../../services/api';
import './DynamicPricing.css';

// Error Boundary Component
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Dynamic Pricing Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message || 'Unknown error'}</p>
          <button onClick={() => window.location.reload()}>Reload Page</button>
        </div>
      );
    }
    return this.props.children;
  }
}

const DynamicPricingContent = () => {
  const [products, setProducts] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('products'); // 'products' or 'history'
  const [page, setPage] = useState(1);
  const [historyPage, setHistoryPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');

  // Modal states
  const [showPredictModal, setShowPredictModal] = useState(false);
  const [showResultModal, setShowResultModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [predictionResult, setPredictionResult] = useState(null);
  const [predicting, setPredicting] = useState(false);
  const [error, setError] = useState('');

  // Dashboard states
  const [topChanges, setTopChanges] = useState([]);
  const [stats, setStats] = useState(null);
  const [flushing, setFlushing] = useState(false);

  // Form data for prediction
  const [formData, setFormData] = useState({
    product_id: 0,
    category: 'Electronics',
    brand_tier: 'Premium',
    msrp: 0,
    cogs: 0,
    min_margin_req: 0.1,
    inventory_qty: 0,
    weeks_of_cover: 1,
    sell_through_rate: 0.5,
    stock_age_days: 30,
    daily_sales_velocity: 5,
    conversion_rate: 0.05,
    cart_abandon_rate: 0.7,
    competitor_price: 0,
    competitor_price_diff_pct: 0,
    competitor_stock_status: 1,
    market_saturation: 0.5,
    season: 'Fall',
    holiday_event: 0,
    marketing_spend_boost: 0,
  });

  const limit = 10;

  useEffect(() => {
    fetchDashboardData();
    if (activeTab === 'products') {
      fetchProducts();
    } else {
      fetchHistory();
    }
  }, [page, historyPage, activeTab, statusFilter]);

  const fetchDashboardData = async () => {
    try {
      const [topResponse, statsResponse] = await Promise.all([
        dynamicPricingAPI.getTopChanges(3),
        dynamicPricingAPI.getStats()
      ]);
      setTopChanges(topResponse.data.data || []);
      setStats(statsResponse.data.counts || null);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await dynamicPricingAPI.getProducts(page, limit);
      setProducts(response.data.data || []);
    } catch (error) {
      console.error('Error fetching products:', error);
      setError('Failed to fetch products');
    }
    setLoading(false);
  };

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await dynamicPricingAPI.getHistory(historyPage, limit, statusFilter || null);
      setHistory(response.data.data || []);
    } catch (error) {
      console.error('Error fetching history:', error);
      setError('Failed to fetch history');
    }
    setLoading(false);
  };

  const openPredictModal = (product) => {
    setSelectedProduct(product);
    // Map category name to ML category
    const categoryMapping = {
      'Electronics': 'Electronics',
      'Wearables': 'Wearables',
      'Gaming': 'Gaming',
      'Home': 'Home',
      'Fashion': 'Fashion',
      'Beauty': 'Beauty',
    };

    // Map brand to brand tier
    const brandTierMapping = (brand) => {
      const luxuryBrands = ['Apple', 'Sony', 'Bose', 'Samsung'];
      const premiumBrands = ['LG', 'Dell', 'HP', 'Nike', 'Adidas'];
      if (luxuryBrands.some(b => brand?.toLowerCase().includes(b.toLowerCase()))) return 'Luxury';
      if (premiumBrands.some(b => brand?.toLowerCase().includes(b.toLowerCase()))) return 'Premium';
      return 'Budget';
    };

    setFormData({
      product_id: product.id,
      category: categoryMapping[product.category_name] || 'Electronics',
      brand_tier: brandTierMapping(product.brand),
      msrp: product.base_price || product.price,
      cogs: (product.base_price || product.price) * 0.6, // Estimate COGS as 60% of price
      min_margin_req: 0.1,
      inventory_qty: product.stock,
      weeks_of_cover: Math.max(1, product.stock / 50),
      sell_through_rate: 0.5,
      stock_age_days: 30,
      daily_sales_velocity: 5,
      conversion_rate: 0.05,
      cart_abandon_rate: 0.7,
      competitor_price: (product.base_price || product.price) * 0.95,
      competitor_price_diff_pct: 0.05,
      competitor_stock_status: 1,
      market_saturation: 0.5,
      season: getCurrentSeason(),
      holiday_event: 0,
      marketing_spend_boost: 0,
    });
    setError('');
    setShowPredictModal(true);
  };

  const getCurrentSeason = () => {
    const month = new Date().getMonth();
    if (month >= 2 && month <= 4) return 'Spring';
    if (month >= 5 && month <= 7) return 'Summer';
    if (month >= 8 && month <= 10) return 'Fall';
    return 'Winter';
  };

  const handleInputChange = (e) => {
    const { name, value, type } = e.target;
    // Integer fields that expect 0 or 1 (or other integers)
    const integerFields = ['competitor_stock_status', 'holiday_event', 'marketing_spend_boost', 'inventory_qty', 'stock_age_days'];
    // String fields (enums)
    const stringFields = ['category', 'brand_tier', 'season'];

    let parsedValue;
    if (stringFields.includes(name)) {
      // Keep as string for enum fields
      parsedValue = value;
    } else if (integerFields.includes(name)) {
      // Parse as integer
      parsedValue = parseInt(value, 10);
      if (isNaN(parsedValue)) parsedValue = 0;
    } else {
      // Parse as float for numeric fields
      parsedValue = parseFloat(value);
      if (isNaN(parsedValue)) parsedValue = 0;
    }

    setFormData(prev => ({
      ...prev,
      [name]: parsedValue
    }));
  };

  const handlePredict = async () => {
    setPredicting(true);
    setError('');
    try {
      const response = await dynamicPricingAPI.predict(formData);
      setPredictionResult(response.data);
      setShowPredictModal(false);
      setShowResultModal(true);
    } catch (error) {
      console.error('Prediction error:', error);
      const detail = error.response?.data?.detail;
      // Handle validation errors (array) or string errors
      if (Array.isArray(detail)) {
        setError(detail.map(e => `${e.loc?.join('.')}: ${e.msg}`).join(', '));
      } else {
        setError(detail || 'Prediction failed');
      }
    }
    setPredicting(false);
  };

  const handleApprove = async () => {
    try {
      await dynamicPricingAPI.approve(predictionResult.history_id);
      setShowResultModal(false);
      setPredictionResult(null);
      fetchProducts();
      alert('Dynamic pricing approved successfully!');
    } catch (error) {
      console.error('Approve error:', error);
      setError(error.response?.data?.detail || 'Failed to approve');
    }
  };

  const handleReject = async () => {
    try {
      await dynamicPricingAPI.reject(predictionResult.history_id);
      setShowResultModal(false);
      setPredictionResult(null);
      alert('Prediction rejected');
    } catch (error) {
      console.error('Reject error:', error);
      setError(error.response?.data?.detail || 'Failed to reject');
    }
  };

  const handleDeactivate = async (productId) => {
    if (!confirm('Are you sure you want to deactivate dynamic pricing for this product?')) return;
    try {
      await dynamicPricingAPI.deactivate(productId);
      fetchProducts();
      alert('Dynamic pricing deactivated');
    } catch (error) {
      console.error('Deactivate error:', error);
      setError(error.response?.data?.detail || 'Failed to deactivate');
    }
  };

  // Approve a pending history record from the history tab
  const handleApproveFromHistory = async (historyId) => {
    if (!confirm('Approve this prediction and activate dynamic pricing?')) return;
    try {
      await dynamicPricingAPI.approve(historyId);
      fetchHistory();
      alert('Dynamic pricing approved and activated!');
    } catch (error) {
      console.error('Approve error:', error);
      setError(error.response?.data?.detail || 'Failed to approve');
    }
  };

  // Reject a pending history record from the history tab
  const handleRejectFromHistory = async (historyId) => {
    if (!confirm('Reject this prediction?')) return;
    try {
      await dynamicPricingAPI.reject(historyId);
      fetchHistory();
      fetchDashboardData();
      alert('Prediction rejected');
    } catch (error) {
      console.error('Reject error:', error);
      setError(error.response?.data?.detail || 'Failed to reject');
    }
  };

  // Update status for any history record
  const handleUpdateStatus = async (historyId, newStatus) => {
    const confirmMessages = {
      approved: 'Re-approve and activate this prediction?',
      rejected: 'Reject this prediction?',
      pending: 'Reset this prediction to pending?',
      deactivated: 'Deactivate this pricing and revert?'
    };
    if (!confirm(confirmMessages[newStatus] || `Change status to ${newStatus}?`)) return;
    try {
      await dynamicPricingAPI.updateStatus(historyId, newStatus);
      fetchHistory();
      fetchDashboardData();
      alert(`Status updated to ${newStatus}`);
    } catch (error) {
      console.error('Update status error:', error);
      setError(error.response?.data?.detail || 'Failed to update status');
    }
  };

  // Flush history
  const handleFlushHistory = async (filterStatus = null) => {
    const msg = filterStatus
      ? `Delete all ${filterStatus} history records?`
      : 'Delete ALL pricing history records? This cannot be undone!';
    if (!confirm(msg)) return;
    setFlushing(true);
    try {
      const response = await dynamicPricingAPI.flushHistory(filterStatus);
      fetchHistory();
      fetchDashboardData();
      alert(`Deleted ${response.data.deleted_count} records`);
    } catch (error) {
      console.error('Flush error:', error);
      setError(error.response?.data?.detail || 'Failed to flush history');
    }
    setFlushing(false);
  };

  const getStatusBadge = (status) => {
    const colors = {
      pending: '#f59e0b',
      approved: '#10b981',
      rejected: '#ef4444',
    };
    return (
      <span className="status-badge" style={{ backgroundColor: colors[status] || '#6b7280' }}>
        {status}
      </span>
    );
  };

  return (
    <div className="dynamic-pricing-container">
      <div className="page-header">
        <h1>🔮 Dynamic Pricing</h1>
        <p>Use ML-powered price predictions to optimize your product pricing</p>
      </div>

      {/* Dashboard Bar */}
      <div className="dashboard-bar">
        <div className="stats-grid">
          <div className="stat-item">
            <span className="stat-number">{stats?.active_products || 0}</span>
            <span className="stat-label">Active Products</span>
          </div>
          <div className="stat-item pending">
            <span className="stat-number">{stats?.pending || 0}</span>
            <span className="stat-label">Pending</span>
          </div>
          <div className="stat-item approved">
            <span className="stat-number">{stats?.approved || 0}</span>
            <span className="stat-label">Approved</span>
          </div>
          <div className="stat-item rejected">
            <span className="stat-number">{stats?.rejected || 0}</span>
            <span className="stat-label">Rejected</span>
          </div>
        </div>

        {topChanges.length > 0 && (
          <div className="top-changes">
            <h4>🏆 Top Price Changes</h4>
            <div className="top-changes-list">
              {topChanges.map((change, idx) => (
                <div key={change.id} className="top-change-item">
                  <span className="rank">#{idx + 1}</span>
                  <img src={change.product_thumbnail} alt="" className="mini-thumb" />
                  <span className="product-name">{change.product_title?.substring(0, 25)}...</span>
                  <span className="price-change">
                    ${change.original_price?.toFixed(2)} → ${change.predicted_price?.toFixed(2)}
                  </span>
                  <span className={`discount ${change.discount_from_original > 0 ? 'positive' : 'negative'}`}>
                    {change.discount_from_original > 0 ? '-' : '+'}{Math.abs(change.discount_from_original).toFixed(1)}%
                  </span>
                  {change.is_active && <span className="active-badge">Active</span>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'products' ? 'active' : ''}`}
          onClick={() => setActiveTab('products')}
        >
          📦 Products
        </button>
        <button
          className={`tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          📜 Pricing History
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="loading">Loading...</div>
      ) : activeTab === 'products' ? (
        <>
          {/* Products Table */}
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Category</th>
                  <th>Current Price</th>
                  <th>Base Price</th>
                  <th>Dynamic Price</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map(product => (
                  <tr key={product.id}>
                    <td className="product-cell">
                      <img src={product.thumbnail} alt={product.title} className="product-thumb" />
                      <div>
                        <strong>{product.title}</strong>
                        <br />
                        <small>{product.brand}</small>
                      </div>
                    </td>
                    <td>{product.category_name}</td>
                    <td>${product.price}</td>
                    <td>{product.base_price ? `$${product.base_price.toFixed(2)}` : '-'}</td>
                    <td>
                      {product.dynamic_price ? (
                        <span className="dynamic-price">${product.dynamic_price.toFixed(2)}</span>
                      ) : '-'}
                    </td>
                    <td>
                      {product.is_dynamic_pricing_active ? (
                        <span className="status-active">✅ Active</span>
                      ) : (
                        <span className="status-inactive">⏸️ Inactive</span>
                      )}
                      {product.pending_predictions > 0 && (
                        <span className="pending-badge">{product.pending_predictions} pending</span>
                      )}
                    </td>
                    <td className="actions-cell">
                      <button
                        className="btn-predict"
                        onClick={() => openPredictModal(product)}
                      >
                        🔮 Predict
                      </button>
                      {product.is_dynamic_pricing_active && (
                        <button
                          className="btn-deactivate"
                          onClick={() => handleDeactivate(product.id)}
                        >
                          ⏹️ Deactivate
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pagination">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
              Previous
            </button>
            <span>Page {page}</span>
            <button onClick={() => setPage(p => p + 1)} disabled={products.length < limit}>
              Next
            </button>
          </div>
        </>
      ) : (
        <>
          {/* History Filters and Actions */}
          <div className="history-header">
            <div className="history-filters">
              <label>Filter by status:</label>
              <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                <option value="">All</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
            <div className="history-actions">
              <button
                className="btn-flush"
                onClick={() => handleFlushHistory(statusFilter || null)}
                disabled={flushing}
              >
                {flushing ? '⏳ Flushing...' : `🗑️ Flush ${statusFilter || 'All'} History`}
              </button>
            </div>
          </div>

          {/* History Table */}
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Product</th>
                  <th>Original Price</th>
                  <th>Predicted Price</th>
                  <th>Discount</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map(record => (
                  <tr key={record.id}>
                    <td>{new Date(record.created_at).toLocaleString()}</td>
                    <td className="product-cell">
                      {record.product_thumbnail && (
                        <img src={record.product_thumbnail} alt="" className="product-thumb-small" />
                      )}
                      <span>{record.product_title}</span>
                    </td>
                    <td>${record.original_price.toFixed(2)}</td>
                    <td className="predicted-price">${record.predicted_price.toFixed(2)}</td>
                    <td>
                      <span className={record.discount_from_original > 0 ? 'discount-positive' : 'discount-negative'}>
                        {record.discount_from_original > 0 ? '-' : '+'}{Math.abs(record.discount_from_original).toFixed(1)}%
                      </span>
                    </td>
                    <td>{getStatusBadge(record.status)}</td>
                    <td className="actions-cell">
                      {record.status === 'pending' && (
                        <>
                          <button
                            className="btn-approve-small"
                            onClick={() => handleApproveFromHistory(record.id)}
                            title="Approve and activate"
                          >
                            ✅ Approve
                          </button>
                          <button
                            className="btn-reject-small"
                            onClick={() => handleRejectFromHistory(record.id)}
                            title="Reject"
                          >
                            ❌ Reject
                          </button>
                        </>
                      )}
                      {record.status === 'approved' && (
                        <>
                          <button
                            className="btn-deactivate-small"
                            onClick={() => handleUpdateStatus(record.id, 'deactivated')}
                            title="Deactivate and fall back to base price"
                          >
                            ⏹️ Deactivate
                          </button>
                          <button
                            className="btn-reset-small"
                            onClick={() => handleUpdateStatus(record.id, 'pending')}
                            title="Reset to pending"
                          >
                            ↩️ Undo
                          </button>
                        </>
                      )}
                      {record.status === 'rejected' && (
                        <>
                          <button
                            className="btn-approve-small"
                            onClick={() => handleUpdateStatus(record.id, 'approved')}
                            title="Re-approve this prediction"
                          >
                            ✅ Re-approve
                          </button>
                          <button
                            className="btn-reset-small"
                            onClick={() => handleUpdateStatus(record.id, 'pending')}
                            title="Reset to pending"
                          >
                            ↩️ Undo
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pagination">
            <button onClick={() => setHistoryPage(p => Math.max(1, p - 1))} disabled={historyPage === 1}>
              Previous
            </button>
            <span>Page {historyPage}</span>
            <button onClick={() => setHistoryPage(p => p + 1)} disabled={history.length < limit}>
              Next
            </button>
          </div>
        </>
      )}

      {/* Predict Modal */}
      {showPredictModal && selectedProduct && (
        <div className="modal-overlay" onClick={() => setShowPredictModal(false)}>
          <div className="modal predict-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>🔮 Predict Dynamic Price</h2>
              <button className="close-btn" onClick={() => setShowPredictModal(false)}>×</button>
            </div>
            <div className="modal-subheader">
              <img src={selectedProduct.thumbnail} alt="" className="modal-product-img" />
              <div>
                <h3>{selectedProduct.title}</h3>
                <p>Current Price: <strong>${selectedProduct.price}</strong></p>
              </div>
            </div>

            <div className="form-grid">
              <div className="form-section">
                <h4>Product Info</h4>
                <div className="form-row">
                  <label>Category</label>
                  <select name="category" value={formData.category} onChange={handleInputChange}>
                    <option value="Electronics">Electronics</option>
                    <option value="Wearables">Wearables</option>
                    <option value="Gaming">Gaming</option>
                    <option value="Home">Home</option>
                    <option value="Fashion">Fashion</option>
                    <option value="Beauty">Beauty</option>
                  </select>
                </div>
                <div className="form-row">
                  <label>Brand Tier</label>
                  <select name="brand_tier" value={formData.brand_tier} onChange={handleInputChange}>
                    <option value="Budget">Budget</option>
                    <option value="Premium">Premium</option>
                    <option value="Luxury">Luxury</option>
                  </select>
                </div>
                <div className="form-row">
                  <label>MSRP ($)</label>
                  <input type="number" name="msrp" value={formData.msrp} onChange={handleInputChange} step="0.01" />
                </div>
                <div className="form-row">
                  <label>COGS ($)</label>
                  <input type="number" name="cogs" value={formData.cogs} onChange={handleInputChange} step="0.01" />
                </div>
                <div className="form-row">
                  <label>Min Margin Req (0-1)</label>
                  <input type="number" name="min_margin_req" value={formData.min_margin_req} onChange={handleInputChange} step="0.01" min="0" max="1" />
                </div>
              </div>

              <div className="form-section">
                <h4>Inventory</h4>
                <div className="form-row">
                  <label>Inventory Qty</label>
                  <input type="number" name="inventory_qty" value={formData.inventory_qty} onChange={handleInputChange} />
                </div>
                <div className="form-row">
                  <label>Weeks of Cover</label>
                  <input type="number" name="weeks_of_cover" value={formData.weeks_of_cover} onChange={handleInputChange} step="0.1" />
                </div>
                <div className="form-row">
                  <label>Sell-through Rate (0-1)</label>
                  <input type="number" name="sell_through_rate" value={formData.sell_through_rate} onChange={handleInputChange} step="0.01" min="0" max="1" />
                </div>
                <div className="form-row">
                  <label>Stock Age (days)</label>
                  <input type="number" name="stock_age_days" value={formData.stock_age_days} onChange={handleInputChange} />
                </div>
                <div className="form-row">
                  <label>Daily Sales Velocity</label>
                  <input type="number" name="daily_sales_velocity" value={formData.daily_sales_velocity} onChange={handleInputChange} step="0.1" />
                </div>
              </div>

              <div className="form-section">
                <h4>Customer Behavior</h4>
                <div className="form-row">
                  <label>Conversion Rate (0-1)</label>
                  <input type="number" name="conversion_rate" value={formData.conversion_rate} onChange={handleInputChange} step="0.01" min="0" max="1" />
                </div>
                <div className="form-row">
                  <label>Cart Abandon Rate (0-1)</label>
                  <input type="number" name="cart_abandon_rate" value={formData.cart_abandon_rate} onChange={handleInputChange} step="0.01" min="0" max="1" />
                </div>
              </div>

              <div className="form-section">
                <h4>Competition</h4>
                <div className="form-row">
                  <label>Competitor Price ($)</label>
                  <input type="number" name="competitor_price" value={formData.competitor_price} onChange={handleInputChange} step="0.01" />
                </div>
                <div className="form-row">
                  <label>Price Diff %</label>
                  <input type="number" name="competitor_price_diff_pct" value={formData.competitor_price_diff_pct} onChange={handleInputChange} step="0.01" />
                </div>
                <div className="form-row">
                  <label>Competitor In Stock</label>
                  <select name="competitor_stock_status" value={formData.competitor_stock_status} onChange={handleInputChange}>
                    <option value={1}>Yes</option>
                    <option value={0}>No</option>
                  </select>
                </div>
                <div className="form-row">
                  <label>Market Saturation (0-1)</label>
                  <input type="number" name="market_saturation" value={formData.market_saturation} onChange={handleInputChange} step="0.01" min="0" max="1" />
                </div>
              </div>

              <div className="form-section">
                <h4>Market Conditions</h4>
                <div className="form-row">
                  <label>Season</label>
                  <select name="season" value={formData.season} onChange={handleInputChange}>
                    <option value="Spring">Spring</option>
                    <option value="Summer">Summer</option>
                    <option value="Fall">Fall</option>
                    <option value="Winter">Winter</option>
                  </select>
                </div>
                <div className="form-row">
                  <label>Holiday Event</label>
                  <select name="holiday_event" value={formData.holiday_event} onChange={handleInputChange}>
                    <option value={0}>No</option>
                    <option value={1}>Yes</option>
                  </select>
                </div>
                <div className="form-row">
                  <label>Marketing Boost</label>
                  <select name="marketing_spend_boost" value={formData.marketing_spend_boost} onChange={handleInputChange}>
                    <option value={0}>No</option>
                    <option value={1}>Yes</option>
                  </select>
                </div>
              </div>
            </div>

            {error && <div className="modal-error">{error}</div>}

            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowPredictModal(false)}>Cancel</button>
              <button className="btn-predict-submit" onClick={handlePredict} disabled={predicting}>
                {predicting ? '⏳ Predicting...' : '🔮 Predict Price'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Result Modal */}
      {showResultModal && predictionResult && (
        <div className="modal-overlay" onClick={() => setShowResultModal(false)}>
          <div className="modal result-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📊 Prediction Result</h2>
              <button className="close-btn" onClick={() => setShowResultModal(false)}>×</button>
            </div>

            <div className="result-content">
              <h3>{predictionResult.product_title || 'Product'}</h3>

              <div className="price-comparison">
                <div className="price-box original">
                  <span className="price-label">Original Price</span>
                  <span className="price-value">${(predictionResult.original_price || 0).toFixed(2)}</span>
                </div>
                <div className="price-arrow">→</div>
                <div className="price-box predicted">
                  <span className="price-label">Predicted Price</span>
                  <span className="price-value">${(predictionResult.predicted_price || 0).toFixed(2)}</span>
                </div>
              </div>

              <div className="savings-banner">
                {(predictionResult.savings_amount || 0) > 0 ? (
                  <>
                    <span className="savings-icon">💰</span>
                    <span>Customer Savings: <strong>${(predictionResult.savings_amount || 0).toFixed(2)}</strong> ({(predictionResult.discount_percentage || 0).toFixed(1)}% off)</span>
                  </>
                ) : (
                  <>
                    <span className="savings-icon">📈</span>
                    <span>Price Increase: <strong>${Math.abs(predictionResult.savings_amount || 0).toFixed(2)}</strong></span>
                  </>
                )}
              </div>

              {predictionResult.pricing_analysis && (
                <div className="analysis-grid">
                  <div className="analysis-item">
                    <span className="analysis-label">Margin</span>
                    <span className="analysis-value">${(predictionResult.pricing_analysis.margin || 0).toFixed(2)}</span>
                  </div>
                  <div className="analysis-item">
                    <span className="analysis-label">Margin %</span>
                    <span className="analysis-value">{(predictionResult.pricing_analysis.margin_percentage || 0).toFixed(1)}%</span>
                  </div>
                  <div className="analysis-item">
                    <span className="analysis-label">Discount from MSRP</span>
                    <span className="analysis-value">{(predictionResult.pricing_analysis.discount_from_msrp_pct || 0).toFixed(1)}%</span>
                  </div>
                  <div className="analysis-item">
                    <span className="analysis-label">Meets Min Margin</span>
                    <span className={`analysis-value ${predictionResult.pricing_analysis.meets_min_margin ? 'text-green' : 'text-red'}`}>
                      {predictionResult.pricing_analysis.meets_min_margin ? '✅ Yes' : '❌ No'}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {error && <div className="modal-error">{error}</div>}

            <div className="modal-actions">
              <button className="btn-reject" onClick={handleReject}>
                ❌ Reject
              </button>
              <button className="btn-approve" onClick={handleApprove}>
                ✅ Approve & Apply
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Wrapper component with error boundary
const DynamicPricing = () => (
  <ErrorBoundary>
    <DynamicPricingContent />
  </ErrorBoundary>
);

export default DynamicPricing;
