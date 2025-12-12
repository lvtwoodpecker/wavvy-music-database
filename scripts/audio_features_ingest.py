"""
Audio features ingestion script using ReccoBeats API.
Fetches audio features for all tracks in the database that don't have them yet.
Uses the ReccoBeats and AudioFeatures services.
"""
import sys
import os
import time
from app import WavvyAPIWrapper
from app.api import WavvyAPIBlueprints
from app.services.register_services import APIServices
from app.services.audio.audio_features_service import fetch_and_save_audio_features

APP = WavvyAPIWrapper(__name__).create_dev_app()
APP._services = APIServices(APP)
WavvyAPIBlueprints.register_blueprints(APP)

def ingest_audio_features(limit=None, track_id=None):
    """
    Ingest audio features for tracks in the database using ReccoBeats API.
    
    Args:
        limit: Maximum number of tracks to process (None for all)
        track_id: Specific track_id to update (None for all tracks)
    """
    try:
        print("Starting audio features ingestion from ReccoBeats API...")
        
        # Query tracks that don't have audio features yet
        query = APP.supabase.from_("Track").select("track_id, title, duration_ms")
        
        if track_id:
            query = query.eq("track_id", track_id)
        
        tracks_response = query.execute()
        
        if not tracks_response.data:
            print("No tracks found to process.")
            return
        
        # Filter out tracks that already have audio features
        tracks_to_process = []
        for track in tracks_response.data:
            # Check if audio features exist
            af_response = APP.supabase.from_("AudioFeatures").select("track_id").eq("track_id", track['track_id']).limit(1).execute()
            if not af_response.data:
                tracks_to_process.append(track)
        
        if not tracks_to_process:
            print("All tracks already have audio features.")
            return
        
        tracks = tracks_to_process
        if limit:
            tracks = tracks[:limit]
        
        print(f"Found {len(tracks)} tracks without audio features to process.")
        
        updated_count = 0
        not_found_count = 0
        error_count = 0
        
        for idx, track in enumerate(tracks, 1):
            print(f"\n[{idx}/{len(tracks)}] Processing: {track['title']}")
            
            # Get artist name for better matching
            trackartist_response = APP.supabase.from_("TrackArtist").select(
                "artist_id"
            ).eq("track_id", track['track_id']).limit(1).execute()
            
            artist_name = None
            if trackartist_response.data:
                artist_id = trackartist_response.data[0]['artist_id']
                artist_response = APP.supabase.from_("Artist").select("name").eq("artist_id", artist_id).limit(1).execute()
                if artist_response.data:
                    artist_name = artist_response.data[0].get('name')
            
            # Fetch and save audio features using the service
            try:
                success = fetch_and_save_audio_features(
                    track_id=track['track_id'],
                    track_title=track['title'],
                    artist_name=artist_name,
                    duration_ms=track.get('duration_ms'),
                    spotify_track_id=track.get('spotify_id')
                )
                
                if success:
                    updated_count += 1
                    print(f"  > ✓ Successfully fetched and saved audio features")
                else:
                    not_found_count += 1
                    print(f"  > ✗ Audio features not found or could not be saved")
                
                # Rate limiting - wait between requests
                time.sleep(0.5)  # 500ms delay to respect rate limits
                
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                if "Rate limited" in error_msg:
                    print(f"  > ⚠ Rate limited - waiting...")
                    wait_time = 60  # Wait 1 minute if rate limited
                    print(f"  > Waiting {wait_time} seconds before continuing...")
                    time.sleep(wait_time)
                else:
                    print(f"  > ✗ Error: {error_msg}")
        
        print(f"\n{'='*50}")
        print(f"Audio Features Ingestion Summary:")
        print(f"  Updated: {updated_count}")
        print(f"  Not Found: {not_found_count}")
        print(f"  Errors: {error_count}")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"An error occurred during audio features ingestion: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Audio Features Ingestion Script (ReccoBeats API)")
    print("=" * 50)
    print("\nOptions:")
    print("1. Update all tracks without audio features")
    print("2. Update specific number of tracks")
    print("3. Update specific track by ID")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        ingest_audio_features()
    elif choice == "2":
        limit = input("Enter number of tracks to process: ").strip()
        try:
            limit = int(limit)
            ingest_audio_features(limit=limit)
        except ValueError:
            print("Invalid number")
    elif choice == "3":
        track_id = input("Enter track_id: ").strip()
        try:
            track_id = int(track_id)
            ingest_audio_features(track_id=track_id)
        except ValueError:
            print("Invalid track_id")
    else:
        print("Invalid choice")

