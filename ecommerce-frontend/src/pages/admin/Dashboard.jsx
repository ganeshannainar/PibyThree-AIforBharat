import { Link } from 'react-router-dom';

const AdminDashboard = () => {
  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <h1>📊 Admin Dashboard</h1>
        <p className="admin-subtitle">Manage your e-commerce platform</p>
      </div>
      
      <div className="admin-nav-grid">
        <Link to="/admin/products" className="admin-nav-card">
          <div className="nav-card-icon">📦</div>
          <div className="nav-card-content">
            <h3>Products</h3>
            <p>Manage inventory</p>
          </div>
        </Link>
        <Link to="/admin/categories" className="admin-nav-card">
          <div className="nav-card-icon">📁</div>
          <div className="nav-card-content">
            <h3>Categories</h3>
            <p>Organize products</p>
          </div>
        </Link>
        <Link to="/admin/dynamic-pricing" className="admin-nav-card pricing-card">
          <div className="nav-card-icon">💰</div>
          <div className="nav-card-content">
            <h3>Dynamic Pricing</h3>
            <p>ML-powered optimization</p>
          </div>
        </Link>
        <Link to="/admin/demand-prediction" className="admin-nav-card demand-card">
          <div className="nav-card-icon">📊</div>
          <div className="nav-card-content">
            <h3>Demand Prediction</h3>
            <p>AI demand forecasting</p>
          </div>
        </Link>
        <Link to="/admin/promotions" className="admin-nav-card promotions-card">
          <div className="nav-card-icon">🎯</div>
          <div className="nav-card-content">
            <h3>Promotions</h3>
            <p>AI-generated content</p>
          </div>
        </Link>
        <Link to="/admin/users" className="admin-nav-card">
          <div className="nav-card-icon">👥</div>
          <div className="nav-card-content">
            <h3>Users</h3>
            <p>Manage accounts</p>
          </div>
        </Link>
      </div>

      <div className="admin-info-card">
        <div className="info-card-header">
          <span className="info-icon">💼</span>
          <h2>Quick Actions</h2>
        </div>
        <div className="info-card-body">
          <p>Welcome to the Admin Dashboard. From here you can:</p>
          <ul className="action-list">
            <li>
              <span className="action-icon">📦</span>
              <div>
                <strong>Products</strong>
                <span>Add, edit, or remove products from the store</span>
              </div>
            </li>
            <li>
              <span className="action-icon">📁</span>
              <div>
                <strong>Categories</strong>
                <span>Organize products into categories</span>
              </div>
            </li>
            <li>
              <span className="action-icon">💰</span>
              <div>
                <strong>Dynamic Pricing</strong>
                <span>Use ML-powered predictions to optimize prices</span>
              </div>
            </li>
            <li>
              <span className="action-icon">📊</span>
              <div>
                <strong>Demand Prediction</strong>
                <span>AI-powered demand forecasting for inventory planning</span>
              </div>
            </li>
            <li>
              <span className="action-icon">🎯</span>
              <div>
                <strong>Promotions</strong>
                <span>Review and approve AI-generated promotional content</span>
              </div>
            </li>
            <li>
              <span className="action-icon">👥</span>
              <div>
                <strong>Users</strong>
                <span>Manage user accounts and roles</span>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
