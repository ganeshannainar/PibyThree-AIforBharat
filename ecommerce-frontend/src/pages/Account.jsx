import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { accountAPI } from '../services/api';

const Account = () => {
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    full_name: user?.full_name || ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await accountAPI.updateMyInfo(formData);
      setSuccess('Profile updated successfully!');
      setEditing(false);
      refreshUser();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    }
    setLoading(false);
  };

  const handleDeleteAccount = async () => {
    if (!window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      return;
    }

    try {
      await accountAPI.deleteMyAccount();
      logout();
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete account');
    }
  };

  if (!user) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="account-page">
      <h1>My Account</h1>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <div className="account-card">
        <h2>Profile Information</h2>
        
        {editing ? (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Full Name</label>
              <input
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label>Username</label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>
            <div className="account-actions">
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
              <button 
                type="button" 
                className="btn btn-secondary"
                onClick={() => {
                  setEditing(false);
                  setFormData({
                    username: user.username,
                    email: user.email,
                    full_name: user.full_name
                  });
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <>
            <div className="account-info">
              <div className="account-info-row">
                <label>Full Name:</label>
                <span>{user.full_name}</span>
              </div>
              <div className="account-info-row">
                <label>Username:</label>
                <span>{user.username}</span>
              </div>
              <div className="account-info-row">
                <label>Email:</label>
                <span>{user.email}</span>
              </div>
              <div className="account-info-row">
                <label>Role:</label>
                <span style={{ textTransform: 'capitalize' }}>{user.role}</span>
              </div>
              <div className="account-info-row">
                <label>Status:</label>
                <span>{user.is_active ? '✅ Active' : '❌ Inactive'}</span>
              </div>
              <div className="account-info-row">
                <label>Member Since:</label>
                <span>{new Date(user.created_at).toLocaleDateString()}</span>
              </div>
            </div>
            <div className="account-actions">
              <button 
                onClick={() => setEditing(true)} 
                className="btn btn-primary"
              >
                Edit Profile
              </button>
            </div>
          </>
        )}
      </div>

      <div className="account-card">
        <h2>Danger Zone</h2>
        <p style={{ color: '#7f8c8d', marginBottom: '15px' }}>
          Once you delete your account, there is no going back. Please be certain.
        </p>
        <button onClick={handleDeleteAccount} className="btn btn-danger">
          Delete My Account
        </button>
      </div>
    </div>
  );
};

export default Account;
