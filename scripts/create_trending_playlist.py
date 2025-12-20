"""
Create a "Now Trending" playlist with sample tracks.
Usage: python -m scripts.create_trending_playlist
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.playlist.playlist_service import PlaylistService
from app.db.sqlalchemy_engine import SessionLocal
from sqlalchemy import select
from app.models.User import User

def create_trending_playlist():
    # Create a temporary app-like object for the service
    class FakeApp:
        pass
    
    service = PlaylistService(FakeApp()).create_service()
    
    try:
        # Get the first listener to own this playlist
        with SessionLocal() as db:
            from app.models.Listener import Listener
            listener = db.scalars(select(Listener).limit(1)).first()
            if not listener:
                print("No listeners found. Please create a listener first.")
                return
            
            owner_id = listener.listener_id
        
        # Check if "Now Trending" already exists
        existing = service.list_playlists(owner_id)
        trending_playlist = next((p for p in existing if p.name == "Now Trending"), None)
        
        if trending_playlist:
            print(f"'Now Trending' playlist already exists (ID: {trending_playlist.id})")
            playlist = trending_playlist
        else:
            # Create the playlist
            playlist = service.create_playlist(owner_id, "Now Trending", "Top hits right now")
            print(f"Created 'Now Trending' playlist (ID: {playlist.id})")
        
        print(f"✓ 'Now Trending' playlist created successfully (ID: {playlist.id})")
        
        # Add tracks to the playlist with track metadata
        from sqlalchemy import text
        from datetime import datetime
        import random
        
        with SessionLocal() as db:
            # Get existing tracks from database
            result = db.execute(text('SELECT "Track".track_id, "Track".title, "Artist".name, "Track".audio_file_url, NULL::text as cover_url, "Track".duration_ms FROM "Track" LEFT JOIN "TrackArtist" ON "Track".track_id = "TrackArtist".track_id LEFT JOIN "Artist" ON "TrackArtist".artist_id = "Artist".artist_id LIMIT 100'))
            existing_tracks = result.fetchall()
            
            if existing_tracks:
                # Randomly select 5-7 tracks
                num_tracks = random.randint(5, 7)
                selected_tracks = random.sample(existing_tracks, min(num_tracks, len(existing_tracks)))
                
                for idx, track in enumerate(selected_tracks):
                    track_id, title, artist, audio_url, cover_url, duration = track
                    # Check if already in playlist
                    check = db.execute(text(
                        'SELECT 1 FROM "PlaylistTrack" WHERE playlist_id = :pid AND track_id = :tid LIMIT 1'
                    ), {"pid": playlist.id, "tid": track_id}).fetchone()
                    
                    if not check:
                        # Just add the relationship - metadata is in Track table
                        db.execute(text(
                            'INSERT INTO "PlaylistTrack" (playlist_id, track_id, date_added) VALUES (:pid, :tid, :date)'
                        ), {
                            "pid": playlist.id, 
                            "tid": track_id, 
                            "date": datetime.now()
                        })
                        print(f"Added track: {title}")
                
                db.commit()
                print(f"\n✓ Added {len(selected_tracks)} tracks to 'Now Trending' playlist!")
            else:
                print("\nNote: No tracks found in database. The playlist is empty.")
        
    except Exception as e:
        import traceback
        print(f"Error creating trending playlist: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    create_trending_playlist()
