import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { usePlayer } from '../context/PlayerContext';
import { playlistService } from '../services/playlistService';
import '../styles/AlbumDetail.css';

export default function AlbumDetail() {
  const { albumName } = useParams();
  const { state } = useLocation();
  const navigate = useNavigate();
  const { token } = useAuth();
  const { playTrack, playTracks, current } = usePlayer();
  const album = state?.album;

  const [likedTracks, setLikedTracks] = useState({});
  const [playlistMenuTrack, setPlaylistMenuTrack] = useState(null);
  const [playlists, setPlaylists] = useState([]);
  const [loadingPlaylists, setLoadingPlaylists] = useState(false);

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

  const handleOpenPlaylistMenu = async (trackId) => {
    setPlaylistMenuTrack(trackId);
    if (playlists.length === 0) {
      setLoadingPlaylists(true);
      try {
        const pls = await playlistService.listPlaylists(token);
        setPlaylists(pls);
      } catch (e) {
        console.error('Failed to load playlists:', e);
      } finally {
        setLoadingPlaylists(false);
      }
    }
  };

  const handleAddToPlaylist = async (playlistId, track) => {
    try {
      await playlistService.addTrack(token, playlistId, {
        title: track.title,
        artist: track.artist,
        audio_url: track.audio_url,
        cover_url: track.cover_url,
        duration_ms: track.duration_ms,
      });
      setPlaylistMenuTrack(null);
    } catch (e) {
      console.error('Failed to add track to playlist:', e);
    }
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
            const showPlaylistMenu = playlistMenuTrack === track.id;
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
                  <div className="track-playlist-menu">
                    <button
                      className="track-add"
                      onClick={() => handleOpenPlaylistMenu(track.id)}
                      title="Add to playlist"
                    >
                      +
                    </button>
                    {showPlaylistMenu && (
                      <div className="track-playlist-dropdown">
                        {loadingPlaylists ? (
                          <p>Loading…</p>
                        ) : playlists.length > 0 ? (
                          playlists.map(pl => (
                            <button
                              key={pl.id}
                              className="playlist-option"
                              onClick={() => handleAddToPlaylist(pl.id, track)}
                            >
                              {pl.name}
                            </button>
                          ))
                        ) : (
                          <p>No playlists</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
}
