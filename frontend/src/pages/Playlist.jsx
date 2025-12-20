import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { usePlayer } from '../context/PlayerContext';
import { playlistService } from '../services/playlistService';
import { recommenderService } from '../services/recommenderService';
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
  const [showAddPanel, setShowAddPanel] = useState(false);
  const [recommendations, setRecommendations] = useState([]);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [confirmDeletePlaylist, setConfirmDeletePlaylist] = useState(false);

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

  const openAddPanel = async () => {
    setShowAddPanel(true);
    setLoadingRecs(true);
    try {
      let recs = [];
      if (playlist?.tracks?.length > 0) {
        // Playlist has songs - recommend based on playlist vibe
        recs = await recommenderService.recommendForPlaylist(token, id, 15);
      } else {
        // New playlist - recommend based on user's listening history
        recs = await recommenderService.recommendForUser(token, 15);
      }
      setRecommendations(recs);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoadingRecs(false);
    }
  };

  const handleRemoveTrack = async (trackId) => {
    try {
      await playlistService.removeTrack(token, id, trackId);
      setConfirmRemove(null);
      await load();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleAddTrack = async (track) => {
    try {
      await playlistService.addTrack(token, id, {
        track_id: track.track_id,
      });
      await load();
      // Remove from recommendations list
      setRecommendations(recommendations.filter(r => (r.track_id || r.id) !== (track.track_id || track.id)));
    } catch (e) {
      setError(e.message);
    }
  };

  const handleDeletePlaylist = async () => {
    try {
      await playlistService.deletePlaylist(token, id);
      navigate('/playlists');
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
          {!playlist.is_public && (
            <>
              <button className="pl-add-btn" onClick={openAddPanel} title="Add songs to playlist">+ Add Songs</button>
              <button className="pl-delete-btn" onClick={() => setConfirmDeletePlaylist(true)} title="Delete playlist">Delete Playlist</button>
            </>
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
                {!playlist.is_public && (
                  <button className="remove-btn" onClick={(e) => { e.stopPropagation(); setConfirmRemove(t); }} title="Remove from playlist">✕</button>
                )}
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

      {showAddPanel && (
        <div className="modal-overlay">
          <div className="add-panel-modal">
            <div className="add-panel-header">
              <h3>{playlist.tracks?.length > 0 ? 'Recommended for your playlist' : 'Recommended for you'}</h3>
              <button className="close-btn" onClick={() => setShowAddPanel(false)}>✕</button>
            </div>
            <div className="add-panel-content">
              {loadingRecs ? (
                <p>Loading recommendations...</p>
              ) : recommendations.length > 0 ? (
                recommendations.map((rec) => (
                  <div key={rec.track_id || rec.id} className="rec-track">
                    <div className="rec-info">
                      <span className="rec-title">{rec.title || rec.name}</span>
                      <span className="rec-artist">{rec.artist || rec.artists?.[0]?.name || 'Unknown'}</span>
                    </div>
                    <button className="add-track-btn" onClick={() => handleAddTrack(rec)}>+</button>
                  </div>
                ))
              ) : (
                <p>No recommendations available.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {confirmDeletePlaylist && (
        <div className="modal-overlay">
          <div className="confirmation-modal">
            <h3>Delete Playlist?</h3>
            <p>Are you sure you want to delete "{playlist.name}"? This action cannot be undone.</p>
            <div className="modal-actions">
              <button className="cancel-btn" onClick={() => setConfirmDeletePlaylist(false)}>Cancel</button>
              <button className="confirm-btn" onClick={handleDeletePlaylist}>Delete</button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
