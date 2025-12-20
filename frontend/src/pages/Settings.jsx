// src/pages/Settings.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { stripeService } from '../services/stripeService';
import { subscriptionService } from '../services/subscriptionService';
import { authService } from '../services/authService';
import PayButton from '../components/PayButton.jsx';
import '../styles/Settings.css';

function Settings() {
  const { user, token, logout, isPremium, markPremium, cancelPremium, setPremiumExpiry } = useAuth();
  const navigate = useNavigate();
  const [stripeStatus, setStripeStatus] = useState({
    connected: false,
    stripe_customer_id: null,
    created_at: null,
  });
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [canceling, setCanceling] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [changingPwd, setChangingPwd] = useState(false);

  useEffect(() => {
    fetchStripeStatus();
    fetchSubscriptionStatus();
  }, []);

  // Re-fetch subscription when auth/premium changes (e.g., after payment success)
  useEffect(() => {
    if (token) fetchSubscriptionStatus();
  }, [token, isPremium]);

  const fetchSubscriptionStatus = async () => {
    if (!token) return;
    try {
      const sub = await subscriptionService.getStatus(token);
      setSubscription(sub);
      if (sub?.status === 'active') {
        markPremium(sub.plan_name || 'Premium');
        if (sub?.expires_at) setPremiumExpiry(sub.expires_at);
      }
    } catch (err) {
      console.error('Error fetching subscription status:', err);
    }
  };

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

  const handleCancelSubscription = async () => {
    try {
      setCanceling(true);
      setError(null);
      await subscriptionService.cancel(token);
      cancelPremium();
      await fetchSubscriptionStatus();
    } catch (err) {
      setError(err.message);
    } finally {
      setCanceling(false);
      setShowCancelConfirm(false);
    }
  };

  const subscriptionActive = subscription?.status === 'active';
  const localExpiry = (typeof window !== 'undefined') ? localStorage.getItem('premium_expires_at') : null;
  const expiresAtDate = subscription?.expires_at
    ? new Date(subscription.expires_at)
    : (localExpiry ? new Date(localExpiry) : null);
  const expiresDisplay = expiresAtDate ? expiresAtDate.toLocaleDateString() : null;
  const now = new Date();
  const hasSub = !!subscription;
  const isActiveDisplay = hasSub ? (subscription?.status === 'active') : (isPremium || (expiresAtDate && expiresAtDate > now));
  const displayPlan = subscription?.plan_name || user?.subscription_plan || (isPremium ? 'Premium' : 'N/A');

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
              <div className="info-item">
                <span className="info-label">Subscription:</span>
                <span className="info-value">{isPremium ? 'Premium' : 'Free'}</span>
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

          <div className="subscription-card">
            <div className="subscription-header">
              <div>
                <p className="label">Subscription</p>
                <p className="status-text">{isActiveDisplay ? 'Active' : 'Inactive'}</p>
              </div>
              {isActiveDisplay && (
                <button
                  className="secondary"
                  onClick={() => setShowCancelConfirm(true)}
                  disabled={canceling}
                >
                  Cancel Subscription
                </button>
              )}
            </div>
            <div className="subscription-body">
              <p><strong>Plan:</strong> {displayPlan}</p>
              <p><strong>Renews/Ends:</strong> {expiresDisplay || 'Unknown'}</p>
              {subscription?.canceled_at && (
                <p><strong>Cancelled on:</strong> {new Date(subscription.canceled_at).toLocaleDateString()}</p>
              )}
              {!isActiveDisplay && (
                <div className="resubscribe-row">
                  <p className="resubscribe-text">Want to come back? Enjoy Premium features again.</p>
                  <PayButton />
                </div>
              )}
            </div>
            {showCancelConfirm && (
              <div className="confirm-panel">
                <p className="confirm-title">Confirm cancellation</p>
                <p className="confirm-body">You will lose Premium features immediately. Are you sure?</p>
                <div className="confirm-actions">
                  <button className="confirm-cancel" onClick={handleCancelSubscription} disabled={canceling}>
                    {canceling ? 'Cancelling…' : 'Confirm Cancel'}
                  </button>
                  <button className="confirm-dismiss" onClick={() => setShowCancelConfirm(false)} disabled={canceling}>
                    Keep Subscription
                  </button>
                </div>
              </div>
            )}
          </div>
          
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
