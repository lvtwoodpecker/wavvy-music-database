import React, { useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { usePlayer } from '../context/PlayerContext';
import '../styles/AlbumDetail.css';

export default function AlbumDetail() {
  const { albumName } = useParams();
  const { state } = useLocation();
  const navigate = useNavigate();
  const { playTrack, playTracks, current } = usePlayer();
  const album = state?.album;

  const [likedTracks, setLikedTracks] = useState({});

  if (!album) {
    return (
      <main className="album-detail">
        <button className="back-btn" onClick={() => navigate(-1)}>← Back</button>
        <p>Album not found. <a href="/library">Go back to Library</a>.</p>
      </main>
    );
  }

  const handleLikeTrack = (trackId) => {
    setLikedTracks(prev => ({ ...prev, [trackId]: !prev[trackId] }));
    // TODO: POST to /api/favorites/add with track_id
  };

  const handleAddToPlaylist = (trackId) => {
    // TODO: POST to /api/playlist/{playlistId}/add-track with track_id
  };

  const handlePlayTrack = (track) => {
    playTrack(track, { replace: false });
  };

  return (
    <main className="album-detail">
      <button className="back-btn" onClick={() => navigate(-1)}>← Back</button>

      <div className="album-header">
        {album.cover_url ? (
          <img src={album.cover_url} alt={album.album} className="album-hero" />
        ) : (
          <div className="album-hero-placeholder">🎵</div>
        )}
        <div className="album-info">
          <h1>{album.album}</h1>
          <p className="album-artist">{album.artist}</p>
          <p className="album-count">{album.tracks.length} tracks</p>
          <button className="album-play-all" onClick={() => playTracks(album.tracks)}>
            ▶ Play All
          </button>
        </div>
      </div>

      <div className="album-tracks">
        <h2>Tracks</h2>
        <div className="track-list">
          {album.tracks.map((track, idx) => {
            const isCurrentTrack = current?.id === track.id;
            return (
              <div key={`${track.id}-${idx}`} className={`track-item ${isCurrentTrack ? 'active' : ''}`}>
                <div className="track-number">{(track.track_no || idx + 1).toString().padStart(2, '0')}</div>
                <div className="track-info" onDoubleClick={() => handlePlayTrack(track)}>
                  <div className="track-title">{track.title}</div>
                  <div className="track-artist">{track.artist}</div>
                </div>
                <div className="track-actions">
                  <button
                    className={`track-like ${likedTracks[track.id] ? 'liked' : ''}`}
                    onClick={() => handleLikeTrack(track.id)}
                    title="Add to favorites"
                  >
                    ♡
                  </button>
                  <button
                    className="track-add"
                    onClick={() => handleAddToPlaylist(track.id)}
                    title="Add to playlist"
                  >
                    +
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
}
