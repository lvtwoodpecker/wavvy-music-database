import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { usePlayer } from '../context/PlayerContext';
import { musicService } from '../services/musicService';
import '../styles/Library.css';

export default function Library() {
  const { token } = useAuth();
  const { playTracks } = usePlayer();
  const navigate = useNavigate();
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

  const handleCardClick = (e, album) => {
    if (e.target.closest('.lib-play-btn')) {
      playTracks(album.tracks);
    } else {
      navigate(`/album/${encodeURIComponent(album.album)}`, { state: { album } });
    }
  };

  if (loading) return <main className="lib-main"><p>Loading your Wavvy Library…</p></main>;

  return (
    <main className="lib-main">
      <h1>Library</h1>
      <div className="lib-grid">
        {albums.map((album) => (

      <div
        key={album.album}
        className="lib-card"
        onClick={(e) => handleCardClick(e, album)}
      >
        <div className="lib-card-inner">
          {/* FRONT */}
          <div className="lib-card-face lib-card-front">
            {album.cover_url ? (
              <img src={album.cover_url} alt={album.album} />
            ) : (
              <div className="lib-cover-fallback">🎵</div>
            )}
            <div className="lib-front-title">
              {album.album}
            </div>
          </div>

          {/* BACK */}
          <div className="lib-card-face lib-card-back">
            <div className="meta">
              <div className="title">{album.album}</div>
              <div className="artist">{album.artist}</div>
              <div className="count">{album.tracks.length} tracks</div>
              <button
                className="lib-play-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  playTracks(album.tracks);
                }}
                hidden
              >
              </button>
            </div>
          </div>
        </div>
      </div>

        ))}
      </div>
    </main>
  );
}
