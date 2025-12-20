// src/pages/Home.jsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PayButton from '../components/PayButton.jsx';
import SearchBar from '../components/SearchBar.jsx';
import { useAuth } from '../context/AuthContext';
import { usePlayer } from '../context/PlayerContext';
import { musicService } from '../services/musicService';
import '../styles/Home.css';

function Home() {
  const { user, token, logout, isPremium } = useAuth();
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

  const handleAlbumClick = (e, album) => {
    if (e.target.closest('.album-play-btn')) {
      playTracks(album.tracks);
    } else {
      navigate(`/album/${encodeURIComponent(album.album)}`, { state: { album } });
    }
  };

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
            {isPremium && <span className="premium-pill">★ Premium</span>}
          </div>
          <div className="avatar">{(user?.first_name?.[0] || user?.username?.[0] || 'W').toUpperCase()}</div>
        </div>
      </div>

      <section className="hero">
        <span className="listener-mode">Listener Mode</span>
        <h1>Good evening</h1>
        <p>Your personalized music experience</p>
      </section>

      <section className="search-section">
        <SearchBar />
      </section>

      <section className="nav-links">
        <button className="nav-link" onClick={() => navigate('/liked')}>Liked Songs</button>
        <button className="nav-link" onClick={goPlaylists}>Playlists</button>
        <button className="nav-link" onClick={goLibrary}>Library</button>
      </section>

      <section className="trending-section">
        <div className="trending-header">
          <div className="trending-banner">
            <img src="https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=1200&h=300&fit=crop&auto=format" alt="Now Trending" />
            <div className="trending-overlay">
              <h2>Now Trending</h2>
              <p>Curated for you right now</p>
              <button className="trending-play-btn" onClick={() => navigate('/playlist/9')}>Open Playlist</button>
            </div>
          </div>
        </div>
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
        <div className="recent-grid">
          {recentAlbums.map((alb) => (
            <div key={alb.album} className="recent-card" onClick={(e) => handleAlbumClick(e, alb)}>
              <img src={alb.cover_url} alt={alb.album} />
              <div className="recent-meta">
                <div className="title">{alb.album}</div>
                <div className="artist">{alb.artist}</div>
                <button className="album-play-btn" onClick={(e) => { e.stopPropagation(); playTracks(alb.tracks); }}>▶ Play</button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {!isPremium && (
        <section className="cta">
          <div className="cta-text">
            <h3>Wavvy Premium (Test Mode)</h3>
            <p>Stripe test cards only — no real money happens here.</p>
            <div className="cta-actions">
              <PayButton />
            </div>
          </div>
          <div className="user-actions">
            <button onClick={handleSettings} className="settings-button">Settings</button>
            <button onClick={handleLogout} className="logout-button">Logout</button>
          </div>
        </section>
      )}

      {isPremium && (
        <section className="cta premium-cta">
          <div className="cta-text">
            <h3>Thanks for being Premium!</h3>
            <p>Enjoy full access. You can manage your subscription in Settings.</p>
          </div>
          <div className="user-actions">
            <button onClick={handleSettings} className="settings-button">Settings</button>
            <button onClick={handleLogout} className="logout-button">Logout</button>
          </div>
        </section>
      )}
    </main>
  );
}

export default Home;
