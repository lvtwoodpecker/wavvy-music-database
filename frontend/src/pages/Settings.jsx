// src/pages/Settings.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { stripeService } from '../services/stripeService';
import { authService } from '../services/authService';
import '../styles/Settings.css';

function Settings() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const [stripeStatus, setStripeStatus] = useState({
    connected: false,
    stripe_customer_id: null,
    created_at: null,
  });
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [changingPwd, setChangingPwd] = useState(false);

  useEffect(() => {
    fetchStripeStatus();
  }, []);

  const fetchStripeStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const status = await stripeService.getStripeStatus(token);
      setStripeStatus(status);
    } catch (err) {
      console.error('Error fetching Stripe status:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectStripe = async () => {
    try {
      setConnecting(true);
      setError(null);
      setSuccessMessage(null);
      
      const result = await stripeService.connectStripeAccount(token);
      
      setSuccessMessage(result.message);
      
      // Refresh status
      await fetchStripeStatus();
    } catch (err) {
      console.error('Error connecting Stripe account:', err);
      setError(err.message);
    } finally {
      setConnecting(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleBackToHome = () => {
    navigate('/app');
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);
    try {
      setChangingPwd(true);
      const res = await authService.changePassword(token, oldPassword, newPassword);
      setSuccessMessage(res.message || 'Password updated');
      setOldPassword('');
      setNewPassword('');
    } catch (err) {
      setError(err.message);
    } finally {
      setChangingPwd(false);
    }
  };

  return (
    <main className="settings-main">
      <div className="settings-container">
        <div className="settings-header">
          <h1>Settings</h1>
          <div className="header-actions">
            <button onClick={handleBackToHome} className="back-button">
              Back to Home
            </button>
            <button onClick={handleLogout} className="logout-button">
              Logout
            </button>
          </div>
        </div>

        <div className="settings-section">
          <div className="user-info-section">
            <h2>Account Information</h2>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Name:</span>
                <span className="info-value">{user?.first_name} {user?.last_name}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Email:</span>
                <span className="info-value">{user?.email}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Username:</span>
                <span className="info-value">{user?.username}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Role:</span>
                <span className="info-value">{user?.role}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="settings-section">
          <h2>Security</h2>
          <form className="password-form" onSubmit={handleChangePassword}>
            <div className="form-row">
              <label htmlFor="oldPassword">Current Password</label>
              <input
                id="oldPassword"
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                placeholder="Enter current password"
              />
            </div>
            <div className="form-row">
              <label htmlFor="newPassword">New Password</label>
              <input
                id="newPassword"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password"
              />
            </div>
            <button type="submit" className="change-password-button" disabled={changingPwd}>
              {changingPwd ? 'Updating...' : 'Change Password'}
            </button>
          </form>
        </div>

        <div className="settings-section">
          <h2>Payments</h2>
          
          {loading ? (
            <div className="loading-state">
              <p>Loading Stripe status...</p>
            </div>
          ) : (
            <div className="stripe-section">
              <div className="stripe-status">
                <div className="status-indicator">
                  <span className={`status-dot ${stripeStatus.connected ? 'connected' : 'disconnected'}`}></span>
                  <span className="status-text">
                    {stripeStatus.connected ? 'Stripe account connected' : 'Not connected'}
                  </span>
                </div>
                
                {stripeStatus.connected && (
                  <div className="stripe-details">
                    <p className="stripe-info">
                      <strong>Customer ID:</strong> {stripeStatus.stripe_customer_id}
                    </p>
                    <p className="stripe-info">
                      <strong>Connected on:</strong> {new Date(stripeStatus.created_at).toLocaleDateString()}
                    </p>
                  </div>
                )}
              </div>

              {error && (
                <div className="error-message">
                  <p>{error}</p>
                </div>
              )}

              {successMessage && (
                <div className="success-message">
                  <p>{successMessage}</p>
                </div>
              )}

              {!stripeStatus.connected && (
                <div className="stripe-actions">
                  <button
                    onClick={handleConnectStripe}
                    disabled={connecting}
                    className="connect-stripe-button"
                  >
                    {connecting ? 'Connecting...' : 'Connect Stripe Account'}
                  </button>
                  <p className="stripe-description">
                    Connect your Stripe account to enable payments, subscriptions, and billing features.
                  </p>
                </div>
              )}

              {stripeStatus.connected && (
                <div className="stripe-actions">
                  <p className="stripe-connected-message">
                    Your Stripe account is connected and ready for payments.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

export default Settings;
