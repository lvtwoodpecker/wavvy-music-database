// src/pages/Home.jsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PayButton from '../components/PayButton.jsx';
import { useAuth } from '../context/AuthContext';
import { usePlayer } from '../context/PlayerContext';
import { musicService } from '../services/musicService';
import '../styles/Home.css';

function Home() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const { playTracks } = usePlayer();
  const [recentAlbums, setRecentAlbums] = useState([]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleSettings = () => {
    navigate('/settings');
  };
  const goLibrary = () => navigate('/library');
  const goNowPlaying = () => navigate('/now-playing');
  const goPlaylists = () => navigate('/playlists');

  useEffect(() => {
    (async () => {
      const albums = await musicService.getLibrary(token);
      setRecentAlbums(albums.slice(0, 6));
    })();
  }, [token]);

  return (
    <main className="home-main">
      <div className="home-topbar">
        <div className="brand">Wavvy</div>
        <div className="mode-toggle">
          <button className="pill active">Listener</button>
          <button className="pill">Advertiser</button>
        </div>
        <div className="user-chip">
          <div className="user-meta">
            <span className="muted">Logged in as</span>
            <span className="strong">{user?.email}</span>
          </div>
          <div className="avatar">{(user?.first_name?.[0] || user?.username?.[0] || 'W').toUpperCase()}</div>
        </div>
      </div>

      <section className="hero">
        <span className="listener-mode">Listener Mode</span>
        <h1>Good evening</h1>
        <p>Your personalized music experience</p>
      </section>

      <section className="stats">
        <div className="stat-card pink">
          <div className="stat-icon">⏱</div>
          <div>
            <div className="stat-value">124 hours</div>
            <div className="stat-label">Listening time this month</div>
          </div>
        </div>
        <div className="stat-card purple">
          <div className="stat-icon">♡</div>
          <div>
            <div className="stat-value">342 songs</div>
            <div className="stat-label">In your liked songs</div>
          </div>
        </div>
        <div className="stat-card mint">
          <div className="stat-icon">↗</div>
          <div>
            <div className="stat-value">18 artists</div>
            <div className="stat-label">Following</div>
          </div>
        </div>
      </section>

      <section className="recent">
        <div className="section-heading">
          <h2>Recently Played</h2>
          <button className="see-all" onClick={goLibrary}>See all</button>
        </div>
        <div className="recent-grid">
          {recentAlbums.map((alb) => (
            <div key={alb.album} className="recent-card" onClick={() => playTracks(alb.tracks)}>
              <img src={alb.cover_url} alt={alb.album} />
              <div className="recent-meta">
                <div className="title">{alb.album}</div>
                <div className="artist">{alb.artist}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="cta">
        <div className="cta-text">
          <h3>Wavvy Premium (Test Mode)</h3>
          <p>Stripe test cards only — no real money happens here.</p>
          <div className="cta-actions">
            <PayButton />
            <button className="ghost" onClick={goNowPlaying}>Now Playing</button>
            <button className="ghost" onClick={goPlaylists}>My Playlists</button>
          </div>
        </div>
        <div className="user-actions">
          <button onClick={handleSettings} className="settings-button">Settings</button>
          <button onClick={handleLogout} className="logout-button">Logout</button>
        </div>
      </section>
    </main>
  );
}

export default Home;
