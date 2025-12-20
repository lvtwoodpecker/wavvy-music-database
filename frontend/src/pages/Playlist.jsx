import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { usePlayer } from '../context/PlayerContext';
import { playlistService } from '../services/playlistService';
import '../styles/Playlist.css';

export default function PlaylistPage() {
  const { id } = useParams();
  const { token } = useAuth();
  const { playTrack } = usePlayer();
  const [playlist, setPlaylist] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  const onAddDemo = async () => {
    try {
      await playlistService.addTrack(token, id, {
        title: 'Wavvy Waves',
        artist: 'Wavvy',
        audio_url: 'https://cdn.pixabay.com/download/audio/2022/03/15/audio_e32846d7d8.mp3?filename=chill-ambient-110387.mp3',
        cover_url: 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=256&auto=format&fit=crop',
        duration_ms: 120000,
      });
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
      <div className="pl-header">
        <div className="pl-cover">🎵</div>
        <div>
          <h1>{playlist.name}</h1>
          {playlist.description && <p>{playlist.description}</p>}
          <button onClick={onAddDemo}>Add Demo Track</button>
        </div>
      </div>
      <div className="pl-tracks">
        {playlist.tracks?.length ? (
          playlist.tracks.map((t) => (
            <div key={t.id} className="pl-track" onClick={() => playTrack(t)}>
              <span className="idx">{t.position + 1}</span>
              <span className="title">{t.title}</span>
              <span className="artist">{t.artist}</span>
            </div>
          ))
        ) : (
          <p>No tracks yet.</p>
        )}
      </div>
    </main>
  );
}
