"""
ReccoBeats API service for fetching audio features.
ReccoBeats is a free API that provides audio features for tracks using Spotify track IDs.
"""
import requests
import time
from typing import Optional, Dict
from app.services.audio.spotify_service import get_spotify_token, fetch_spotify_api


class ReccoBeatsService:
    """Service for interacting with ReccoBeats API."""
    
    BASE_URL = "https://api.reccobeats.com"
    
    @staticmethod
    def get_spotify_track_id(track_title: str, artist_name: Optional[str] = None, 
                             duration_ms: Optional[int] = None) -> Optional[str]:
        """
        Search Spotify API to get track ID, which we can then use with ReccoBeats.
        
        Args:
            track_title: Track title
            artist_name: Optional artist name for better matching
            duration_ms: Optional duration in milliseconds for better matching
        
        Returns:
            Spotify track ID or None if not found
        """
        try:
            token = get_spotify_token()
            
            # Build search query
            if artist_name:
                query = f"track:{track_title} artist:{artist_name}"
            else:
                query = f"track:{track_title}"
            
            # Search Spotify
            search_data = fetch_spotify_api(f"search?q={query}&type=track&limit=5", token)
            
            if not search_data or 'tracks' not in search_data or 'items' not in search_data['tracks']:
                return None
            
            tracks = search_data['tracks']['items']
            
            if not tracks:
                return None
            
            # If we have duration, try to match it
            if duration_ms:
                for track in tracks:
                    # Allow 2 second tolerance
                    if abs(track.get('duration_ms', 0) - duration_ms) <= 2000:
                        return track['id']
            
            # Return first match
            return tracks[0]['id']
            
        except Exception as e:
            print(f"    > Error searching Spotify: {e}")
            return None
    
    @staticmethod
    def get_audio_features(spotify_track_id: str) -> Optional[Dict]:
        """
        Fetch audio features from ReccoBeats API using /v1/audio-features endpoint.
        Documentation: https://reccobeats.com/docs/apis/get-audio-features
        
        Args:
            spotify_track_id: Spotify track ID (e.g., "7mcPmdy1XIJoQvD30saXPt")
        
        Returns:
            Dictionary with audio features or None if not found
            Features include: tempo, loudness, danceability, energy, valence, acousticness
        """
        endpoint = f"{ReccoBeatsService.BASE_URL}/v1/audio-features"
        params = {"ids": spotify_track_id}
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # ReccoBeats returns: {"content": [{"id": "...", "tempo": ..., ...}]}
                if isinstance(data, dict) and 'content' in data:
                    content = data['content']
                    if isinstance(content, list) and len(content) > 0:
                        track_data = content[0]
                        
                        # Extract features
                        features = {}
                        
                        # Tempo
                        tempo = track_data.get('tempo')
                        if tempo:
                            try:
                                features['tempo'] = float(tempo)
                            except (ValueError, TypeError):
                                pass
                        
                        # Loudness
                        loudness = track_data.get('loudness')
                        if loudness is not None:
                            try:
                                features['loudness'] = float(loudness)
                            except (ValueError, TypeError):
                                pass
                        
                        # Danceability (0-1 scale)
                        danceability = track_data.get('danceability')
                        if danceability is not None:
                            try:
                                features['danceability'] = float(danceability)
                            except (ValueError, TypeError):
                                pass
                        
                        # Energy (0-1 scale)
                        energy = track_data.get('energy')
                        if energy is not None:
                            try:
                                features['energy'] = float(energy)
                            except (ValueError, TypeError):
                                pass
                        
                        # Valence (0-1 scale)
                        valence = track_data.get('valence')
                        if valence is not None:
                            try:
                                features['valence'] = float(valence)
                            except (ValueError, TypeError):
                                pass
                        
                        # Acousticness (0-1 scale)
                        acousticness = track_data.get('acousticness')
                        if acousticness is not None:
                            try:
                                features['acousticness'] = float(acousticness)
                            except (ValueError, TypeError):
                                pass
                        
                        # Return features if we got at least tempo
                        if 'tempo' in features:
                            if 'loudness' not in features:
                                features['loudness'] = -10.0  # Default
                            return features
            
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise Exception(f"Rate limited. Wait {retry_after} seconds")
            elif response.status_code == 400:
                # Bad request - might be invalid track ID
                return None
            else:
                return None
        
        except requests.exceptions.Timeout:
            return None
        except requests.exceptions.RequestException as e:
            if "Rate limited" in str(e):
                raise
            return None
        except Exception as e:
            if "Rate limited" in str(e):
                raise
            return None
    
    @staticmethod
    def get_audio_features_for_track(track_title: str, artist_name: Optional[str] = None,
                                     duration_ms: Optional[int] = None,
                                     spotify_track_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get audio features for a track by searching Spotify first if needed.
        
        Args:
            track_title: Track title
            artist_name: Optional artist name for better matching
            duration_ms: Optional duration in milliseconds for better matching
            spotify_track_id: Optional Spotify track ID if already known
        
        Returns:
            Dictionary with audio features or None if not found
        """
        # If we don't have Spotify track ID, search for it first
        if not spotify_track_id:
            spotify_track_id = ReccoBeatsService.get_spotify_track_id(
                track_title, artist_name, duration_ms
            )
            if not spotify_track_id:
                return None
        
        # Get audio features using the Spotify track ID
        return ReccoBeatsService.get_audio_features(spotify_track_id)


# Create a singleton instance for convenience
reccobeats_service = ReccoBeatsService()

