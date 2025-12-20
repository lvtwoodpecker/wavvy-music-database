// src/pages/ForgotPassword.jsx
import React, { useState } from 'react';
import { authService } from '../services/authService';
import '../styles/Auth.css';

function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState(null);
  const [tokenDev, setTokenDev] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setTokenDev(null);
    try {
      setLoading(true);
      const res = await authService.requestPasswordReset(email);
      setMessage(res.message || 'If the email exists, a reset was initiated');
      if (res.token) setTokenDev(res.token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-main">
      <div className="auth-card">
        <h1>Forgot Password</h1>
        <form onSubmit={handleSubmit} className="auth-form">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Sending...' : 'Request Reset'}
          </button>
        </form>
        {error && <p className="auth-error">{error}</p>}
        {message && (
          <div className="auth-success">
            <p>{message}</p>
            {tokenDev && (
              <div className="dev-token">
                <p className="token-label">Dev Token (copy/paste):</p>
                <p className="token-mono">{tokenDev}</p>
                <a className="auth-link" href={`/reset-password?token=${encodeURIComponent(tokenDev)}`}>
                  Go to Reset Password
                </a>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

export default ForgotPassword;
