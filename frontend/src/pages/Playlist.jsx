import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { usePlayer } from '../context/PlayerContext';
import { playlistService } from '../services/playlistService';
import '../styles/Playlist.css';

export default function PlaylistPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const { playTrack, playTracks, current } = usePlayer();
  const [playlist, setPlaylist] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [confirmRemove, setConfirmRemove] = useState(null);

  const load = async () => {
    try {
      setLoading(true);
      const data = await playlistService.getPlaylist(token, id);
      setPlaylist(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [id]);

  const handleRemoveTrack = async (trackId) => {
    try {
      await playlistService.removeTrack(token, id, trackId);
      setConfirmRemove(null);
      await load();
    } catch (e) {
      setError(e.message);
    }
  };

  if (loading) return <main className="pl-main"><p>Loading playlist…</p></main>;
  if (error) return <main className="pl-main"><p className="error">{error}</p></main>;
  if (!playlist) return null;

  return (
    <main className="pl-main">
      <button className="back-btn" onClick={() => navigate(-1)}>← Back</button>
      <div className="pl-header">
        <div className="pl-cover">🎵</div>
        <div>
          <h1>{playlist.name}</h1>
          {playlist.description && <p>{playlist.description}</p>}
          <p className="pl-count">{playlist.tracks?.length || 0} tracks</p>
          {playlist.tracks && playlist.tracks.length > 0 && (
            <button className="pl-play-all" onClick={() => playTracks(playlist.tracks)}>▶ Play All</button>
          )}
        </div>
      </div>
      <div className="pl-tracks">
        {playlist.tracks?.length ? (
          playlist.tracks.map((t, idx) => {
            const isCurrentTrack = current?.id === t.id;
            return (
              <div key={t.id} className={`pl-track ${isCurrentTrack ? 'active' : ''}`} onDoubleClick={() => playTrack(t)}>
                <span className="idx">{(idx + 1).toString().padStart(2, '0')}</span>
                <div className="track-info">
                  <span className="title">{t.title}</span>
                  <span className="artist">{t.artist || 'Unknown'}</span>
                </div>
                <button className="remove-btn" onClick={(e) => { e.stopPropagation(); setConfirmRemove(t); }} title="Remove from playlist">✕</button>
              </div>
            );
          })
        ) : (
          <p>No tracks yet.</p>
        )}
      </div>

      {confirmRemove && (
        <div className="modal-overlay">
          <div className="confirmation-modal">
            <h3>Remove Song?</h3>
            <p>Are you sure you want to remove "{confirmRemove.title}" from this playlist?</p>
            <div className="modal-actions">
              <button className="cancel-btn" onClick={() => setConfirmRemove(null)}>Cancel</button>
              <button className="confirm-btn" onClick={() => handleRemoveTrack(confirmRemove.id)}>Remove</button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
