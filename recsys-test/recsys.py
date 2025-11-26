"""
Content-based filtering recommendation system using K-Nearest Neighbors.
Uses audio features, genres, and listening patterns to recommend tracks.
Optimized for performance with batch queries and caching.
"""
import sys
import os
import numpy as np
from typing import List, Dict, Optional, Set
from collections import defaultdict
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.supabase_client import supabase


class ContentBasedRecommender:
    """Content-based filtering recommender using K-NN with audio features and genres."""
    
    def __init__(self, n_neighbors: int = 10, metric: str = 'cosine'):
        """
        Initialize the recommender.
        
        Args:
            n_neighbors: Number of neighbors to consider for K-NN
            metric: Distance metric ('cosine', 'euclidean', 'manhattan')
        """
        if not supabase:
            raise Exception("Supabase client not initialized")
        self._feature_cache = {}  # Cache track features to avoid repeated queries
        self.n_neighbors = n_neighbors
        self.metric = metric
        self.scaler = StandardScaler()
    
    def _get_track_features(self, track_id: int) -> Optional[Dict]:
        """Get all features for a track (audio features + genres), with caching."""
        if track_id in self._feature_cache:
            return self._feature_cache[track_id]
        
        # Get audio features
        af_response = supabase.from_("AudioFeatures").select("*").eq("track_id", track_id).limit(1).execute()
        audio_features = af_response.data[0] if af_response.data else None
        
        # Get genres
        tg_response = supabase.from_("TrackGenre").select("genre_id").eq("track_id", track_id).execute()
        genre_ids = [tg['genre_id'] for tg in tg_response.data] if tg_response.data else []
        
        # Get genre names
        genres = []
        if genre_ids:
            genre_response = supabase.from_("Genre").select("genre_id, name").in_("genre_id", genre_ids).execute()
            if genre_response.data:
                genres = [g['name'] for g in genre_response.data]
        
        features = {
            'audio_features': audio_features,
            'genres': genres
        }
        
        self._feature_cache[track_id] = features
        return features
    
    def _build_feature_vector(self, features: Dict, genre_encoding: Dict[str, int] = None) -> Optional[np.ndarray]:
        """
        Build feature vector from track features.
        Includes audio features and genre encoding.
        
        Args:
            features: Track features dict with audio_features and genres
            genre_encoding: Optional dict mapping genre names to indices for one-hot encoding
        """
        af = features.get('audio_features')
        if not af:
            return None
        
        # Audio feature vector: [tempo, loudness, danceability, energy, valence, acousticness]
        tempo = af.get('tempo', 120) or 120
        loudness = af.get('loudness', -10) or -10
        danceability = af.get('danceability', 0.5) or 0.5
        energy = af.get('energy', 0.5) or 0.5
        valence = af.get('valence', 0.5) or 0.5
        acousticness = af.get('acousticness', 0.5) or 0.5
        
        feature_vec = [tempo, loudness, danceability, energy, valence, acousticness]
        
        # Add genre encoding if provided
        if genre_encoding:
            genres = features.get('genres', [])
            genre_vec = [0.0] * len(genre_encoding)
            for genre in genres:
                if genre in genre_encoding:
                    genre_vec[genre_encoding[genre]] = 1.0
            feature_vec.extend(genre_vec)
        
        return np.array(feature_vec)
    
    def _build_feature_matrix(self, track_features_map: Dict[int, Dict], genre_encoding: Dict[str, int] = None) -> tuple:
        """
        Build feature matrix from track features map.
        
        Returns:
            (feature_matrix, track_ids) tuple
        """
        feature_vectors = []
        track_ids = []
        
        for track_id, features in track_features_map.items():
            vec = self._build_feature_vector(features, genre_encoding)
            if vec is not None:
                feature_vectors.append(vec)
                track_ids.append(track_id)
        
        if not feature_vectors:
            return None, []
        
        return np.array(feature_vectors), track_ids
    
    
    def _get_playlist_tracks(self, playlist_id: int) -> List[Dict]:
        """Get all tracks in a playlist."""
        pt_response = supabase.from_("PlaylistTrack").select(
            "track_id, date_added"
        ).eq("playlist_id", playlist_id).is_("date_removed", "null").execute()
        
        if not pt_response.data:
            return []
        
        track_ids = [pt['track_id'] for pt in pt_response.data]
        tracks_response = supabase.from_("Track").select("*").in_("track_id", track_ids).execute()
        
        if not tracks_response.data:
            return []
        
        # Create a map for quick lookup
        track_map = {t['track_id']: t for t in tracks_response.data}
        
        tracks = []
        for pt in pt_response.data:
            track_id = pt['track_id']
            if track_id in track_map:
                tracks.append({
                    'track': track_map[track_id],
                    'date_added': pt['date_added']
                })
        
        return tracks
    
    def _get_user_history_tracks(self, listener_id: str, limit: int = 100) -> List[Dict]:
        """Get user's listening history tracks."""
        ph_response = supabase.from_("PlayHistory").select(
            "track_id, played_at"
        ).eq("listener_id", listener_id).order("played_at", desc=True).limit(limit).execute()
        
        if not ph_response.data:
            return []
        
        track_ids = [ph['track_id'] for ph in ph_response.data]
        tracks_response = supabase.from_("Track").select("*").in_("track_id", track_ids).execute()
        
        if not tracks_response.data:
            return []
        
        # Create a map for quick lookup
        track_map = {t['track_id']: t for t in tracks_response.data}
        
        tracks = []
        for ph in ph_response.data:
            track_id = ph['track_id']
            if track_id in track_map:
                tracks.append({
                    'track': track_map[track_id],
                    'played_at': ph['played_at']
                })
        
        return tracks
    
    
    def _batch_get_track_features(self, track_ids: List[int]) -> Dict[int, Dict]:
        """Batch fetch features for multiple tracks to reduce database queries."""
        if not track_ids:
            return {}
        
        features_map = {}
        
        # Batch get audio features
        af_response = supabase.from_("AudioFeatures").select("*").in_("track_id", track_ids).execute()
        audio_features_map = {af['track_id']: af for af in (af_response.data or [])}
        
        # Batch get track genres
        tg_response = supabase.from_("TrackGenre").select("track_id, genre_id").in_("track_id", track_ids).execute()
        track_genre_map = defaultdict(list)
        if tg_response.data:
            for tg in tg_response.data:
                track_genre_map[tg['track_id']].append(tg['genre_id'])
        
        # Batch get genre names
        all_genre_ids = set()
        for genre_ids in track_genre_map.values():
            all_genre_ids.update(genre_ids)
        
        genre_map = {}
        if all_genre_ids:
            genre_response = supabase.from_("Genre").select("genre_id, name").in_("genre_id", list(all_genre_ids)).execute()
            if genre_response.data:
                genre_map = {g['genre_id']: g['name'] for g in genre_response.data}
        
        # Build features for each track
        for track_id in track_ids:
            audio_features = audio_features_map.get(track_id)
            genre_ids = track_genre_map.get(track_id, [])
            genres = [genre_map[gid] for gid in genre_ids if gid in genre_map]
            
            features = {
                'audio_features': audio_features,
                'genres': genres
            }
            features_map[track_id] = features
            self._feature_cache[track_id] = features
        
        return features_map
    
    def _recommend_by_genre(self, genre_ids: List[int], exclude_track_ids: Set[int], n_recommendations: int) -> List[Dict]:
        """Recommend tracks by genre when audio features are not available."""
        if not genre_ids:
            return []
        
        # Find tracks with matching genres (batch query)
        track_ids_set = set()
        for genre_id in genre_ids:
            tg_response = supabase.from_("TrackGenre").select("track_id").eq("genre_id", genre_id).limit(100).execute()
            if tg_response.data:
                for tg in tg_response.data:
                    track_id = tg['track_id']
                    if track_id not in exclude_track_ids:
                        track_ids_set.add(track_id)
                    if len(track_ids_set) >= n_recommendations * 2:  # Get extra for filtering
                        break
            if len(track_ids_set) >= n_recommendations * 2:
                break
        
        if not track_ids_set:
            return []
        
        # Batch fetch tracks
        track_ids_list = list(track_ids_set)[:n_recommendations * 2]
        tracks_response = supabase.from_("Track").select("track_id, title").in_("track_id", track_ids_list).execute()
        
        if not tracks_response.data:
            return []
        
        recommendations = []
        for track in tracks_response.data[:n_recommendations]:
            track_id = track['track_id']
            features = self._get_track_features(track_id)
            recommendations.append({
                'track_id': track_id,
                'title': track['title'],
                'similarity': 0.5,  # Default similarity for genre-based
                'features': features or {}
            })
        
        return recommendations
    
    def recommend_for_playlist(self, playlist_id: int, n_recommendations: int = 10) -> List[Dict]:
        """
        Recommend tracks for a playlist using K-NN based on existing tracks.
        
        Args:
            playlist_id: Database playlist_id
            n_recommendations: Number of recommendations to return
        
        Returns:
            List of recommended tracks with similarity scores
        """
        # Get playlist tracks
        playlist_tracks = self._get_playlist_tracks(playlist_id)
        
        if not playlist_tracks:
            return []
        
        playlist_track_ids = {item['track']['track_id'] for item in playlist_tracks}
        playlist_track_ids_list = list(playlist_track_ids)
        
        # Batch get features for all playlist tracks
        playlist_features_map = self._batch_get_track_features(playlist_track_ids_list)
        
        # Filter to only tracks with audio features
        playlist_features = {tid: feat for tid, feat in playlist_features_map.items() 
                           if feat.get('audio_features')}
        
        if not playlist_features:
            # Fallback: recommend by genre
            playlist_genre_ids = set()
            for track_id in playlist_track_ids_list:
                features = playlist_features_map.get(track_id, {})
                if features.get('genres'):
                    tg_response = supabase.from_("TrackGenre").select("genre_id").eq("track_id", track_id).execute()
                    if tg_response.data:
                        playlist_genre_ids.update([tg['genre_id'] for tg in tg_response.data])
            
            if playlist_genre_ids:
                return self._recommend_by_genre(list(playlist_genre_ids), playlist_track_ids, n_recommendations)
            return []
        
        # Get all candidate tracks with audio features
        af_tracks_response = supabase.from_("AudioFeatures").select("track_id").execute()
        candidate_track_ids = [af['track_id'] for af in (af_tracks_response.data or []) 
                             if af['track_id'] not in playlist_track_ids]
        
        if not candidate_track_ids:
            return []
        
        # Batch get features for candidates (limit to reasonable number)
        max_candidates = min(1000, len(candidate_track_ids))
        candidate_features_map = self._batch_get_track_features(candidate_track_ids[:max_candidates])
        candidate_features = {tid: feat for tid, feat in candidate_features_map.items() 
                            if feat.get('audio_features')}
        
        if not candidate_features:
            return []
        
        # Build genre encoding from all genres in playlist and candidates
        all_genres = set()
        for features in list(playlist_features.values()) + list(candidate_features.values()):
            all_genres.update(features.get('genres', []))
        genre_encoding = {genre: idx for idx, genre in enumerate(sorted(all_genres))}
        
        # Build feature matrices
        playlist_matrix, playlist_ids = self._build_feature_matrix(playlist_features, genre_encoding)
        candidate_matrix, candidate_ids = self._build_feature_matrix(candidate_features, genre_encoding)
        
        if playlist_matrix is None or candidate_matrix is None or len(playlist_matrix) == 0:
            return []
        
        # Standardize features
        all_features = np.vstack([playlist_matrix, candidate_matrix])
        all_features_scaled = self.scaler.fit_transform(all_features)
        playlist_scaled = all_features_scaled[:len(playlist_matrix)]
        candidate_scaled = all_features_scaled[len(playlist_matrix):]
        
        # Use K-NN to find nearest neighbors
        # Fit on playlist tracks, find neighbors in candidates
        knn = NearestNeighbors(n_neighbors=min(self.n_neighbors, len(candidate_scaled)), 
                              metric=self.metric, algorithm='brute')
        knn.fit(candidate_scaled)
        
        # Get average feature vector of playlist tracks
        playlist_avg = np.mean(playlist_scaled, axis=0).reshape(1, -1)
        
        # Find nearest neighbors
        distances, indices = knn.kneighbors(playlist_avg, n_neighbors=min(n_recommendations, len(candidate_ids)))
        
        # Build recommendations
        recommendations = []
        for idx, dist in zip(indices[0], distances[0]):
            track_id = candidate_ids[idx]
            track_response = supabase.from_("Track").select("track_id, title").eq("track_id", track_id).limit(1).execute()
            if track_response.data:
                # Convert distance to similarity (closer = higher similarity)
                similarity = 1.0 / (1.0 + dist) if dist > 0 else 1.0
                recommendations.append({
                    'track_id': track_id,
                    'title': track_response.data[0]['title'],
                    'similarity': similarity,
                    'features': candidate_features[track_id]
                })
        
        return recommendations
    
    def recommend_for_user(self, listener_id: str, n_recommendations: int = 10) -> List[Dict]:
        """
        Recommend tracks based on user's listening history using K-NN.
        
        Args:
            listener_id: Database listener_id (UUID)
            n_recommendations: Number of recommendations to return
        
        Returns:
            List of recommended tracks with similarity scores
        """
        # Get user's recent listening history (exclude these from recommendations)
        recent_history = self._get_user_history_tracks(listener_id, limit=10)
        recent_track_ids = {item['track']['track_id'] for item in recent_history}
        
        # Get broader listening history for features
        history_tracks = self._get_user_history_tracks(listener_id, limit=50)
        
        if not history_tracks:
            return []
        
        history_track_ids_list = [item['track']['track_id'] for item in history_tracks]
        all_history_track_ids = set(history_track_ids_list)
        
        # Batch get features for history tracks
        history_features_map = self._batch_get_track_features(history_track_ids_list)
        
        # Filter to only tracks with audio features
        history_features = {tid: feat for tid, feat in history_features_map.items() 
                          if feat.get('audio_features')}
        
        if not history_features:
            # Fallback 1: recommend by genre
            history_genre_ids = set()
            if history_track_ids_list:
                tg_response = supabase.from_("TrackGenre").select("track_id, genre_id").in_("track_id", history_track_ids_list).execute()
                if tg_response.data:
                    history_genre_ids.update([tg['genre_id'] for tg in tg_response.data])
            
            if history_genre_ids:
                genre_recommendations = self._recommend_by_genre(
                    list(history_genre_ids),
                    recent_track_ids,
                    n_recommendations
                )
                if genre_recommendations:
                    return genre_recommendations
            
            # Fallback 2: recommend from past listening history
            if len(all_history_track_ids) > len(recent_track_ids):
                past_track_ids = list(all_history_track_ids - recent_track_ids)[:n_recommendations]
                tracks_response = supabase.from_("Track").select("track_id, title").in_("track_id", past_track_ids).execute()
                
                if tracks_response.data:
                    recommendations = []
                    for track in tracks_response.data:
                        track_id = track['track_id']
                        features = self._get_track_features(track_id)
                        recommendations.append({
                            'track_id': track_id,
                            'title': track['title'],
                            'similarity': 0.3,
                            'features': features or {}
                        })
                    return recommendations
            return []
        
        # Get all candidate tracks with audio features
        af_tracks_response = supabase.from_("AudioFeatures").select("track_id").execute()
        candidate_track_ids = [af['track_id'] for af in (af_tracks_response.data or []) 
                             if af['track_id'] not in recent_track_ids]
        
        if not candidate_track_ids:
            return []
        
        # Batch get features for candidates
        max_candidates = min(1000, len(candidate_track_ids))
        candidate_features_map = self._batch_get_track_features(candidate_track_ids[:max_candidates])
        candidate_features = {tid: feat for tid, feat in candidate_features_map.items() 
                            if feat.get('audio_features')}
        
        if not candidate_features:
            return []
        
        # Build genre encoding from all genres in history and candidates
        all_genres = set()
        for features in list(history_features.values()) + list(candidate_features.values()):
            all_genres.update(features.get('genres', []))
        genre_encoding = {genre: idx for idx, genre in enumerate(sorted(all_genres))}
        
        # Build feature matrices
        history_matrix, history_ids = self._build_feature_matrix(history_features, genre_encoding)
        candidate_matrix, candidate_ids = self._build_feature_matrix(candidate_features, genre_encoding)
        
        if history_matrix is None or candidate_matrix is None or len(history_matrix) == 0:
            return []
        
        # Standardize features
        all_features = np.vstack([history_matrix, candidate_matrix])
        all_features_scaled = self.scaler.fit_transform(all_features)
        history_scaled = all_features_scaled[:len(history_matrix)]
        candidate_scaled = all_features_scaled[len(history_matrix):]
        
        # Use K-NN to find nearest neighbors
        knn = NearestNeighbors(n_neighbors=min(self.n_neighbors, len(candidate_scaled)), 
                              metric=self.metric, algorithm='brute')
        knn.fit(candidate_scaled)
        
        # Get average feature vector of history tracks
        history_avg = np.mean(history_scaled, axis=0).reshape(1, -1)
        
        # Find nearest neighbors
        distances, indices = knn.kneighbors(history_avg, n_neighbors=min(n_recommendations, len(candidate_ids)))
        
        # Build recommendations
        recommendations = []
        for idx, dist in zip(indices[0], distances[0]):
            track_id = candidate_ids[idx]
            track_response = supabase.from_("Track").select("track_id, title").eq("track_id", track_id).limit(1).execute()
            if track_response.data:
                # Convert distance to similarity
                similarity = 1.0 / (1.0 + dist) if dist > 0 else 1.0
                recommendations.append({
                    'track_id': track_id,
                    'title': track_response.data[0]['title'],
                    'similarity': similarity,
                    'features': candidate_features[track_id]
                })
        
        return recommendations


if __name__ == "__main__":
    # Test the recommender
    recommender = ContentBasedRecommender()
    
    print("Content-Based Recommendation System Test")
    print("=" * 60)
    
    # Test playlist recommendations
    print("\n1. Testing playlist recommendations...")
    playlists = supabase.from_("Playlist").select("playlist_id, title").limit(5).execute()
    if playlists.data:
        test_playlist = playlists.data[0]
        print(f"   Testing with playlist: {test_playlist['title']} (ID: {test_playlist['playlist_id']})")
        recommendations = recommender.recommend_for_playlist(
            playlist_id=test_playlist['playlist_id'],
            n_recommendations=5
        )
        print(f"   Found {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec['title']} (similarity: {rec['similarity']:.3f})")
    else:
        print("   No playlists found in database")
    
    # Test user history recommendations
    print("\n2. Testing user listening history recommendations...")
    listeners = supabase.from_("Listener").select("listener_id").limit(1).execute()
    if listeners.data:
        test_listener = listeners.data[0]['listener_id']
        print(f"   Testing with listener ID: {test_listener}")
        recommendations = recommender.recommend_for_user(
            listener_id=test_listener,
            n_recommendations=5
        )
        print(f"   Found {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec['title']} (similarity: {rec['similarity']:.3f})")
    else:
        print("   No listeners found in database")
