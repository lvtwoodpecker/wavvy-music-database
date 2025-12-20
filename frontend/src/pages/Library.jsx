import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { usePlayer } from '../context/PlayerContext';
import { musicService } from '../services/musicService';
import '../styles/Library.css';

export default function Library() {
  const { token } = useAuth();
  const { playTracks } = usePlayer();
  const [albums, setAlbums] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const data = await musicService.getLibrary(token);
      setAlbums(data);
      setLoading(false);
    })();
  }, [token]);

  if (loading) return <main className="lib-main"><p>Loading your Wavvy Library…</p></main>;

  return (
    <main className="lib-main">
      <h1>Library</h1>
      <div className="lib-grid">
        {albums.map((album) => (
          <div key={album.album} className="lib-card" onClick={() => playTracks(album.tracks)}>
            {album.cover_url ? (
              <img src={album.cover_url} alt={album.album} />
            ) : (
              <div className="lib-cover-fallback">🎵</div>
            )}
            <div className="meta">
              <div className="title">{album.album}</div>
              <div className="artist">{album.artist}</div>
              <div className="count">{album.tracks.length} tracks</div>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
