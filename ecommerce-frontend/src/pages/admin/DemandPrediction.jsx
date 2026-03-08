import { useState, useEffect, Component } from 'react';
import { demandPredictionAPI } from '../../services/api';
import './DemandPrediction.css';

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
    console.error('Demand Prediction Error:', error, errorInfo);
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

// Stock Market Ticker Component
const StockTicker = ({ trendingProducts, loading }) => {

  if (loading) {
    return (
      <div className="stock-ticker-container loading">
        <div className="ticker-skeleton">
          <div className="skeleton-pulse"></div>
          Loading market data...
        </div>
      </div>
    );
  }

  if (trendingProducts.length === 0) {
    return (
      <div className="stock-ticker-container empty">
        <div className="empty-state">
          <span className="empty-icon">📊</span>
          <p>No demand data yet. Run predictions to see market trends!</p>
        </div>
      </div>
    );
  }

  const getDemandColor = (level) => {
    switch (level) {
      case 'very_high': return '#ef4444';
      case 'high': return '#f97316';
      case 'medium': return '#eab308';
      case 'low': return '#22c55e';
      default: return '#6b7280';
    }
  };

  const getDemandBgColor = (level) => {
    switch (level) {
      case 'very_high': return 'rgba(239, 68, 68, 0.15)';
      case 'high': return 'rgba(249, 115, 22, 0.15)';
      case 'medium': return 'rgba(234, 179, 8, 0.15)';
      case 'low': return 'rgba(34, 197, 94, 0.15)';
      default: return 'rgba(107, 114, 128, 0.15)';
    }
  };

  const getArrowIcon = (direction, changePct) => {
    if (direction === 'up' || (changePct && changePct > 0)) {
      return '▲';
    } else if (direction === 'down' || (changePct && changePct < 0)) {
      return '▼';
    }
    return '▬';
  };

  const getArrowClass = (direction, changePct) => {
    if (direction === 'up' || (changePct && changePct > 0)) {
      return 'arrow-up';
    } else if (direction === 'down' || (changePct && changePct < 0)) {
      return 'arrow-down';
    }
    return 'arrow-neutral';
  };

  // Double the products for seamless loop
  const tickerItems = [...trendingProducts, ...trendingProducts];

  return (
    <div className="stock-ticker-container">
      <div className="ticker-header">
        <div className="ticker-title">
          <span className="market-icon">📈</span>
          <h2>Demand Market</h2>
        </div>
        <div className="live-badge">
          <span className="live-dot"></span>
          LIVE
        </div>
      </div>

      <div className="ticker-wrapper">
        <div className="ticker-track">
          {tickerItems.map((product, index) => (
            <div
              key={`${product.id}-${index}`}
              className="ticker-item"
              style={{
                '--demand-color': getDemandColor(product.demand_level),
                '--demand-bg': getDemandBgColor(product.demand_level)
              }}
            >
              <div className="ticker-number">
                #{(index % trendingProducts.length) + 1}
              </div>
              <div className="ticker-product">
                <img
                  src={product.product_thumbnail}
                  alt={product.product_title}
                  className="ticker-thumb"
                />
                <div className="ticker-info">
                  <span className="ticker-name">{product.product_title}</span>
                  <span className="ticker-brand">{product.brand}</span>
                </div>
              </div>

              <div className="ticker-stats">
                <div className="ticker-stat stock-stat">
                  <span className="stat-label">STOCK</span>
                  <span className="stat-value">{product.product_stock}</span>
                </div>

                <div className="ticker-stat forecast-stat">
                  <span className="stat-label">FORECAST</span>
                  <div className="forecast-value-container">
                    <span
                      className={`arrow-indicator ${getArrowClass(product.trend_direction, product.demand_change_pct)}`}
                    >
                      {getArrowIcon(product.trend_direction, product.demand_change_pct)}
                    </span>
                    <span className="stat-value" style={{ color: getDemandColor(product.demand_level) }}>
                      {Math.round(product.adjusted_forecast)}
                    </span>
                  </div>
                </div>

                <div className="ticker-stat change-stat">
                  <span className="stat-label">CHANGE</span>
                  <span
                    className={`stat-value change-value ${product.demand_change_pct > 0 ? 'positive' : product.demand_change_pct < 0 ? 'negative' : 'neutral'}`}
                  >
                    {product.demand_change_pct ?
                      `${product.demand_change_pct > 0 ? '+' : ''}${product.demand_change_pct.toFixed(1)}%`
                      : '—'}
                  </span>
                </div>

                <div
                  className="demand-level-tag"
                  style={{
                    backgroundColor: getDemandBgColor(product.demand_level),
                    color: getDemandColor(product.demand_level),
                    borderColor: getDemandColor(product.demand_level)
                  }}
                >
                  {product.demand_level.replace('_', ' ').toUpperCase()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="ticker-footer">
        <div className="ticker-legend">
          <div className="legend-item">
            <span className="legend-dot" style={{ background: '#22c55e' }}></span>
            <span>Low</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ background: '#eab308' }}></span>
            <span>Medium</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ background: '#f97316' }}></span>
            <span>High</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ background: '#ef4444' }}></span>
            <span>Very High</span>
          </div>
        </div>
        <div className="market-time">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

const DemandPredictionContent = () => {
  const [products, setProducts] = useState([]);
  const [history, setHistory] = useState([]);
  const [trendingProducts, setTrendingProducts] = useState([]);
  const [demandStats, setDemandStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [trendingLoading, setTrendingLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('products');
  const [page, setPage] = useState(1);
  const [historyPage, setHistoryPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [demandLevelFilter, setDemandLevelFilter] = useState('');
  const [productDemandFilter, setProductDemandFilter] = useState('');

  // Modal states
  const [showPredictModal, setShowPredictModal] = useState(false);
  const [showBulkPredictModal, setShowBulkPredictModal] = useState(false);
  const [showResultModal, setShowResultModal] = useState(false);
  const [showBulkResultModal, setShowBulkResultModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [predictionResult, setPredictionResult] = useState(null);
  const [bulkPredictionResult, setBulkPredictionResult] = useState(null);
  const [predicting, setPredicting] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [error, setError] = useState('');

  // Form data for prediction
  const [formData, setFormData] = useState({
    product_id: 0,
    holiday: 'No Holiday',
    weather: 'Overcast',
  });

  // Bulk form data
  const [bulkFormData, setBulkFormData] = useState({
    holiday: 'No Holiday',
    weather: 'Overcast',
  });

  const limit = 10;

  useEffect(() => {
    fetchTrendingProducts();
    fetchDemandStats();
  }, []);

  useEffect(() => {
    if (activeTab === 'products') {
      fetchProducts();
    } else {
      fetchHistory();
    }
  }, [page, historyPage, activeTab, statusFilter, demandLevelFilter, productDemandFilter]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await demandPredictionAPI.getProducts(page, limit, productDemandFilter || null);
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
      const response = await demandPredictionAPI.getHistory(
        historyPage,
        limit,
        statusFilter || null,
        demandLevelFilter || null
      );
      setHistory(response.data.data || []);
    } catch (error) {
      console.error('Error fetching history:', error);
      setError('Failed to fetch history');
    }
    setLoading(false);
  };

  const fetchTrendingProducts = async () => {
    setTrendingLoading(true);
    try {
      const response = await demandPredictionAPI.getTrending(10);
      setTrendingProducts(response.data.data || []);
    } catch (error) {
      console.error('Error fetching trending products:', error);
    }
    setTrendingLoading(false);
  };

  const fetchDemandStats = async () => {
    setStatsLoading(true);
    try {
      const response = await demandPredictionAPI.getStats();
      setDemandStats(response.data);
    } catch (error) {
      console.error('Error fetching demand stats:', error);
    }
    setStatsLoading(false);
  };

  const openPredictModal = (product) => {
    setSelectedProduct(product);
    setFormData({
      product_id: product.id,
      holiday: 'No Holiday',
      weather: 'Overcast',
    });
    setError('');
    setShowPredictModal(true);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handlePredict = async () => {
    setPredicting(true);
    setError('');
    try {
      const response = await demandPredictionAPI.predict(formData);
      setPredictionResult(response.data);
      setShowPredictModal(false);
      setShowResultModal(true);
      // Refresh trending products
      fetchTrendingProducts();
    } catch (error) {
      console.error('Prediction error:', error);
      const detail = error.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map(e => `${e.loc?.join('.')}: ${e.msg}`).join(', '));
      } else {
        setError(detail || 'Prediction failed');
      }
    }
    setPredicting(false);
  };

  const handleAcknowledge = async () => {
    try {
      await demandPredictionAPI.acknowledge(predictionResult.history_id);
      setShowResultModal(false);
      setPredictionResult(null);
      fetchProducts();
      fetchTrendingProducts();
      fetchDemandStats();
    } catch (error) {
      console.error('Acknowledge error:', error);
      setError(error.response?.data?.detail || 'Failed to acknowledge');
    }
  };

  const handleBulkPredict = async () => {
    setPredicting(true);
    setError('');
    try {
      const response = await demandPredictionAPI.predictBulk({
        holiday: bulkFormData.holiday,
        weather: bulkFormData.weather,
        product_ids: null // null means predict for all products
      });
      setBulkPredictionResult(response.data);
      setShowBulkPredictModal(false);
      setShowBulkResultModal(true);
      // Refresh data
      fetchTrendingProducts();
      fetchDemandStats();
      fetchProducts();
    } catch (error) {
      console.error('Bulk prediction error:', error);
      const detail = error.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map(e => `${e.loc?.join('.')}: ${e.msg}`).join(', '));
      } else {
        setError(detail || 'Bulk prediction failed');
      }
    }
    setPredicting(false);
  };

  const handleDeletePrediction = async (historyId, productId) => {
    if (!window.confirm('Are you sure you want to delete this prediction?')) {
      return;
    }
    setDeleting(historyId);
    try {
      await demandPredictionAPI.delete(historyId);
      // Refresh relevant data
      if (activeTab === 'products') {
        fetchProducts();
      } else {
        fetchHistory();
      }
      fetchTrendingProducts();
      fetchDemandStats();
    } catch (error) {
      console.error('Delete error:', error);
      setError(error.response?.data?.detail || 'Failed to delete prediction');
    }
    setDeleting(null);
  };

  const getDemandBadge = (level) => {
    const colors = {
      very_high: '#ef4444',
      high: '#f97316',
      medium: '#eab308',
      low: '#22c55e',
    };
    return (
      <span className="demand-level-badge" style={{ backgroundColor: colors[level] || '#6b7280' }}>
        {level?.replace('_', ' ')}
      </span>
    );
  };

  const getStatusBadge = (status) => {
    const colors = {
      pending: '#f59e0b',
      acknowledged: '#10b981',
    };
    return (
      <span className="status-badge" style={{ backgroundColor: colors[status] || '#6b7280' }}>
        {status}
      </span>
    );
  };

  return (
    <div className="demand-prediction-container">
      <div className="page-header">
        <div className="header-left">
          <h1>📊 Demand Prediction</h1>
          <p>AI-powered demand forecasting to optimize inventory and pricing</p>
        </div>
        <button
          className="btn-bulk-predict"
          onClick={() => setShowBulkPredictModal(true)}
        >
          🚀 Predict All Products
        </button>
      </div>

      {/* Dashboard Stats Bar */}
      <div className="demand-dashboard">
        <div className="dashboard-stats">
          <div className="stat-card low">
            <div className="stat-icon">📉</div>
            <div className="stat-content">
              <span className="stat-count">{demandStats?.counts?.low || 0}</span>
              <span className="stat-label">Low Demand</span>
            </div>
          </div>
          <div className="stat-card medium">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <span className="stat-count">{demandStats?.counts?.medium || 0}</span>
              <span className="stat-label">Medium Demand</span>
            </div>
          </div>
          <div className="stat-card high">
            <div className="stat-icon">📈</div>
            <div className="stat-content">
              <span className="stat-count">{demandStats?.counts?.high || 0}</span>
              <span className="stat-label">High Demand</span>
            </div>
          </div>
          <div className="stat-card very-high">
            <div className="stat-icon">🔥</div>
            <div className="stat-content">
              <span className="stat-count">{demandStats?.counts?.very_high || 0}</span>
              <span className="stat-label">Very High</span>
            </div>
          </div>
        </div>

        {demandStats?.top3 && demandStats.top3.length > 0 && (
          <div className="top-products">
            <h3>🏆 Top 3 In-Demand Products</h3>
            <div className="top-products-list">
              {demandStats.top3.map((product, index) => (
                <div key={product.product_id} className="top-product-item">
                  <span className="rank-badge">#{index + 1}</span>
                  <img src={product.product_thumbnail} alt={product.product_title} className="top-product-thumb" />
                  <div className="top-product-info">
                    <span className="top-product-name">{product.product_title}</span>
                    <span className="top-product-forecast">
                      Forecast: {Math.round(product.adjusted_forecast)} units
                      {product.demand_change_pct && (
                        <span className={`change-indicator ${product.demand_change_pct > 0 ? 'positive' : 'negative'}`}>
                          {product.demand_change_pct > 0 ? '↑' : '↓'} {Math.abs(product.demand_change_pct).toFixed(1)}%
                        </span>
                      )}
                    </span>
                  </div>
                  {getDemandBadge(product.demand_level)}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Stock Market Ticker */}
      <StockTicker
        trendingProducts={trendingProducts}
        loading={trendingLoading}
      />

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
          📜 Prediction History
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="loading">Loading...</div>
      ) : activeTab === 'products' ? (
        <>
          {/* Products Filter */}
          <div className="filter-bar">
            <select
              value={productDemandFilter}
              onChange={(e) => setProductDemandFilter(e.target.value)}
            >
              <option value="">All Demand Levels</option>
              <option value="very_high">Very High</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Products Table */}
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Category</th>
                  <th>Price</th>
                  <th>Stock</th>
                  <th>Latest Forecast</th>
                  <th>Demand Level</th>
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
                    <td>
                      <span className={`stock-badge ${product.stock < 20 ? 'low' : ''}`}>
                        {product.stock}
                      </span>
                    </td>
                    <td>
                      {product.latest_forecast ? (
                        <span className="forecast-value">{Math.round(product.latest_forecast)} units/week</span>
                      ) : '-'}
                    </td>
                    <td>
                      {product.latest_demand_level ? getDemandBadge(product.latest_demand_level) : '-'}
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
                      {product.latest_history_id && (
                        <button
                          className="btn-delete"
                          onClick={() => handleDeletePrediction(product.latest_history_id, product.id)}
                          disabled={deleting === product.latest_history_id}
                          title="Delete latest prediction"
                        >
                          {deleting === product.latest_history_id ? '...' : '🗑️'}
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
              ← Previous
            </button>
            <span>Page {page}</span>
            <button onClick={() => setPage(p => p + 1)} disabled={products.length < limit}>
              Next →
            </button>
          </div>
        </>
      ) : (
        <>
          {/* Filter */}
          <div className="filter-bar">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="acknowledged">Acknowledged</option>
            </select>
            <select
              value={demandLevelFilter}
              onChange={(e) => setDemandLevelFilter(e.target.value)}
            >
              <option value="">All Demand Levels</option>
              <option value="very_high">Very High</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* History Table */}
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Conditions</th>
                  <th>Base Forecast</th>
                  <th>Adjusted Forecast</th>
                  <th>Demand Level</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map(record => (
                  <tr key={record.id}>
                    <td className="product-cell">
                      <img src={record.product_thumbnail} alt={record.product_title} className="product-thumb-small" />
                      <span>{record.product_title}</span>
                    </td>
                    <td>
                      <small>
                        🎄 {record.holiday_input}<br />
                        🌤️ {record.weather_input}
                      </small>
                    </td>
                    <td>{Math.round(record.base_forecast)} units</td>
                    <td>
                      <strong>{Math.round(record.adjusted_forecast)} units</strong>
                      {record.demand_change_pct && (
                        <span className={`change-badge ${record.demand_change_pct > 0 ? 'positive' : 'negative'}`}>
                          {record.demand_change_pct > 0 ? '+' : ''}{record.demand_change_pct.toFixed(1)}%
                        </span>
                      )}
                    </td>
                    <td>{getDemandBadge(record.demand_level)}</td>
                    <td>{getStatusBadge(record.status)}</td>
                    <td>{new Date(record.created_at).toLocaleDateString()}</td>
                    <td className="actions-cell">
                      {record.status === 'pending' && (
                        <button
                          className="btn-acknowledge-small"
                          onClick={() => handleAcknowledge(record.id, record.product_id)}
                          title="Acknowledge this prediction"
                        >
                          ✅ Acknowledge
                        </button>
                      )}
                      <button
                        className="btn-delete-small"
                        onClick={() => handleDeletePrediction(record.id, record.product_id)}
                        disabled={deleting === record.id}
                        title="Delete prediction"
                      >
                        {deleting === record.id ? '...' : '🗑️'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pagination">
            <button onClick={() => setHistoryPage(p => Math.max(1, p - 1))} disabled={historyPage === 1}>
              ← Previous
            </button>
            <span>Page {historyPage}</span>
            <button onClick={() => setHistoryPage(p => p + 1)} disabled={history.length < limit}>
              Next →
            </button>
          </div>
        </>
      )}

      {/* Predict Modal */}
      {showPredictModal && (
        <div className="modal-overlay" onClick={() => setShowPredictModal(false)}>
          <div className="modal-content predict-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>🔮 Predict Demand</h2>
              <button className="close-btn" onClick={() => setShowPredictModal(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="product-preview">
                <img src={selectedProduct?.thumbnail} alt={selectedProduct?.title} />
                <div>
                  <h3>{selectedProduct?.title}</h3>
                  <p>Stock: {selectedProduct?.stock} | Price: ${selectedProduct?.price}</p>
                </div>
              </div>

              {error && <div className="error-message">{error}</div>}

              <div className="form-grid">
                <div className="form-group">
                  <label>🎄 Holiday Condition</label>
                  <select name="holiday" value={formData.holiday} onChange={handleInputChange}>
                    <option value="No Holiday">No Holiday</option>
                    <option value="Christmas">Christmas</option>
                    <option value="New Year">New Year</option>
                    <option value="Black Friday">Black Friday</option>
                    <option value="Cyber Monday">Cyber Monday</option>
                    <option value="Valentine's Day">Valentine's Day</option>
                    <option value="Mother's Day">Mother's Day</option>
                    <option value="Father's Day">Father's Day</option>
                    <option value="Easter">Easter</option>
                    <option value="Thanksgiving">Thanksgiving</option>
                    <option value="Independence Day">Independence Day</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>🌤️ Weather Condition</label>
                  <select name="weather" value={formData.weather} onChange={handleInputChange}>
                    <option value="Overcast">Overcast</option>
                    <option value="Sunny">Sunny</option>
                    <option value="Rainy">Rainy</option>
                    <option value="Cloudy">Cloudy</option>
                    <option value="Stormy">Stormy</option>
                    <option value="Snowy">Snowy</option>
                    <option value="Clear">Clear</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowPredictModal(false)}>Cancel</button>
              <button
                className="btn-primary"
                onClick={handlePredict}
                disabled={predicting}
              >
                {predicting ? 'Predicting...' : '🔮 Predict Demand'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Result Modal */}
      {showResultModal && predictionResult && (
        <div className="modal-overlay" onClick={() => setShowResultModal(false)}>
          <div className="modal-content result-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header success">
              <h2>✅ Prediction Complete</h2>
              <button className="close-btn" onClick={() => setShowResultModal(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="result-card">
                <div className="result-header">
                  <img
                    src={predictionResult.prediction.product_thumbnail}
                    alt={predictionResult.prediction.product_title}
                    className="result-thumbnail"
                  />
                  <div>
                    <h3>{predictionResult.prediction.product_title}</h3>
                    <p>{predictionResult.message}</p>
                  </div>
                </div>

                <div className="result-stats">
                  <div className="stat-box">
                    <span className="stat-label">Base Forecast</span>
                    <span className="stat-value">{Math.round(predictionResult.prediction.base_forecast)}</span>
                    <span className="stat-unit">units/week</span>
                  </div>

                  <div className="stat-arrow">→</div>

                  <div className="stat-box highlight">
                    <span className="stat-label">Adjusted Forecast</span>
                    <span className="stat-value">{Math.round(predictionResult.prediction.adjusted_forecast)}</span>
                    <span className="stat-unit">units/week</span>
                  </div>
                </div>

                <div className="result-details">
                  <div className="detail-row">
                    <span>Demand Level</span>
                    {getDemandBadge(predictionResult.prediction.demand_level)}
                  </div>
                  {predictionResult.prediction.trend_score && (
                    <div className="detail-row">
                      <span>Trend Score</span>
                      <span>{predictionResult.prediction.trend_score.toFixed(1)}/100</span>
                    </div>
                  )}
                  {predictionResult.prediction.multiplier && (
                    <div className="detail-row">
                      <span>Adjustment Multiplier</span>
                      <span>×{predictionResult.prediction.multiplier.toFixed(3)}</span>
                    </div>
                  )}
                  {predictionResult.prediction.demand_change_pct !== null && (
                    <div className="detail-row">
                      <span>Change from Previous Forecast of week</span>
                      <span className={predictionResult.prediction.demand_change_pct > 0 ? 'positive' : 'negative'}>
                        {predictionResult.prediction.demand_change_pct > 0 ? '+' : ''}
                        {predictionResult.prediction.demand_change_pct.toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>

                {/* Dynamic Pricing Auto-Trigger Section */}
                {predictionResult.dynamic_pricing_triggered && predictionResult.dynamic_pricing && (
                  <div className="dynamic-pricing-section auto-activated">
                    <div className="dp-header">
                      <span className="dp-icon">⚡</span>
                      <span>Dynamic Pricing Auto-Activated!</span>
                    </div>
                    <div className="dp-details">
                      <div className="dp-price-change">
                        <span className="original-price">${predictionResult.dynamic_pricing.original_price.toFixed(2)}</span>
                        <span className="price-arrow">→</span>
                        <span className="new-price">${predictionResult.dynamic_pricing.predicted_price.toFixed(2)}</span>
                        <span className={`price-direction ${predictionResult.dynamic_pricing.price_direction}`}>
                          {predictionResult.dynamic_pricing.price_direction === 'increased' ? '↑' : '↓'}
                        </span>
                        <span className="dp-status-active">✓ LIVE</span>
                      </div>
                      <p className="dp-reason success">
                        Price {predictionResult.dynamic_pricing.price_direction} due to <strong>{predictionResult.prediction.demand_level}</strong> demand level.
                        This price is now active on the product!
                      </p>
                    </div>
                  </div>
                )}

                {/* Promotion Created Section */}
                {predictionResult.promotion_created && predictionResult.promotion_id && (
                  <div className="promotion-section">
                    <div className="promo-header">
                      <span className="promo-icon">🎯</span>
                      <span>Promotional Banner Created!</span>
                    </div>
                    <div className="promo-details">
                      <p>
                        A promotional banner has been created for this discounted product.
                      </p>
                      <div className="promo-id-badge">
                        Promotion ID: <strong>{predictionResult.promotion_id}</strong>
                      </div>
                      <p className="promo-note">
                        📝 The promotion is in <strong>draft</strong> status. Go to Promotions tab to review and activate.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowResultModal(false)}>Close</button>
              <button className="btn-primary" onClick={handleAcknowledge}>
                ✅ Acknowledge
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Predict Modal */}
      {showBulkPredictModal && (
        <div className="modal-overlay" onClick={() => setShowBulkPredictModal(false)}>
          <div className="modal-content predict-modal bulk-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>🚀 Bulk Predict All Products</h2>
              <button className="close-btn" onClick={() => setShowBulkPredictModal(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="bulk-info">
                <div className="bulk-info-icon">📦</div>
                <p>This will run demand prediction for <strong>all products</strong> in the system using the same conditions. This may take a moment.</p>
              </div>

              {error && <div className="error-message">{error}</div>}

              <div className="form-grid">
                <div className="form-group">
                  <label>🎄 Holiday Condition</label>
                  <select
                    name="holiday"
                    value={bulkFormData.holiday}
                    onChange={(e) => setBulkFormData(prev => ({ ...prev, holiday: e.target.value }))}
                  >
                    <option value="No Holiday">No Holiday</option>
                    <option value="Christmas">Christmas</option>
                    <option value="New Year">New Year</option>
                    <option value="Black Friday">Black Friday</option>
                    <option value="Cyber Monday">Cyber Monday</option>
                    <option value="Valentine's Day">Valentine's Day</option>
                    <option value="Mother's Day">Mother's Day</option>
                    <option value="Father's Day">Father's Day</option>
                    <option value="Easter">Easter</option>
                    <option value="Thanksgiving">Thanksgiving</option>
                    <option value="Independence Day">Independence Day</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>🌤️ Weather Condition</label>
                  <select
                    name="weather"
                    value={bulkFormData.weather}
                    onChange={(e) => setBulkFormData(prev => ({ ...prev, weather: e.target.value }))}
                  >
                    <option value="Overcast">Overcast</option>
                    <option value="Sunny">Sunny</option>
                    <option value="Rainy">Rainy</option>
                    <option value="Cloudy">Cloudy</option>
                    <option value="Stormy">Stormy</option>
                    <option value="Snowy">Snowy</option>
                    <option value="Clear">Clear</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowBulkPredictModal(false)}>Cancel</button>
              <button
                className="btn-primary btn-bulk"
                onClick={handleBulkPredict}
                disabled={predicting}
              >
                {predicting ? '⏳ Predicting All...' : '🚀 Predict All Products'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Result Modal */}
      {showBulkResultModal && bulkPredictionResult && (
        <div className="modal-overlay" onClick={() => setShowBulkResultModal(false)}>
          <div className="modal-content result-modal bulk-result-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header success">
              <h2>✅ Bulk Prediction Complete</h2>
              <button className="close-btn" onClick={() => setShowBulkResultModal(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="bulk-result-summary">
                <div className="summary-icon">🎉</div>
                <h3>Demand Prediction Complete!</h3>
                <p>Successfully predicted demand for <strong>{bulkPredictionResult.total_products}</strong> products</p>
              </div>

              <div className="bulk-result-breakdown">
                <h4>Demand Level Breakdown:</h4>
                <div className="breakdown-grid">
                  {['very_low', 'low', 'medium', 'high', 'very_high'].map(level => {
                    const count = bulkPredictionResult.predictions?.filter(p => p.demand_level === level).length || 0;
                    return (
                      <div key={level} className={`breakdown-item ${level}`}>
                        <span className="breakdown-count">{count}</span>
                        <span className="breakdown-label">{level.replace('_', ' ')}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Dynamic Pricing Auto-Triggered Info */}
              {bulkPredictionResult.dynamic_pricing_triggered_count > 0 && (
                <div className="dynamic-pricing-triggered-info auto-activated">
                  <h4>⚡ Dynamic Pricing Auto-Activated</h4>
                  <p>
                    <strong>{bulkPredictionResult.dynamic_pricing_triggered_count}</strong> products
                    had their prices <strong>automatically updated</strong>!
                  </p>
                  <div className="triggered-products-list">
                    {bulkPredictionResult.dynamic_pricing_results?.slice(0, 5).map((dp, idx) => (
                      <div key={idx} className="triggered-product-item">
                        <span className="triggered-product-name">{dp.product_title}</span>
                        <span className="triggered-price-change">
                          ${dp.original_price?.toFixed(2)} → <strong>${dp.predicted_price?.toFixed(2)}</strong>
                          {dp.price_direction === 'increased' ? ' ↑' : ' ↓'}
                        </span>
                        {getDemandBadge(dp.demand_level)}
                        <span className="status-activated">✓ Active</span>
                      </div>
                    ))}
                  </div>
                  <p className="dynamic-pricing-note success">
                    ✅ Dynamic prices are now <strong>LIVE</strong> on these products!
                  </p>
                </div>
              )}

              {/* Promotions Auto-Created Info */}
              {bulkPredictionResult.promotions_created_count > 0 && (
                <div className="promotions-created-info">
                  <h4>🎯 Promotional Banners Created</h4>
                  <p>
                    <strong>{bulkPredictionResult.promotions_created_count}</strong> promotional banners
                    were auto-created for products with dynamic pricing!
                  </p>
                  <div className="triggered-products-list">
                    {bulkPredictionResult.promotion_results?.slice(0, 3).map((promo, idx) => (
                      <div key={idx} className="triggered-product-item promotion-item">
                        <span className="promo-icon">🏷️</span>
                        <span className="triggered-product-name">{promo.product_title}</span>
                        <span className="promo-id">ID: {promo.promotion_id}</span>
                        <span className="status-draft">Draft</span>
                      </div>
                    ))}
                  </div>
                  <p className="promotions-note">
                    📝 Promotions created as <strong>drafts</strong>. Go to Promotions tab to review and activate.
                  </p>
                </div>
              )}

              <div className="bulk-result-list">
                <h4>Top Predictions:</h4>
                <div className="result-list-scroll">
                  {bulkPredictionResult.predictions?.slice(0, 10).map((pred, idx) => (
                    <div key={idx} className={`result-list-item ${pred.dynamic_pricing_triggered ? 'pricing-triggered' : ''}`}>
                      <img src={pred.product_thumbnail} alt={pred.product_title} className="mini-thumb" />
                      <span className="result-product-name">{pred.product_title}</span>
                      <span className="result-forecast">{Math.round(pred.adjusted_forecast)} units</span>
                      {getDemandBadge(pred.demand_level)}
                      {pred.dynamic_pricing_triggered && <span className="pricing-badge">💰</span>}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-primary" onClick={() => setShowBulkResultModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const DemandPrediction = () => {
  return (
    <ErrorBoundary>
      <DemandPredictionContent />
    </ErrorBoundary>
  );
};

export default DemandPrediction;
