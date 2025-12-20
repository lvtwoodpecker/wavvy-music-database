import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { playlistService } from '../services/playlistService';
import '../styles/Playlists.css';

export default function Playlists() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [playlists, setPlaylists] = useState([]);
  const [name, setName] = useState('New Playlist');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await playlistService.listPlaylists(token);
      setPlaylists(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const onCreate = async () => {
    try {
      const pl = await playlistService.createPlaylist(token, { name });
      navigate(`/playlist/${pl.id}`);
    } catch (e) {
      setError(e.message);
    }
  };

  const handleDeletePlaylist = async (pl) => {
    try {
      await playlistService.deletePlaylist(token, pl.id);
      setConfirmDelete(null);
      await load();
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <main className="pls-main">
      <div className="pls-header">
        <h1>My Playlists</h1>
        <div className="create">
          <input value={name} onChange={(e) => setName(e.target.value)} />
          <button onClick={onCreate}>Create</button>
        </div>
      </div>
      {loading ? (
        <p>Loading…</p>
      ) : error ? (
        <p className="error">{error}</p>
      ) : (
        <div className="pls-list">
          {playlists.map(pl => (
            <div key={pl.id} className="pls-item">
              <div className="pls-content" onClick={() => navigate(`/playlist/${pl.id}`)}>
                <div className="cover" style={{ fontSize: '14px', fontWeight: '700' }}>PL</div>
                <div className="meta">
                  <div className="title">{pl.name}</div>
                  <div className="sub">{pl.track_count || 0} tracks</div>
                </div>
              </div>
              {!pl.is_public && (
                <button className="delete-icon" onClick={(e) => { e.stopPropagation(); setConfirmDelete(pl); }} title="Delete playlist">✕</button>
              )}
            </div>
          ))}
          {playlists.length === 0 && <p>No playlists yet — create one!</p>}
        </div>
      )}

      {confirmDelete && (
        <div className="modal-overlay">
          <div className="confirmation-modal">
            <h3>Delete Playlist?</h3>
            <p>Are you sure you want to delete "{confirmDelete.name}"? This action cannot be undone.</p>
            <div className="modal-actions">
              <button className="cancel-btn" onClick={() => setConfirmDelete(null)}>Cancel</button>
              <button className="confirm-btn" onClick={() => handleDeletePlaylist(confirmDelete)}>Delete</button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
