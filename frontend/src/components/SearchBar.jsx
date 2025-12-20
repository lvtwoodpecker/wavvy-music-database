// SearchBar component for track/song searching
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { searchService } from '../services/searchService';
import { useAuth } from '../context/AuthContext';
import { usePlayer } from '../context/PlayerContext';
import '../styles/SearchBar.css';

function SearchBar() {
  const { token } = useAuth();
  const { playTrack } = usePlayer();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [error, setError] = useState(null);
  const searchTimeoutRef = useRef(null);
  const searchContainerRef = useRef(null);

  // Debounced search function
  const performSearch = useCallback(async (searchQuery) => {
    if (!searchQuery || searchQuery.trim().length === 0) {
      setResults([]);
      setShowResults(false);
      return;
    }

    setIsSearching(true);
    setError(null);

    try {
      const data = await searchService.searchTracks(searchQuery, token, 10);
      setResults(data.results || []);
      setShowResults(true);
    } catch (err) {
      console.error('Search failed:', err);
      setError('Search failed. Please try again.');
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  }, [token]);

  // Handle input change with debouncing
  const handleInputChange = (e) => {
    const value = e.target.value;
    setQuery(value);

    // Clear existing timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Set new timeout for debounced search
    if (value.trim().length > 0) {
      searchTimeoutRef.current = setTimeout(() => {
        performSearch(value);
      }, 300); // 300ms debounce
    } else {
      setResults([]);
      setShowResults(false);
    }
  };

  // Handle track play
  const handlePlayTrack = (track) => {
    if (!track.audio_file_url) {
      console.warn('Track does not have an audio file URL:', track);
      return;
    }

    // Convert search result to track format expected by player
    const playerTrack = {
      id: track.track_id,
      title: track.track_title,
      artist: track.artist_names,
      album: track.album_titles,
      audio_url: track.audio_file_url,
    };
    
    playTrack(playerTrack, { replace: false });
    setShowResults(false);
    setQuery('');
  };

  // Close results when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  const handleClearSearch = () => {
    setQuery('');
    setResults([]);
    setShowResults(false);
    setError(null);
  };

  return (
    <div className="search-bar-container" ref={searchContainerRef}>
      <div className="search-input-wrapper">
        <span className="search-icon" aria-hidden="true">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </span>

        <input
          type="text"
          className="search-input"
          placeholder="Search for songs, artists, or albums..."
          value={query}
          onChange={handleInputChange}
          onFocus={() => query && results.length > 0 && setShowResults(true)}
        />
        {query && (
          <button 
          className="clear-search-btn" 
          onClick={handleClearSearch}
          type="button"
          aria-label="Clear search"
          >
            ✕
          </button>
        )}
        {isSearching && <span className="search-loader">⏳</span>}
      </div>

      {showResults && (
        <div className="search-results-dropdown">
          {error && (
            <div className="search-error">{error}</div>
          )}
          
          {!error && results.length === 0 && !isSearching && (
            <div className="no-results">No tracks found for "{query}"</div>
          )}

          {!error && results.length > 0 && (
            <div className="results-list">
              {results.map((track) => (
                <div
                  key={track.track_id}
                  className="result-item"
                  onClick={() => handlePlayTrack(track)}
                >
                  <div className="result-info">
                    <div className="result-title">{track.track_title}</div>
                    <div className="result-meta">
                      {track.artist_names && <span className="result-artist">{track.artist_names}</span>}
                      {track.artist_names && track.album_titles && <span className="result-separator">•</span>}
                      {track.album_titles && <span className="result-album">{track.album_titles}</span>}
                    </div>

                    </div>

                    {track.audio_file_url ? (
                      <button
                        className="result-play-btn"
                        aria-label={`Play ${track.track_title}`}
                        onClick={() => playTrack(track.audio_file_url)}
                      >
                        <span className="play-icon" />
                      </button>
                    ) : (
                      <button
                        className="result-play-btn disabled"
                        aria-label={`No audio available for ${track.track_title}`}
                        disabled
                      >
                        <span className="play-icon disabled" />
                      </button>
                    )}

                    </div>

              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SearchBar;
