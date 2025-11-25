"""
Spotify data ingestion script - ingests artists, albums, tracks, genres, labels, and work credits.
Note: Audio features are now ingested separately using scripts/audio_features_ingest.py
"""
import sys
import os
import time
from datetime import datetime, timezone

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.spotify_service import (
    get_spotify_token,
    fetch_spotify_api,
    get_preview_url_workaround,
    ingest_track_from_spotify
)
from app.services.audio_features_service import fetch_and_save_audio_features
from app.db.supabase_client import supabase

if not supabase:
    raise Exception("Supabase client not initialized")


def ingest_data(artist_name):
    """Main ingestion function for artist data."""
    try:
        print("Starting ingestion process...")
        token = get_spotify_token()
        print("Spotify token acquired.")

        # STEP 1: Ingest Artist
        print(f"Searching for artist: {artist_name}")
        artist_data = fetch_spotify_api(f"search?q={artist_name}&type=artist&limit=1", token)
        spotify_artist = artist_data['artists']['items'][0]

        if not spotify_artist:
            print(f"Artist \"{artist_name}\" not found.")
            return

        artist_to_insert = {
            "name": spotify_artist['name'],
            "bio": f"Genres: {', '.join(spotify_artist['genres'])}",
            "type": 'Solo' if spotify_artist['type'] == 'artist' else 'Group'
        }
        
        response = supabase.from_("Artist").upsert(artist_to_insert, on_conflict='name').execute()
        if response.data:
            db_artist = response.data[0]
            print(f"Successfully ingested Artist: {db_artist['name']} (ID: {db_artist['artist_id']})")
        else:
            raise Exception(f"Failed to insert artist: {response.error.message if response.error else 'No data returned'}")

        # STEP 1a: Ingest Genres for Artist
        artist_genres = spotify_artist.get('genres', [])
        for genre_name in artist_genres:
            if genre_name:
                genre_response = supabase.from_("Genre").upsert({"name": genre_name}, on_conflict='name').execute()
                if genre_response.data:
                    db_genre = genre_response.data[0]
                    supabase.from_("ArtistGenre").upsert({
                        "artist_id": db_artist['artist_id'],
                        "genre_id": db_genre['genre_id']
                    }, on_conflict='artist_id, genre_id').execute()
                    print(f"  > Linked Genre: {db_genre['name']} to Artist")

        # STEP 2: Ingest Albums
        print(f"Fetching albums for {db_artist['name']}...")
        albums_data = fetch_spotify_api(f"artists/{spotify_artist['id']}/albums?include_groups=album,single&limit=3", token)

        for spotify_album in albums_data['items']:
            time.sleep(1)  # Rate limiting
            full_album_data = fetch_spotify_api(f"albums/{spotify_album['id']}", token)
            label_name = full_album_data.get('label', 'Unknown Label')

            # STEP 2a: Ingest Label
            label_response = supabase.from_("Label").upsert({"name": label_name}, on_conflict='name').execute()
            db_label = label_response.data[0]
            print(f"  > Ingested Label: {db_label['name']}")

            # STEP 2b: Ingest Album
            release_date_str = full_album_data['release_date']
            precision = full_album_data['release_date_precision']
            
            formatted_release_date = None
            if precision == 'year':
                formatted_release_date = f"{release_date_str}-01-01"
            elif precision == 'month':
                formatted_release_date = f"{release_date_str}-01"
            elif precision == 'day':
                formatted_release_date = release_date_str

            album_to_insert = {
                "title": full_album_data['name'],
                "release_date": formatted_release_date,
                "type": full_album_data['album_type'],
                "label_id": db_label['label_id']
            }
            
            album_response = supabase.from_("Album").insert(album_to_insert).execute()
            
            if not album_response.data:
                album_response = supabase.from_("Album").select("*").eq("title", full_album_data['name']).limit(1).execute()
                if not album_response.data:
                    print(f"  > Skipping Album (failed insert/select): {full_album_data['name']}")
                    continue
            
            db_album = album_response.data[0]
            print(f"  > Ingested Album: {db_album['title']}")

            # Link Album and Artist
            supabase.from_("AlbumArtist").upsert({
                "album_id": db_album['album_id'],
                "artist_id": db_artist['artist_id']
            }, on_conflict='album_id, artist_id').execute()

            # Ingest Tracks
            for spotify_track in full_album_data['tracks']['items']:
                # Use the service function to ingest track (handles spotify_id, isrc, etc.)
                db_track = ingest_track_from_spotify(spotify_track, token)
                
                if not db_track:
                    print(f"    > Skipping Track (failed to ingest): {spotify_track['name']}")
                    continue
                
                print(f"    > Ingested/Updated Track: {db_track['title']} (Spotify ID: {db_track.get('spotify_id', 'None')})")

                # Link Track to Album
                supabase.from_("AlbumTrack").upsert({
                    "album_id": db_album['album_id'],
                    "track_id": db_track['track_id'],
                    "disc_no": spotify_track['disc_number'],
                    "track_no": spotify_track['track_number']
                }, on_conflict='album_id, track_id').execute()

                # Link Track to Artist (if not already linked by ingest_track_from_spotify)
                supabase.from_("TrackArtist").upsert({
                    "track_id": db_track['track_id'],
                    "artist_id": db_artist['artist_id'],
                    "role": 'Main'
                }, on_conflict='track_id, artist_id, role').execute()
                
                # Fetch and save audio features
                try:
                    artist_name = db_artist.get('name')
                    success = fetch_and_save_audio_features(
                        track_id=db_track['track_id'],
                        track_title=db_track['title'],
                        artist_name=artist_name,
                        duration_ms=db_track['duration_ms'],
                        spotify_track_id=db_track.get('spotify_id') or spotify_track['id']
                    )
                    if success:
                        print(f"      > Fetched and saved audio features")
                    else:
                        print(f"      > Could not fetch audio features")
                except Exception as e:
                    print(f"      > Error fetching audio features: {e}")

                # STEP 3a: Link Genres to Track
                for genre_name in artist_genres:
                    if genre_name:
                        genre_response = supabase.from_("Genre").select("*").eq("name", genre_name).limit(1).execute()
                        if genre_response.data:
                            db_genre = genre_response.data[0]
                            supabase.from_("TrackGenre").upsert({
                                "track_id": db_track['track_id'],
                                "genre_id": db_genre['genre_id']
                            }, on_conflict='track_id, genre_id').execute()

                # STEP 3b: Ingest Work Credits
                isrc = spotify_track['external_ids'].get('isrc')
                if isrc:
                    try:
                        work_response = supabase.from_("Work").select("*").eq("title", spotify_track['name']).limit(1).execute()
                        
                        if work_response.data:
                            db_work = work_response.data[0]
                        else:
                            work_to_insert = {"title": spotify_track['name']}
                            work_response = supabase.from_("Work").insert(work_to_insert).execute()
                            if work_response.data:
                                db_work = work_response.data[0]
                            else:
                                continue
                        
                        supabase.from_("TrackWork").upsert({
                            "track_id": db_track['track_id'],
                            "work_id": db_work['work_id']
                        }, on_conflict='track_id, work_id').execute()
                        
                        supabase.from_("WorkComposer").upsert({
                            "work_id": db_work['work_id'],
                            "artist_id": db_artist['artist_id']
                        }, on_conflict='work_id, artist_id').execute()
                        print(f"      > Created/Linked Work entry for track")
                    except Exception as e:
                        print(f"      > Error creating work entry: {e}")

        print("Ingestion process completed successfully!")

    except Exception as e:
        print(f"An error occurred during ingestion: {e}")


if __name__ == "__main__":
    band = input("What band? ")
    ingest_data(band)

