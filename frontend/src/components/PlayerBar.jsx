import React, { useEffect } from 'react';
import { usePlayer } from '../context/PlayerContext';
import { useAuth } from '../context/AuthContext';
import { playlistService } from '../services/playlistService';
import '../styles/Player.css';

export default function PlayerBar() {
  const { isAuthenticated, token } = useAuth();
  const { current, queue, isPlaying, toggle, next, prev, progress, seek, volume, setVolume } = usePlayer();
  const [liked, setLiked] = React.useState(false);
  const [showPlaylistMenu, setShowPlaylistMenu] = React.useState(false);
  const [playlists, setPlaylists] = React.useState([]);
  const [loadingPlaylists, setLoadingPlaylists] = React.useState(false);

  // Hardcode 30 seconds for demo snippets
  const durationSec = 30;

  // Check if current track is liked
  useEffect(() => {
    if (current) {
      const likedTracks = JSON.parse(localStorage.getItem('likedTracks') || '[]');
      setLiked(likedTracks.some(t => t.id === current.id));
    }
  }, [current]);

  // Load playlists when menu opens
  useEffect(() => {
    if (showPlaylistMenu && playlists.length === 0) {
      setLoadingPlaylists(true);
      playlistService.listPlaylists(token)
        .then(pls => setPlaylists(pls))
        .catch(e => console.error('Failed to load playlists:', e))
        .finally(() => setLoadingPlaylists(false));
    }
  }, [showPlaylistMenu, token]);

  // Hide bar if not logged in or nothing queued
  if (!isAuthenticated || (!current && (!queue || queue.length === 0))) {
    return null;
  }

  const handleLike = () => {
    if (!current) return;
    const newLiked = !liked;
    setLiked(newLiked);
    
    // Save to localStorage
    const likedTracks = JSON.parse(localStorage.getItem('likedTracks') || '[]');
    if (newLiked) {
      // Add track if not already liked
      if (!likedTracks.find(t => t.id === current.id)) {
        likedTracks.push(current);
        localStorage.setItem('likedTracks', JSON.stringify(likedTracks));
      }
    } else {
      // Remove track
      const filtered = likedTracks.filter(t => t.id !== current.id);
      localStorage.setItem('likedTracks', JSON.stringify(filtered));
    }
  };

  const handleAddToPlaylist = async (playlistId) => {
    if (!current) return;
    try {
      await playlistService.addTrack(token, playlistId, {
        title: current.title,
        artist: current.artist,
        audio_url: current.audio_url,
        cover_url: current.cover_url,
        duration_ms: current.duration_ms,
      });
      setShowPlaylistMenu(false);
    } catch (e) {
      console.error('Failed to add track to playlist:', e);
    }
  };

  return (
    <div className="player-bar">
      <div className="player-meta">
        {current?.cover_url ? (
          <img src={current.cover_url} alt={current.title} className="player-cover" />
        ) : (
          <div className="player-cover placeholder">—</div>
        )}
        <div className="player-text">
          <div className="player-title">{current?.title || 'Nothing playing'}</div>
          <div className="player-artist">{current?.artist || ''}</div>
        </div>
        <div className="player-actions">
          <button
            className={`player-action-btn ${liked ? 'liked' : ''}`}
            onClick={handleLike}
            title={liked ? 'Remove from favorites' : 'Add to favorites'}
          >
            ♡
          </button>
          <div className="playlist-menu">
            <button className="player-action-btn" onClick={() => setShowPlaylistMenu(!showPlaylistMenu)} title="Add to playlist">
              +
            </button>
            {showPlaylistMenu && (
              <div className="playlist-dropdown">
                {loadingPlaylists ? (
                  <p className="placeholder">Loading…</p>
                ) : playlists.length > 0 ? (
                  playlists.map(pl => (
                    <button
                      key={pl.id}
                      className="playlist-item"
                      onClick={() => handleAddToPlaylist(pl.id)}
                    >
                      {pl.name}
                    </button>
                  ))
                ) : (
                  <p className="placeholder">No playlists</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="player-controls">
        <button className="player-btn" onClick={prev} disabled={!current}>⏮</button>
        <button className="player-btn primary" onClick={toggle} disabled={!current}>
          {isPlaying ? '⏸' : '▶'}
        </button>
        <button className="player-btn" onClick={next} disabled={!current}>⏭</button>
        <div className="player-progress">
          <input
            type="range"
            min={0}
            max={durationSec}
            value={Math.floor(progress)}
            onChange={(e) => seek(parseInt(e.target.value, 10))}
          />
        </div>
      </div>

      <div className="player-volume">
        <span>🔊</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={volume}
          onChange={(e) => setVolume(parseFloat(e.target.value))}
        />
      </div>
    </div>
  );
}
