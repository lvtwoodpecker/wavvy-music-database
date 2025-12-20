<<<<<<< HEAD
=======
import React, { createContext, useContext, useMemo, useRef, useState, useEffect } from 'react';
import { playHistoryService } from '../services/playHistoryService';
import { useAuth } from './AuthContext';

const PlayerContext = createContext(null);

export function PlayerProvider({ children }) {
  const { token } = useAuth();
  const audioRef = useRef(null);
  const [queue, setQueue] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [volume, setVolume] = useState(0.9);
  const playTrackedRef = useRef(new Set()); // Track which songs have been logged

  const current = currentIndex >= 0 ? queue[currentIndex] : null;

  useEffect(() => {
    if (!audioRef.current) return;
    audioRef.current.volume = volume;
  }, [volume]);

  useEffect(() => {
    if (!audioRef.current) return;
    const onTime = () => setProgress(audioRef.current.currentTime || 0);
    const onEnded = () => next();
    const el = audioRef.current;
    el.addEventListener('timeupdate', onTime);
    el.addEventListener('ended', onEnded);
    return () => {
      el.removeEventListener('timeupdate', onTime);
      el.removeEventListener('ended', onEnded);
    };
  }, [currentIndex, queue]);

  // When the current track changes, update the audio source and optionally play
  useEffect(() => {
    if (!audioRef.current) return;
    console.log('Setting audio source:', current?.title || 'none', current?.audio_url || 'no url');
    audioRef.current.src = current?.audio_url || '';
    if (current && isPlaying) {
      audioRef.current.play().catch(err => {
        console.error('Play failed:', err);
        setIsPlaying(false);
      });
    } else {
      audioRef.current.pause();
    }
    setProgress(0);
  }, [current]);

  useEffect(() => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.play().catch(() => setIsPlaying(false));
    } else {
      audioRef.current.pause();
    }
  }, [isPlaying, currentIndex]);

  // Track play after 10 seconds
  useEffect(() => {
    if (!current || !isPlaying || !token) return;
    
    const trackKey = `${current.id || current.track_id}_${currentIndex}`;
    if (playTrackedRef.current.has(trackKey)) return;
    
    const timeout = setTimeout(() => {
      if (audioRef.current && audioRef.current.currentTime >= 10) {
        playHistoryService.trackPlay(token, current.id || current.track_id);
        playTrackedRef.current.add(trackKey);
        console.log('Tracked play for:', current.title);
      }
    }, 10000); // 10 seconds
    
    return () => clearTimeout(timeout);
  }, [current, isPlaying, currentIndex, token]);

  // Reset tracking when track changes
  useEffect(() => {
    // Clean up old tracking data (keep last 20 tracks)
    if (playTrackedRef.current.size > 20) {
      playTrackedRef.current.clear();
    }
  }, [currentIndex]);

  const playTrack = (track, options = { replace: false }) => {
    setQueue(prev => {
      if (options.replace) {
        setCurrentIndex(0);
        return [track];
      }
      const existingIdx = prev.findIndex(t => t.id === track.id && t.audio_url === track.audio_url);
      if (existingIdx !== -1) {
        setCurrentIndex(existingIdx);
        return prev;
      }
      setCurrentIndex(prev.length);
      return [...prev, track];
    });
    setIsPlaying(true);
  };

  const playTracks = (tracks) => {
    if (!tracks || tracks.length === 0) {
      console.warn('playTracks called with empty tracks');
      return;
    }
    console.log('Playing tracks:', tracks.map(t => ({ title: t.title, hasAudio: !!t.audio_url })));
    setQueue(tracks);
    setCurrentIndex(0);
    setIsPlaying(true);
  };

  const play = () => setIsPlaying(true);
  const pause = () => setIsPlaying(false);
  const toggle = () => setIsPlaying(p => !p);

  const seek = (seconds) => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = seconds;
    setProgress(seconds);
  };

  const next = () => {
    setCurrentIndex(idx => {
      if (idx < 0) return -1;
      const ni = idx + 1;
      if (ni < queue.length) return ni;
      return idx; // end of queue: stay
    });
    setIsPlaying(true);
  };

  const prev = () => {
    setCurrentIndex(idx => (idx > 0 ? idx - 1 : idx));
    setIsPlaying(true);
  };

  const value = useMemo(() => ({
    audioRef,
    queue,
    current,
    currentIndex,
    isPlaying,
    progress,
    volume,
    setVolume,
    playTrack,
    playTracks,
    play,
    pause,
    toggle,
    next,
    prev,
    seek,
    setQueue,
    setCurrentIndex,
  }), [queue, current, currentIndex, isPlaying, progress, volume]);

  return (
    <PlayerContext.Provider value={value}>
      {/* hidden audio element - src set via useEffect */}
      <audio ref={audioRef} preload="metadata" crossOrigin="anonymous" />
      {children}
    </PlayerContext.Provider>
  );
}

export function usePlayer() {
  const ctx = useContext(PlayerContext);
  if (!ctx) throw new Error('usePlayer must be used within PlayerProvider');
  return ctx;
}
>>>>>>> a26026be19ebc256ead4b45831ff6cedfc8ed287
