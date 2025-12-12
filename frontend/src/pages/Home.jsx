// src/pages/Home.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import PayButton from '../components/PayButton.jsx';
import { useAuth } from '../context/AuthContext';
import '../styles/Home.css';

function Home() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleSettings = () => {
    navigate('/settings');
  };

  return (
    <main className="home-main">
      <div className="home-card">
        <div className="user-info">
          <h2>Welcome, {user?.first_name || user?.username}!</h2>
          <p className="user-email">{user?.email}</p>
          <div className="user-actions">
            <button onClick={handleSettings} className="settings-button">
              Settings
            </button>
            <button onClick={handleLogout} className="logout-button">
              Logout
            </button>
          </div>
        </div>
        
        <h1>Wavvy Premium (Test Mode)</h1>
        <p>
          This is a fake checkout for wavvy.
          Use Stripe test cards only – no real money happens here.
        </p>
        <PayButton />
      </div>
    </main>
  );
}

export default Home;
