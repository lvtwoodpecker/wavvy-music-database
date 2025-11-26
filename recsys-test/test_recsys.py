"""
Test script for the recommendation system.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from recsys import ContentBasedRecommender
from app.db.supabase_client import supabase

# Skip all tests if Supabase is not initialized
pytestmark = pytest.mark.skipif(
    not supabase,
    reason="Supabase client not initialized - missing SUPABASE_URL or SUPABASE_SERVICE_KEY"
)


def test_playlist_recommendations():
    """Test playlist-based recommendations."""
    print("\n" + "="*60)
    print("TEST: Playlist Recommendations")
    print("="*60)
    
    recommender = ContentBasedRecommender()
    
    # Get one playlist
    playlists = supabase.from_("Playlist").select("playlist_id, title").limit(1).execute()
    
    if not playlists.data:
        print("No playlists found in database")
        return
    
    playlist = playlists.data[0]
    
    print(f"\nPlaylist: {playlist['title']} (ID: {playlist['playlist_id']})")
    
    # Get tracks in playlist
    pt_response = supabase.from_("PlaylistTrack").select("track_id").eq(
        "playlist_id", playlist['playlist_id']
    ).is_("date_removed", "null").execute()
    
    if pt_response.data:
        track_ids = [pt['track_id'] for pt in pt_response.data]
        tracks_response = supabase.from_("Track").select("title").in_("track_id", track_ids).execute()
        print(f"  Current tracks ({len(tracks_response.data)}):")
        for track in tracks_response.data[:5]:
            print(f"    - {track['title']}")
    
    # Get recommendations
    recommendations = recommender.recommend_for_playlist(
        playlist_id=playlist['playlist_id'],
        n_recommendations=10
    )
    
    print(f"\n  Recommendations ({len(recommendations)}):")
    for i, rec in enumerate(recommendations[:5], 1):
        genres = ', '.join(rec['features'].get('genres', [])[:3]) if rec.get('features') else 'No genres'
        print(f"    {i}. {rec['title']}")
        print(f"       Similarity: {rec['similarity']:.3f} | Genres: {genres}")


def test_user_history_recommendations():
    """Test user listening history-based recommendations."""
    print("\n" + "="*60)
    print("TEST: User Listening History Recommendations")
    print("="*60)
    
    recommender = ContentBasedRecommender()
    
    # Get a listener
    listeners = supabase.from_("Listener").select("listener_id").limit(1).execute()
    
    if not listeners.data:
        print("No listeners found in database")
        return
    
    listener_id = listeners.data[0]['listener_id']
    print(f"\nListener ID: {listener_id}")
    
    # Get listening history
    ph_response = supabase.from_("PlayHistory").select("track_id, played_at").eq(
        "listener_id", listener_id
    ).order("played_at", desc=True).limit(10).execute()
    
    if ph_response.data:
        track_ids = [ph['track_id'] for ph in ph_response.data]
        tracks_response = supabase.from_("Track").select("title").in_("track_id", track_ids).execute()
        print(f"  Recent listening history ({len(tracks_response.data)} tracks):")
        for track in tracks_response.data[:5]:
            print(f"    - {track['title']}")
    
    # Get recommendations
    recommendations = recommender.recommend_for_user(
        listener_id=listener_id,
        n_recommendations=10
    )
    
    print(f"\n  Recommendations ({len(recommendations)}):")
    for i, rec in enumerate(recommendations[:5], 1):
        genres = ', '.join(rec['features'].get('genres', [])[:3]) or 'No genres'
        print(f"    {i}. {rec['title']}")
        print(f"       Similarity: {rec['similarity']:.3f} | Genres: {genres}")


if __name__ == "__main__":
    print("Recommendation System Test Suite")
    print("="*60)
    
    try:
        test_playlist_recommendations()
        test_user_history_recommendations()
        
        print("\n" + "="*60)
        print("Tests completed!")
        print("="*60)
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()

