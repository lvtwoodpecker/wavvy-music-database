import React from 'react';
import { usePlayer } from '../context/PlayerContext';
import { useAuth } from '../context/AuthContext';
import '../styles/Player.css';

export default function PlayerBar() {
  const { isAuthenticated } = useAuth();
  const { current, queue, isPlaying, toggle, next, prev, progress, seek, volume, setVolume } = usePlayer();
  const [liked, setLiked] = React.useState(false);
  const [showPlaylistMenu, setShowPlaylistMenu] = React.useState(false);

  // Hardcode 30 seconds for demo snippets
  const durationSec = 30;

  // Hide bar if not logged in or nothing queued
  if (!isAuthenticated || (!current && (!queue || queue.length === 0))) {
    return null;
  }

  const handleLike = () => {
    setLiked(!liked);
    // TODO: POST to /api/favorites/add with track_id
  };

  const handleAddToPlaylist = (playlistId) => {
    // TODO: POST to /api/playlist/{playlistId}/add-track with track_id
    setShowPlaylistMenu(false);
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
                <p className="placeholder">Select a playlist</p>
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
