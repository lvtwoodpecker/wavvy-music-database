"""User similarity based on song attributes (audio features + genres)."""
import sys
import os
import pickle
import json
import base64
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
from datetime import datetime
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from app.db.supabase_client import supabase

if not supabase:
    raise Exception("Supabase client not initialized")

MODEL_NAME = 'content_based_similarity'
RETRAIN_THRESHOLD = 0.1
MIN_NEW_TRACKS = 100


class ContentBasedSimilarityService:
    """Calculate user similarity based on song attributes only."""
    
    def __init__(self, n_neighbors: int = 50, metric: str = 'cosine'):
        self.n_neighbors = n_neighbors
        self.metric = metric
        self.scaler = StandardScaler()
        self._feature_cache = {}
        self._genre_encoding_cache = None
        self._cached_model = None
        self._cached_feature_matrix = None
        self._cached_track_ids = None
    
    def _get_total_tracks_count(self) -> int:
        try:
            af_response = supabase.from_("AudioFeatures").select("track_id", count="exact").execute()
            if hasattr(af_response, 'count') and af_response.count is not None:
                return af_response.count
            if hasattr(af_response, 'data'):
                return len(af_response.data) if af_response.data else 0
            return 0
        except:
            try:
                af_response = supabase.from_("AudioFeatures").select("track_id").execute()
                return len(af_response.data) if af_response.data else 0
            except:
                return 0
    
    def _get_model_metadata(self) -> Optional[Dict]:
        try:
            response = supabase.from_("ModelCache").select("metadata").eq("model_name", MODEL_NAME).limit(1).execute()
            if response.data and len(response.data) > 0:
                return response.data[0].get('metadata')
            return None
        except:
            return None
    
    def _save_model_metadata(self, track_count: int, metadata_dict: Dict = None):
        metadata = {
            'track_count': track_count,
            'last_trained': datetime.now().isoformat(),
            'n_neighbors': self.n_neighbors,
            'metric': self.metric
        }
        if metadata_dict:
            metadata.update(metadata_dict)
        return metadata
    
    def _should_retrain(self) -> bool:
        metadata = self._get_model_metadata()
        if not metadata:
            return True
        
        current_count = self._get_total_tracks_count()
        cached_count = metadata.get('track_count', 0)
        
        if cached_count == 0:
            return True
        
        new_tracks = current_count - cached_count
        percentage_increase = new_tracks / cached_count if cached_count > 0 else 1.0
        
        should_retrain = new_tracks >= MIN_NEW_TRACKS or percentage_increase >= RETRAIN_THRESHOLD
        return should_retrain
    
    def _load_cached_model(self) -> bool:
        try:
            response = supabase.from_("ModelCache").select("model_data, metadata").eq("model_name", MODEL_NAME).limit(1).execute()
            
            if not response.data or len(response.data) == 0:
                return False
            
            model_data_b64 = response.data[0]['model_data']
            metadata = response.data[0].get('metadata', {})
            
            if not model_data_b64:
                raise ValueError("Model data is empty")
            
            # Supabase returns BYTEA as base64 string, decode it
            if isinstance(model_data_b64, str):
                model_data_bytes = base64.b64decode(model_data_b64)
            else:
                # If it's already bytes (shouldn't happen with Supabase, but handle it)
                model_data_bytes = model_data_b64
            
            cached_data = pickle.loads(model_data_bytes)
            
            self._cached_model = cached_data['model']
            self._cached_feature_matrix = cached_data['feature_matrix']
            self._cached_track_ids = cached_data['track_ids']
            self.scaler = cached_data['scaler']
            self._genre_encoding_cache = cached_data.get('genre_encoding')
            
            return True
        except Exception:
            try:
                supabase.from_("ModelCache").delete().eq("model_name", MODEL_NAME).execute()
            except Exception:
                pass
            return False
    
    def _save_model(self, model: NearestNeighbors, feature_matrix: np.ndarray, track_ids: List[int], genre_encoding: Dict[str, int]):
        try:
            model_data = {
                'model': model,
                'feature_matrix': feature_matrix,
                'track_ids': track_ids,
                'scaler': self.scaler,
                'genre_encoding': genre_encoding
            }
            
            model_data_bytes = pickle.dumps(model_data)
            # Supabase/PostgREST requires BYTEA data to be base64 encoded when sent via HTTP
            model_data_b64 = base64.b64encode(model_data_bytes).decode('utf-8')
            metadata = self._save_model_metadata(len(track_ids))
            
            existing = supabase.from_("ModelCache").select("model_id").eq("model_name", MODEL_NAME).limit(1).execute()
            
            if existing.data and len(existing.data) > 0:
                result = supabase.from_("ModelCache").update({
                    'model_data': model_data_b64,
                    'metadata': metadata,
                    'updated_at': datetime.now().isoformat()
                }).eq("model_name", MODEL_NAME).execute()
                if not result.data:
                    raise Exception("Update returned no data")
            else:
                result = supabase.from_("ModelCache").insert({
                    'model_name': MODEL_NAME,
                    'model_data': model_data_b64,
                    'metadata': metadata
                }).execute()
                if not result.data:
                    raise Exception("Insert returned no data")
            
            self._cached_model = model
            self._cached_feature_matrix = feature_matrix
            self._cached_track_ids = track_ids
        except Exception as e:
            raise Exception(f"Failed to save model to cache: {str(e)}")
    
    def _get_all_genres(self) -> Dict[str, int]:
        if self._genre_encoding_cache is not None:
            return self._genre_encoding_cache
        
        genre_response = supabase.from_("Genre").select("genre_id, name").execute()
        if not genre_response.data:
            return {}
        
        genres = sorted([g['name'] for g in genre_response.data])
        self._genre_encoding_cache = {genre: idx for idx, genre in enumerate(genres)}
        return self._genre_encoding_cache
    
    def _build_feature_vector(self, af: Dict, genres: List[str], genre_encoding: Dict[str, int]) -> np.ndarray:
        feature_vec = [
            (af.get('tempo', 120) or 120) / 200.0,
            ((af.get('loudness', -10) or -10) + 60) / 60.0,
            af.get('danceability', 0.5) or 0.5,
            af.get('energy', 0.5) or 0.5,
            af.get('valence', 0.5) or 0.5,
            af.get('acousticness', 0.5) or 0.5,
            af.get('instrumentalness', 0.5) or 0.5,
            af.get('speechiness', 0.5) or 0.5,
            af.get('liveness', 0.5) or 0.5,
            (af.get('key', 0) or 0) / 11.0,
            af.get('mode', 0.5) or 0.5,
            (af.get('time_signature', 4) or 4) / 7.0,
        ]
        
        if genre_encoding:
            genre_vec = [0.0] * len(genre_encoding)
            for genre in genres:
                if genre in genre_encoding:
                    genre_vec[genre_encoding[genre]] = 1.0
            feature_vec.extend(genre_vec)
        
        return np.array(feature_vec)
    
    def _batch_get_track_features_vectorized(self, track_ids: List[int], genre_encoding: Dict[str, int]) -> Dict[int, np.ndarray]:
        if not track_ids:
            return {}
        
        af_response = supabase.from_("AudioFeatures").select("*").in_("track_id", track_ids).execute()
        audio_features_map = {af['track_id']: af for af in (af_response.data or [])}
        
        tg_response = supabase.from_("TrackGenre").select("track_id, genre_id").in_("track_id", track_ids).execute()
        track_genre_map = defaultdict(set)
        if tg_response.data:
            for tg in tg_response.data:
                track_genre_map[tg['track_id']].add(tg['genre_id'])
        
        all_genre_ids = set()
        for genre_ids in track_genre_map.values():
            all_genre_ids.update(genre_ids)
        
        genre_id_to_name = {}
        if all_genre_ids:
            genre_response = supabase.from_("Genre").select("genre_id, name").in_("genre_id", list(all_genre_ids)).execute()
            if genre_response.data:
                genre_id_to_name = {g['genre_id']: g['name'] for g in genre_response.data}
        
        feature_vectors = {}
        for track_id in track_ids:
            af = audio_features_map.get(track_id)
            if not af:
                continue
            
            genre_ids = track_genre_map.get(track_id, set())
            genres = [genre_id_to_name[gid] for gid in genre_ids if gid in genre_id_to_name]
            
            feature_vectors[track_id] = self._build_feature_vector(af, genres, genre_encoding)
        
        return feature_vectors
    
    def _get_user_tracks(self, listener_id: str) -> Set[int]:
        tracks = set()
        
        try:
            ph_response = supabase.from_("PlayHistory").select("track_id").eq("listener_id", listener_id).execute()
            if ph_response.data:
                tracks.update([ph['track_id'] for ph in ph_response.data])
        except:
            pass
        
        try:
            playlists_response = supabase.from_("Playlist").select("playlist_id").eq("owner_listener_id", listener_id).execute()
            playlist_ids = [p['playlist_id'] for p in (playlists_response.data or [])]
            
            if playlist_ids:
                pt_response = supabase.from_("PlaylistTrack").select("track_id").in_("playlist_id", playlist_ids).is_("date_removed", "null").execute()
                if pt_response.data:
                    tracks.update([pt['track_id'] for pt in pt_response.data])
        except:
            pass
        
        return tracks
    
    def _get_listener_id(self, username: str) -> Optional[str]:
        try:
            user_response = supabase.from_("User").select("user_id").eq("username", username).limit(1).execute()
            if not user_response.data:
                return None
            
            user_id = user_response.data[0]['user_id']
            listener_response = supabase.from_("Listener").select("listener_id").eq("user_id", user_id).limit(1).execute()
            if not listener_response.data:
                return None
            
            return listener_response.data[0]['listener_id']
        except:
            return None
    
    def calculate_content_based_similarity(self, username1: str, username2: str) -> Dict:
        listener_id1 = self._get_listener_id(username1)
        listener_id2 = self._get_listener_id(username2)
        
        if not listener_id1 or not listener_id2:
            return {"error": "Could not find listener for one or both users"}
        
        tracks1 = self._get_user_tracks(listener_id1)
        tracks2 = self._get_user_tracks(listener_id2)
        
        if not tracks1 or not tracks2:
            return {"error": "One or both users have no tracks"}
        
        genre_encoding = self._get_all_genres()
        features1 = self._batch_get_track_features_vectorized(list(tracks1), genre_encoding)
        features2 = self._batch_get_track_features_vectorized(list(tracks2), genre_encoding)
        
        if not features1 or not features2:
            return {"error": "Could not extract features for user tracks"}
        
        vecs1 = list(features1.values())
        vecs2 = list(features2.values())
        
        min_dim = min(min(len(v) for v in vecs1), min(len(v) for v in vecs2))
        vecs1 = [v[:min_dim] for v in vecs1]
        vecs2 = [v[:min_dim] for v in vecs2]
        
        avg_vec1 = np.mean(vecs1, axis=0)
        avg_vec2 = np.mean(vecs2, axis=0)
        
        cosine_sim = cosine_similarity(avg_vec1.reshape(1, -1), avg_vec2.reshape(1, -1))[0][0]
        euclidean_dist = np.linalg.norm(avg_vec1 - avg_vec2)
        euclidean_sim = 1.0 / (1.0 + euclidean_dist)
        
        genres1 = set()
        genres2 = set()
        
        for track_id in tracks1:
            tg_response = supabase.from_("TrackGenre").select("genre_id").eq("track_id", track_id).execute()
            if tg_response.data:
                genre_ids = [tg['genre_id'] for tg in tg_response.data]
                if genre_ids:
                    genre_response = supabase.from_("Genre").select("name").in_("genre_id", genre_ids).execute()
                    if genre_response.data:
                        genres1.update([g['name'] for g in genre_response.data])
        
        for track_id in tracks2:
            tg_response = supabase.from_("TrackGenre").select("genre_id").eq("track_id", track_id).execute()
            if tg_response.data:
                genre_ids = [tg['genre_id'] for tg in tg_response.data]
                if genre_ids:
                    genre_response = supabase.from_("Genre").select("name").in_("genre_id", genre_ids).execute()
                    if genre_response.data:
                        genres2.update([g['name'] for g in genre_response.data])
        
        genre_overlap = len(genres1 & genres2)
        genre_union = len(genres1 | genres2)
        genre_jaccard = genre_overlap / genre_union if genre_union > 0 else 0.0
        
        return {
            "user1": username1,
            "user2": username2,
            "similarity_scores": {
                "cosine_similarity": float(cosine_sim),
                "euclidean_similarity": float(euclidean_sim),
                "genre_jaccard": float(genre_jaccard),
                "overall": float((cosine_sim + euclidean_sim + genre_jaccard) / 3.0)
            },
            "statistics": {
                "user1_tracks": len(tracks1),
                "user2_tracks": len(tracks2),
                "user1_tracks_with_features": len(features1),
                "user2_tracks_with_features": len(features2),
                "user1_genres": len(genres1),
                "user2_genres": len(genres2),
                "shared_genres": genre_overlap,
                "total_unique_genres": genre_union
            }
        }
    
    def train_model_on_all_tracks(self, max_tracks: int = 5000, force_retrain: bool = False) -> Tuple[np.ndarray, List[int], NearestNeighbors]:
        if not force_retrain and not self._should_retrain():
            if self._cached_model is not None:
                return self._cached_feature_matrix, self._cached_track_ids, self._cached_model
            if self._load_cached_model():
                return self._cached_feature_matrix, self._cached_track_ids, self._cached_model
        
        af_response = supabase.from_("AudioFeatures").select("track_id").limit(max_tracks).execute()
        if not af_response.data:
            if self._load_cached_model():
                return self._cached_feature_matrix, self._cached_track_ids, self._cached_model
            return None, [], None
        
        track_ids = [af['track_id'] for af in af_response.data]
        genre_encoding = self._get_all_genres()
        features_map = self._batch_get_track_features_vectorized(track_ids, genre_encoding)
        
        if not features_map:
            if self._load_cached_model():
                return self._cached_feature_matrix, self._cached_track_ids, self._cached_model
            return None, [], None
        
        feature_vectors = []
        valid_track_ids = []
        
        for track_id, vec in features_map.items():
            if vec is not None:
                feature_vectors.append(vec)
                valid_track_ids.append(track_id)
        
        if not feature_vectors:
            if self._load_cached_model():
                return self._cached_feature_matrix, self._cached_track_ids, self._cached_model
            return None, [], None
        
        feature_matrix = np.array(feature_vectors)
        feature_matrix_scaled = self.scaler.fit_transform(feature_matrix)
        
        knn = NearestNeighbors(n_neighbors=min(self.n_neighbors, len(feature_matrix_scaled)),
                              metric=self.metric, algorithm='brute')
        knn.fit(feature_matrix_scaled)
        
        self._save_model(knn, feature_matrix_scaled, valid_track_ids, genre_encoding)
        
        self._cached_model = knn
        self._cached_feature_matrix = feature_matrix_scaled
        self._cached_track_ids = valid_track_ids
        
        return feature_matrix_scaled, valid_track_ids, knn
    
    def get_recommendations_for_both_users(
        self,
        username1: str,
        username2: str,
        n_recommendations: int = 10,
        max_artist_repeats: int = 2
    ) -> Dict:
        listener_id1 = self._get_listener_id(username1)
        listener_id2 = self._get_listener_id(username2)
        
        if not listener_id1 or not listener_id2:
            return {"error": "Could not find one or both users"}
        
        tracks1 = self._get_user_tracks(listener_id1)
        tracks2 = self._get_user_tracks(listener_id2)
        all_user_tracks = tracks1 | tracks2
        
        if not all_user_tracks:
            return {"error": "Users have no tracks"}
        
        feature_matrix, all_track_ids, knn_model = self.train_model_on_all_tracks(max_tracks=5000)
        
        if feature_matrix is None or knn_model is None:
            return {"error": "Could not train model on tracks"}
        
        genre_encoding = self._get_all_genres()
        user_track_ids_list = list(all_user_tracks)
        user_features = self._batch_get_track_features_vectorized(user_track_ids_list, genre_encoding)
        
        if not user_features:
            return {"error": "Could not extract features for user tracks"}
        
        user_vecs = list(user_features.values())
        if not user_vecs:
            return {"error": "No valid feature vectors"}
        
        min_dim = min(len(v) for v in user_vecs)
        if min_dim != feature_matrix.shape[1]:
            min_dim = min(min_dim, feature_matrix.shape[1])
            user_vecs = [v[:min_dim] for v in user_vecs]
            feature_matrix = feature_matrix[:, :min_dim]
        
        avg_user_vec = np.mean(user_vecs, axis=0)
        avg_user_vec_scaled = self.scaler.transform(avg_user_vec.reshape(1, -1))
        
        candidate_indices = [i for i, tid in enumerate(all_track_ids) if tid not in all_user_tracks]
        
        if not candidate_indices:
            return {"error": "No candidate tracks found"}
        
        candidate_matrix = feature_matrix[candidate_indices]
        candidate_track_ids = [all_track_ids[i] for i in candidate_indices]
        
        knn_candidates = NearestNeighbors(n_neighbors=min(n_recommendations * 3, len(candidate_matrix)),
                                         metric=self.metric, algorithm='brute')
        knn_candidates.fit(candidate_matrix)
        
        distances, indices = knn_candidates.kneighbors(
            avg_user_vec_scaled,
            n_neighbors=min(n_recommendations * 5, len(candidate_track_ids))
        )
        
        track_artists_map = {}
        all_candidate_ids = [candidate_track_ids[idx] for idx in indices[0]]
        
        ta_response = supabase.from_("TrackArtist").select("track_id, artist_id").in_("track_id", all_candidate_ids).execute()
        if ta_response.data:
            for ta in ta_response.data:
                track_id = ta['track_id']
                artist_id = ta['artist_id']
                if track_id not in track_artists_map:
                    track_artists_map[track_id] = []
                track_artists_map[track_id].append(artist_id)
        
        all_artist_ids = set()
        for artist_ids in track_artists_map.values():
            all_artist_ids.update(artist_ids)
        
        artist_names_map = {}
        if all_artist_ids:
            artist_response = supabase.from_("Artist").select("artist_id, name").in_("artist_id", list(all_artist_ids)[:200]).execute()
            if artist_response.data:
                artist_names_map = {a['artist_id']: a['name'] for a in artist_response.data}
        
        recommendations = []
        artist_count = defaultdict(int)
        
        for idx, dist in zip(indices[0], distances[0]):
            track_id = candidate_track_ids[idx]
            
            artist_ids = track_artists_map.get(track_id, [])
            artists = [artist_names_map.get(aid, "Unknown") for aid in artist_ids if aid in artist_names_map]
            
            if artists:
                primary_artist = artists[0]
                if artist_count[primary_artist] >= max_artist_repeats:
                    continue
                artist_count[primary_artist] += 1
            
            track_response = supabase.from_("Track").select("track_id, title").eq("track_id", track_id).limit(1).execute()
            if not track_response.data:
                continue
            
            tg_response = supabase.from_("TrackGenre").select("genre_id").eq("track_id", track_id).execute()
            genre_ids = [tg['genre_id'] for tg in (tg_response.data or [])]
            genres = []
            if genre_ids:
                genre_response = supabase.from_("Genre").select("name").in_("genre_id", genre_ids).execute()
                if genre_response.data:
                    genres = [g['name'] for g in genre_response.data]
            
            similarity = 1.0 / (1.0 + dist) if dist > 0 else 1.0
            
            recommendations.append({
                "track_id": track_id,
                "title": track_response.data[0]['title'],
                "artists": artists,
                "genres": genres[:5],
                "similarity": float(similarity),
                "distance": float(dist)
            })
            
            if len(recommendations) >= n_recommendations:
                break
        
        top_track_ids = [r['track_id'] for r in recommendations]
        af_response = supabase.from_("AudioFeatures").select("track_id, tempo, danceability, energy, valence").in_("track_id", top_track_ids).execute()
        audio_features_map = {af['track_id']: af for af in (af_response.data or [])}
        
        for rec in recommendations:
            af = audio_features_map.get(rec['track_id'])
            if af:
                rec['audio_features'] = {
                    'tempo': af.get('tempo'),
                    'danceability': af.get('danceability'),
                    'energy': af.get('energy'),
                    'valence': af.get('valence')
                }
        
        metadata = self._get_model_metadata()
        is_cached = metadata is not None and not self._should_retrain()
        
        return {
            "user1": username1,
            "user2": username2,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "model_info": {
                "method": "Content-based K-NN on audio features + genres",
                "total_tracks_in_model": len(all_track_ids),
                "user_tracks_analyzed": len(all_user_tracks),
                "max_artist_repeats": max_artist_repeats,
                "model_cached": is_cached
            },
            "diversity_stats": {
                "unique_artists": len(set(artist_count.keys())),
                "artist_distribution": dict(artist_count)
            }
        }
