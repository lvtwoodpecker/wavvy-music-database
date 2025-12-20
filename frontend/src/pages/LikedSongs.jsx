import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePlayer } from '../context/PlayerContext';
import '../styles/Playlist.css';

export default function LikedSongs() {
  const navigate = useNavigate();
  const { playTrack, playTracks, current } = usePlayer();
  const [likedTracks, setLikedTracks] = useState([]);

  useEffect(() => {
    const liked = JSON.parse(localStorage.getItem('likedTracks') || '[]');
    setLikedTracks(liked);
  }, []);

  const handleRemove = (trackIndex) => {
    const updated = likedTracks.filter((_, idx) => idx !== trackIndex);
    setLikedTracks(updated);
    localStorage.setItem('likedTracks', JSON.stringify(updated));
  };

  const handlePlayAll = () => {
    if (likedTracks.length > 0) {
      playTracks(likedTracks);
    }
  };

  return (
    <main className="playlist-main">
      <div className="playlist-header" style={{ background: 'linear-gradient(180deg, #ff4757 0%, #1a1a1a 100%)' }}>
        <button className="back-btn" onClick={() => navigate(-1)}>← Back</button>
        <div className="playlist-art" style={{ fontSize: '18px', fontWeight: '700' }}>LIKED</div>
        <div className="playlist-meta">
          <span className="playlist-type">Playlist</span>
          <h1>Liked Songs</h1>
          <p>{likedTracks.length} songs</p>
        </div>
      </div>

      <div className="playlist-actions">
        <button className="play-all-btn" onClick={handlePlayAll} disabled={likedTracks.length === 0}>
          ▶ Play all
        </button>
      </div>

      <div className="tracklist">
        {likedTracks.length === 0 ? (
          <p className="empty">No liked songs yet. Like songs by clicking the ♡ button while playing!</p>
        ) : (
          likedTracks.map((track, idx) => (
            <div
              key={`${track.title}-${idx}`}
              className={`track-row ${current?.title === track.title ? 'active' : ''}`}
              onDoubleClick={() => playTrack(track, likedTracks)}
            >
              <div className="track-num">{idx + 1}</div>
              <div className="track-info">
                <div className="track-title">{track.title}</div>
                <div className="track-artist">{track.artist}</div>
              </div>
              <button className="track-remove" onClick={() => handleRemove(idx)}>×</button>
            </div>
          ))
        )}
      </div>
    </main>
  );
}
