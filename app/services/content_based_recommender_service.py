"""Content-based filtering recommender for playlists and users."""
import sys
import os
import pickle
import json
import base64
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict
from datetime import datetime
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from app.db.supabase_client import supabase

MODEL_NAME_PLAYLIST = 'content_based_recommender_playlist'
MODEL_NAME_USER = 'content_based_recommender_user'
RETRAIN_THRESHOLD = 0.1
MIN_NEW_TRACKS = 100


class ContentBasedRecommenderService:
    """Content-based filtering recommender using K-NN with cached models."""
    
    def __init__(self, n_neighbors: int = 10, metric: str = 'cosine'):
        self.n_neighbors = n_neighbors
        self.metric = metric
        self.scaler = StandardScaler()
        self._feature_cache = {}
        self._cached_all_tracks_model = None
        self._cached_all_tracks_features = None
        self._cached_all_track_ids = None
        self._cached_genre_encoding = None

    def _ensure_supabase(self):
        """Ensure Supabase client is initialized before use."""
        if not supabase:
            raise Exception("Supabase client not initialized")
    
    def _get_total_tracks_count(self) -> int:
        self._ensure_supabase()
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
    
    def _get_model_metadata(self, model_name: str) -> Optional[Dict]:
        self._ensure_supabase()
        try:
            response = supabase.from_("ModelCache").select("metadata").eq("model_name", model_name).limit(1).execute()
            if response.data and len(response.data) > 0:
                return response.data[0].get('metadata')
            return None
        except:
            return None
    
    def _should_retrain(self, model_name: str) -> bool:
        metadata = self._get_model_metadata(model_name)
        if not metadata:
            print(f"[ModelCache] No metadata found for {model_name}, will retrain")
            return True
        
        current_count = self._get_total_tracks_count()
        cached_count = metadata.get('track_count', 0)
        
        if cached_count == 0:
            print(f"[ModelCache] Cached count is 0 for {model_name}, will retrain")
            return True
        
        new_tracks = current_count - cached_count
        percentage_increase = new_tracks / cached_count if cached_count > 0 else 1.0
        
        should_retrain = new_tracks >= MIN_NEW_TRACKS or percentage_increase >= RETRAIN_THRESHOLD
        print(f"[ModelCache] Check retrain for {model_name}: current={current_count}, cached={cached_count}, new={new_tracks}, pct={percentage_increase:.2%}, retrain={should_retrain}")
        return should_retrain
    
    def _load_cached_model(self, model_name: str) -> bool:
        self._ensure_supabase()
        try:
            print(f"[ModelCache] Attempting to load cached model {model_name}")
            response = supabase.from_("ModelCache").select("model_data, metadata").eq("model_name", model_name).limit(1).execute()
            
            if not response.data or len(response.data) == 0:
                print(f"[ModelCache] No cached model found for {model_name}")
                return False
            
            print(f"[ModelCache] Found cached model {model_name}, loading...")
            model_data_b64_raw = response.data[0]['model_data']
            
            raw_len = len(model_data_b64_raw) if model_data_b64_raw else 0
            print(f"[ModelCache] Raw data length: {raw_len}")
            
            model_data_b64 = model_data_b64_raw.strip().replace('\n', '').replace('\r', '').replace(' ', '')
            cleaned_len = len(model_data_b64)
            print(f"[ModelCache] Cleaned data length: {cleaned_len}")
            
            remainder = cleaned_len % 4
            if remainder != 0:
                padding_needed = 4 - remainder
                print(f"[ModelCache] Length {cleaned_len} mod 4 = {remainder}, adding {padding_needed} padding chars")
                model_data_b64 += '=' * padding_needed
            
            final_len = len(model_data_b64)
            if final_len % 4 != 0:
                print(f"[ModelCache] ERROR: After padding, length {final_len} is still not multiple of 4 (mod {final_len % 4})")
                raise ValueError(f"Invalid base64 string length: {final_len}")
            
            print(f"[ModelCache] Final base64 length: {final_len} (multiple of 4: {final_len % 4 == 0})")
            
            try:
                model_data_bytes = base64.b64decode(model_data_b64, validate=True)
                print(f"[ModelCache] Successfully decoded {len(model_data_bytes)} bytes")
            except Exception as decode_error:
                print(f"[ModelCache] Strict decode failed: {decode_error}")
                try:
                    model_data_bytes = base64.b64decode(model_data_b64, validate=False)
                    print(f"[ModelCache] Lenient decode succeeded: {len(model_data_bytes)} bytes")
                except Exception as lenient_error:
                    print(f"[ModelCache] Lenient decode failed: {lenient_error}")
                    raise ValueError(f"Cannot decode base64: {lenient_error}")
            
            cached_data = pickle.loads(model_data_bytes)
            
            self._cached_all_tracks_model = cached_data['model']
            self._cached_all_tracks_features = cached_data['feature_matrix']
            self._cached_all_track_ids = cached_data['track_ids']
            self.scaler = cached_data['scaler']
            self._cached_genre_encoding = cached_data.get('genre_encoding')
            
            print(f"[ModelCache] Successfully loaded cached model {model_name}")
            return True
        except Exception as e:
            print(f"[ModelCache] ERROR loading cached model {model_name}: {str(e)}")
            print(f"[ModelCache] Model data appears corrupted, will retrain on next request")
            try:
                supabase.from_("ModelCache").delete().eq("model_name", model_name).execute()
                print(f"[ModelCache] Deleted corrupted model entry")
            except:
                pass
            import traceback
            traceback.print_exc()
            return False
    
    def _save_model(self, model_name: str, model: NearestNeighbors, feature_matrix: np.ndarray, 
                   track_ids: List[int], genre_encoding: Dict[str, int]):
        self._ensure_supabase()
        try:
            model_data = {
                'model': model,
                'feature_matrix': feature_matrix,
                'track_ids': track_ids,
                'scaler': self.scaler,
                'genre_encoding': genre_encoding
            }
            
            model_data_bytes = pickle.dumps(model_data)
            model_data_b64 = base64.b64encode(model_data_bytes).decode('utf-8')
            
            print(f"[ModelCache] Saving model {model_name}, size: {len(model_data_b64)} chars")
            
            metadata = {
                'track_count': len(track_ids),
                'last_trained': datetime.now().isoformat(),
                'n_neighbors': self.n_neighbors,
                'metric': self.metric
            }
            
            existing = supabase.from_("ModelCache").select("model_id").eq("model_name", model_name).limit(1).execute()
            
            if existing.data and len(existing.data) > 0:
                result = supabase.from_("ModelCache").update({
                    'model_data': model_data_b64,
                    'metadata': metadata,
                    'updated_at': datetime.now().isoformat()
                }).eq("model_name", model_name).execute()
                if result.data:
                    print(f"[ModelCache] Updated model {model_name} successfully")
                else:
                    print(f"[ModelCache] WARNING: Update returned no data for {model_name}")
            else:
                result = supabase.from_("ModelCache").insert({
                    'model_name': model_name,
                    'model_data': model_data_b64,
                    'metadata': metadata
                }).execute()
                if result.data:
                    print(f"[ModelCache] Inserted model {model_name} successfully")
                else:
                    print(f"[ModelCache] WARNING: Insert returned no data for {model_name}")
            
            verify = supabase.from_("ModelCache").select("model_id, model_data").eq("model_name", model_name).execute()
            if verify.data and len(verify.data) > 0:
                saved_size = len(verify.data[0].get('model_data', ''))
                print(f"[ModelCache] Verified: Model {model_name} exists in database, saved size: {saved_size} chars (original: {len(model_data_b64)} chars)")
                if saved_size != len(model_data_b64):
                    print(f"[ModelCache] WARNING: Size mismatch! Data may be corrupted or truncated.")
            else:
                print(f"[ModelCache] ERROR: Model {model_name} not found after save!")
            
            self._cached_all_tracks_model = model
            self._cached_all_tracks_features = feature_matrix
            self._cached_all_track_ids = track_ids
            self._cached_genre_encoding = genre_encoding
        except Exception as e:
            print(f"[ModelCache] ERROR saving model {model_name}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _get_all_genres(self) -> Dict[str, int]:
        if self._cached_genre_encoding is not None:
            return self._cached_genre_encoding
        self._ensure_supabase()
        
        genre_response = supabase.from_("Genre").select("genre_id, name").execute()
        if not genre_response.data:
            return {}
        
        genres = sorted([g['name'] for g in genre_response.data])
        self._cached_genre_encoding = {genre: idx for idx, genre in enumerate(genres)}
        return self._cached_genre_encoding
    
    def _build_feature_vector(self, af: Dict, genres: List[str], genre_encoding: Dict[str, int]) -> Optional[np.ndarray]:
        if not af:
            return None
        
        feature_vec = [
            (af.get('tempo', 120) or 120) / 200.0,
            ((af.get('loudness', -10) or -10) + 60) / 60.0,
            af.get('danceability', 0.5) or 0.5,
            af.get('energy', 0.5) or 0.5,
            af.get('valence', 0.5) or 0.5,
            af.get('acousticness', 0.5) or 0.5,
        ]
        
        if genre_encoding:
            genre_vec = [0.0] * len(genre_encoding)
            for genre in genres:
                if genre in genre_encoding:
                    genre_vec[genre_encoding[genre]] = 1.0
            feature_vec.extend(genre_vec)
        
        return np.array(feature_vec)
    
    def _batch_get_track_features(self, track_ids: List[int], genre_encoding: Dict[str, int]) -> Dict[int, Dict]:
        if not track_ids:
            return {}
        self._ensure_supabase()
        
        features_map = {}
        
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
        
        for track_id in track_ids:
            audio_features = audio_features_map.get(track_id)
            genre_ids = track_genre_map.get(track_id, set())
            genres = [genre_id_to_name[gid] for gid in genre_ids if gid in genre_id_to_name]
            
            features = {
                'audio_features': audio_features,
                'genres': genres
            }
            features_map[track_id] = features
            self._feature_cache[track_id] = features
        
        return features_map
    
    def _build_feature_matrix(self, track_features_map: Dict[int, Dict], genre_encoding: Dict[str, int]) -> Tuple[Optional[np.ndarray], List[int]]:
        feature_vectors = []
        track_ids = []
        
        for track_id, features in track_features_map.items():
            af = features.get('audio_features')
            genres = features.get('genres', [])
            vec = self._build_feature_vector(af, genres, genre_encoding)
            if vec is not None:
                feature_vectors.append(vec)
                track_ids.append(track_id)
        
        if not feature_vectors:
            return None, []
        
        return np.array(feature_vectors), track_ids
    
    def _train_all_tracks_model(self, model_name: str, max_tracks: int = 5000, force_retrain: bool = False) -> Tuple[Optional[np.ndarray], List[int], Optional[NearestNeighbors]]:
        self._ensure_supabase()
        if not force_retrain and not self._should_retrain(model_name):
            if self._cached_all_tracks_model is not None:
                return self._cached_all_tracks_features, self._cached_all_track_ids, self._cached_all_tracks_model
            if self._load_cached_model(model_name):
                return self._cached_all_tracks_features, self._cached_all_track_ids, self._cached_all_tracks_model
        
        af_response = supabase.from_("AudioFeatures").select("track_id").limit(max_tracks).execute()
        if not af_response.data:
            if self._load_cached_model(model_name):
                return self._cached_all_tracks_features, self._cached_all_track_ids, self._cached_all_tracks_model
            return None, [], None
        
        track_ids = [af['track_id'] for af in af_response.data]
        genre_encoding = self._get_all_genres()
        features_map = self._batch_get_track_features(track_ids, genre_encoding)
        
        if not features_map:
            if self._load_cached_model(model_name):
                return self._cached_all_tracks_features, self._cached_all_track_ids, self._cached_all_tracks_model
            return None, [], None
        
        feature_matrix, valid_track_ids = self._build_feature_matrix(features_map, genre_encoding)
        
        if feature_matrix is None:
            if self._load_cached_model(model_name):
                return self._cached_all_tracks_features, self._cached_all_track_ids, self._cached_all_tracks_model
            return None, [], None
        
        feature_matrix_scaled = self.scaler.fit_transform(feature_matrix)
        
        knn = NearestNeighbors(n_neighbors=min(self.n_neighbors, len(feature_matrix_scaled)),
                              metric=self.metric, algorithm='brute')
        knn.fit(feature_matrix_scaled)
        
        print(f"[ModelCache] Training complete for {model_name}, tracks: {len(valid_track_ids)}, features shape: {feature_matrix_scaled.shape}")
        
        self._save_model(model_name, knn, feature_matrix_scaled, valid_track_ids, genre_encoding)
        
        return feature_matrix_scaled, valid_track_ids, knn
    
    def _get_playlist_tracks(self, playlist_id: int) -> List[Dict]:
        self._ensure_supabase()
        pt_response = supabase.from_("PlaylistTrack").select(
            "track_id, date_added"
        ).eq("playlist_id", playlist_id).is_("date_removed", "null").execute()
        
        if not pt_response.data:
            return []
        
        track_ids = [pt['track_id'] for pt in pt_response.data]
        tracks_response = supabase.from_("Track").select("*").in_("track_id", track_ids).execute()
        
        if not tracks_response.data:
            return []
        
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
        self._ensure_supabase()
        ph_response = supabase.from_("PlayHistory").select(
            "track_id, played_at"
        ).eq("listener_id", listener_id).order("played_at", desc=True).limit(limit).execute()
        
        if not ph_response.data:
            return []
        
        track_ids = [ph['track_id'] for ph in ph_response.data]
        tracks_response = supabase.from_("Track").select("*").in_("track_id", track_ids).execute()
        
        if not tracks_response.data:
            return []
        
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
    
    def recommend_for_playlist(self, playlist_id: int, n_recommendations: int = 10) -> List[Dict]:
        self._ensure_supabase()
        playlist_tracks = self._get_playlist_tracks(playlist_id)
        
        if not playlist_tracks:
            return []
        
        playlist_track_ids = {item['track']['track_id'] for item in playlist_tracks}
        playlist_track_ids_list = list(playlist_track_ids)
        
        all_tracks_features, all_track_ids, all_tracks_model = self._train_all_tracks_model(MODEL_NAME_PLAYLIST, max_tracks=5000)
        
        if all_tracks_features is None or all_tracks_model is None:
            return []
        
        genre_encoding = self._get_all_genres()
        playlist_features_map = self._batch_get_track_features(playlist_track_ids_list, genre_encoding)
        playlist_features = {tid: feat for tid, feat in playlist_features_map.items() 
                           if feat.get('audio_features')}
        
        if not playlist_features:
            return []
        
        playlist_matrix, _ = self._build_feature_matrix(playlist_features, genre_encoding)
        
        if playlist_matrix is None or len(playlist_matrix) == 0:
            return []
        
        playlist_matrix_scaled = self.scaler.transform(playlist_matrix)
        playlist_avg = np.mean(playlist_matrix_scaled, axis=0).reshape(1, -1)
        
        candidate_indices = [i for i, tid in enumerate(all_track_ids) if tid not in playlist_track_ids]
        
        if not candidate_indices:
            return []
        
        candidate_matrix = all_tracks_features[candidate_indices]
        candidate_track_ids = [all_track_ids[i] for i in candidate_indices]
        
        knn_candidates = NearestNeighbors(n_neighbors=min(n_recommendations, len(candidate_matrix)),
                                         metric=self.metric, algorithm='brute')
        knn_candidates.fit(candidate_matrix)
        
        distances, indices = knn_candidates.kneighbors(playlist_avg, n_neighbors=min(n_recommendations, len(candidate_track_ids)))
        
        recommendations = []
        for idx, dist in zip(indices[0], distances[0]):
            track_id = candidate_track_ids[idx]
            track_response = supabase.from_("Track").select("track_id, title").eq("track_id", track_id).limit(1).execute()
            if track_response.data:
                similarity = 1.0 / (1.0 + dist) if dist > 0 else 1.0
                recommendations.append({
                    'track_id': track_id,
                    'title': track_response.data[0]['title'],
                    'similarity': float(similarity),
                    'features': playlist_features_map.get(track_id, {})
                })
        
        return recommendations
    
    def recommend_for_user(self, listener_id: str, n_recommendations: int = 10) -> List[Dict]:
        self._ensure_supabase()
        recent_history = self._get_user_history_tracks(listener_id, limit=10)
        recent_track_ids = {item['track']['track_id'] for item in recent_history}
        
        history_tracks = self._get_user_history_tracks(listener_id, limit=50)
        
        if not history_tracks:
            return []
        
        history_track_ids_list = [item['track']['track_id'] for item in history_tracks]
        
        all_tracks_features, all_track_ids, all_tracks_model = self._train_all_tracks_model(MODEL_NAME_USER, max_tracks=5000)
        
        if all_tracks_features is None or all_tracks_model is None:
            return []
        
        genre_encoding = self._get_all_genres()
        history_features_map = self._batch_get_track_features(history_track_ids_list, genre_encoding)
        history_features = {tid: feat for tid, feat in history_features_map.items() 
                          if feat.get('audio_features')}
        
        if not history_features:
            return []
        
        history_matrix, _ = self._build_feature_matrix(history_features, genre_encoding)
        
        if history_matrix is None or len(history_matrix) == 0:
            return []
        
        history_matrix_scaled = self.scaler.transform(history_matrix)
        history_avg = np.mean(history_matrix_scaled, axis=0).reshape(1, -1)
        
        candidate_indices = [i for i, tid in enumerate(all_track_ids) if tid not in recent_track_ids]
        
        if not candidate_indices:
            return []
        
        candidate_matrix = all_tracks_features[candidate_indices]
        candidate_track_ids = [all_track_ids[i] for i in candidate_indices]
        
        knn_candidates = NearestNeighbors(n_neighbors=min(n_recommendations, len(candidate_matrix)),
                                         metric=self.metric, algorithm='brute')
        knn_candidates.fit(candidate_matrix)
        
        distances, indices = knn_candidates.kneighbors(history_avg, n_neighbors=min(n_recommendations, len(candidate_track_ids)))
        
        recommendations = []
        for idx, dist in zip(indices[0], distances[0]):
            track_id = candidate_track_ids[idx]
            track_response = supabase.from_("Track").select("track_id, title").eq("track_id", track_id).limit(1).execute()
            if track_response.data:
                similarity = 1.0 / (1.0 + dist) if dist > 0 else 1.0
                recommendations.append({
                    'track_id': track_id,
                    'title': track_response.data[0]['title'],
                    'similarity': float(similarity),
                    'features': history_features_map.get(track_id, {})
                })
        
        return recommendations

