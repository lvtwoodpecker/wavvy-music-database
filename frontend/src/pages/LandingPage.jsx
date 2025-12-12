// src/pages/LandingPage.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/LandingPage.css';

function LandingPage() {
  return (
    <div className="landing-page">
      {/* Header */}
      <header className="landing-header">
        <div className="header-content">
          <div className="logo">Wavvy</div>
          <nav className="nav-links">
            <Link to="/">Home</Link>
            <Link to="/login" className="nav-login">Login</Link>
            <Link to="/signup" className="nav-signup">Sign Up</Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">Wavvy — Discover Music. Power Campaigns. Smarter.</h1>
          <p className="hero-subtitle">
            The ultimate platform connecting music lovers with intelligent recommendations
            and empowering advertisers with data-driven campaigns.
          </p>
          <div className="hero-buttons">
            <Link to="/signup" className="btn btn-primary">Sign Up</Link>
            <Link to="/login" className="btn btn-secondary">Login</Link>
          </div>
        </div>
      </section>

      {/* For Listeners Section */}
      <section className="info-section">
        <div className="section-content">
          <h2>For Listeners</h2>
          <p>
            Discover your next favorite song with Wavvy's machine learning-powered recommendations.
            Our intelligent system learns your taste and connects you with music you'll love.
          </p>
          <ul className="feature-list">
            <li>Personalized music recommendations tailored to your taste</li>
            <li>Discover new artists and genres</li>
            <li>Curated playlists updated daily</li>
            <li>Seamless listening experience across devices</li>
          </ul>
        </div>
      </section>

      {/* For Advertisers Section */}
      <section className="info-section alternate">
        <div className="section-content">
          <h2>For Advertisers</h2>
          <p>
            Reach your target audience with precision. Wavvy provides powerful tools
            to create, manage, and optimize your advertising campaigns.
          </p>
          <ul className="feature-list">
            <li>Advanced targeting based on user preferences and behavior</li>
            <li>Real-time analytics and campaign performance tracking</li>
            <li>Flexible budget management and optimization</li>
            <li>Access to engaged music listeners</li>
          </ul>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="info-section">
        <div className="section-content">
          <h2>How It Works</h2>
          <p>
            Wavvy uses cutting-edge machine learning algorithms to understand music preferences
            and deliver personalized experiences.
          </p>
          <div className="how-it-works-grid">
            <div className="how-card">
              <div className="how-number">1</div>
              <h3>Listen & Learn</h3>
              <p>As you listen, our ML models learn your unique taste</p>
            </div>
            <div className="how-card">
              <div className="how-number">2</div>
              <h3>Smart Recommendations</h3>
              <p>Get personalized suggestions based on your preferences</p>
            </div>
            <div className="how-card">
              <div className="how-number">3</div>
              <h3>Discover More</h3>
              <p>Explore new music perfectly matched to your taste</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <p>&copy; 2025 Wavvy. All rights reserved.</p>
          <div className="footer-links">
            <span>About</span>
            <span>FAQ</span>
            <span>Pricing</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;
