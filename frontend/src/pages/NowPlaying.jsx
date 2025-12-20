import React from 'react';
import { usePlayer } from '../context/PlayerContext';
import '../styles/NowPlaying.css';

export default function NowPlaying() {
  const { current, queue, currentIndex } = usePlayer();
  return (
    <main className="np-main">
      <h1>Now Playing</h1>
      {current ? (
        <div className="np-current">
          {current.cover_url ? (
            <img src={current.cover_url} alt={current.title} />
          ) : (
            <div className="np-cover">🎵</div>
          )}
          <div className="np-meta">
            <h2>{current.title}</h2>
            <p>{current.artist}</p>
          </div>
        </div>
      ) : (
        <p>Pick something from your Library or Playlist.</p>
      )}

      <div className="np-queue">
        <h3>Queue</h3>
        {queue.length ? (
          queue.map((t, i) => (
            <div key={`${t.id}-${i}`} className={`np-queue-item ${i === currentIndex ? 'active' : ''}`}>
              <span>{t.title}</span>
              <span className="by">{t.artist}</span>
            </div>
          ))
        ) : (
          <p>Queue is empty.</p>
        )}
      </div>
    </main>
  );
}
