import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';

const Navbar = () => {
  const { user, isAuthenticated, logout, isAdmin } = useAuth();
  const { getCartItemCount } = useCart();
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/products?search=${encodeURIComponent(searchQuery.trim().toLowerCase())}`);
      setSearchQuery('');
    }
  };

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        <img src="/White_Logo.png" alt="Pi Buy 3" className="navbar-logo" />
      </Link>

      <form onSubmit={handleSearch} className="navbar-search">
        <input
          type="text"
          placeholder="Search products..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="navbar-search-input"
        />
        <button type="submit" className="navbar-search-btn">🔍</button>
      </form>
      
      <div className="navbar-links">
        <Link to="/">Home</Link>
        <Link to="/products">Products</Link>
        
        {isAuthenticated && (
          <Link to="/cart" className="cart-link">
            Cart
            {getCartItemCount() > 0 && (
              <span className="cart-count">{getCartItemCount()}</span>
            )}
          </Link>
        )}
        
        {isAuthenticated && (
          <Link to="/orders">Orders</Link>
        )}
        
        {isAuthenticated && isAdmin() && (
          <Link to="/admin">Admin</Link>
        )}
        
        {isAuthenticated ? (
          <div className="navbar-user">
            <Link to="/account">
              👤 {user?.username}
            </Link>
            <button onClick={handleLogout} className="btn-logout">
              Logout
            </button>
          </div>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/signup">Sign Up</Link>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
