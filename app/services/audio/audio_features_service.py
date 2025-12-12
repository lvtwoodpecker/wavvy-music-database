# """
# Service for managing audio features in the database.
# Handles fetching and storing audio features using ReccoBeats API.
# """
# from typing import Optional, Dict
# from app.services.audio.reccobeats_service import ReccoBeatsService

# if not supabase:
#     raise Exception("Supabase client not initialized")


# def fetch_and_save_audio_features(
#     supabase,
#     track_id: int, track_title: str, 
#                                   artist_name: Optional[str] = None,
#                                   duration_ms: Optional[int] = None,
#                                   spotify_track_id: Optional[str] = None) -> bool:
#     """
#     Fetch audio features for a track and save them to the database.
#     Also updates the track's spotify_id if not already set.
    
#     Args:
#         track_id: Database track_id
#         track_title: Track title
#         artist_name: Optional artist name for better matching
#         duration_ms: Optional duration in milliseconds for better matching
#         spotify_track_id: Optional Spotify track ID if already known
    
#     Returns:
#         True if audio features were successfully saved, False otherwise
#     """
#     try:
#         # Get Spotify track ID if not provided
#         if not spotify_track_id:
#             spotify_track_id = ReccoBeatsService.get_spotify_track_id(
#                 track_title, artist_name, duration_ms
#             )
#             if not spotify_track_id:
#                 return False
        
#         # Update track with spotify_id if not already set
#         track_response = supabase.from_("Track").select("spotify_id").eq("track_id", track_id).limit(1).execute()
#         if track_response.data and not track_response.data[0].get('spotify_id'):
#             supabase.from_("Track").update({"spotify_id": spotify_track_id}).eq("track_id", track_id).execute()
        
#         # Get audio features from ReccoBeats
#         features = ReccoBeatsService.get_audio_features(spotify_track_id)
        
#         if not features:
#             return False
        
#         # Validate and prepare for insertion
#         audio_features_to_insert = {
#             "track_id": track_id,
#             "tempo": features.get('tempo', 0),
#             "loudness": features.get('loudness', 0),
#             "danceability": features.get('danceability', 0),
#             "energy": features.get('energy'),
#             "valence": features.get('valence'),
#             "acousticness": features.get('acousticness')
#         }
        
#         # Validate tempo and loudness constraints
#         if audio_features_to_insert['tempo'] > 0 and -60 <= audio_features_to_insert['loudness'] <= 10:
#             audio_features_response = supabase.from_("AudioFeatures").upsert(
#                 audio_features_to_insert, 
#                 on_conflict='track_id'
#             ).execute()
            
#             return bool(audio_features_response.data)
        
#         return False
        
#     except Exception as e:
#         print(f"      > Error fetching/saving audio features: {e}")
#         return False

