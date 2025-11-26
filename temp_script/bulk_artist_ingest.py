"""
Bulk artist ingestion script.
Randomly selects ~150 artists from MTV CSV and ingests one random album per artist.
"""
import sys
import os
import csv
import random
import time
import requests
from typing import List, Dict, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.supabase_client import supabase
from app.services.spotify_service import get_spotify_token, fetch_spotify_api
from app.services.track_info_and_relationship_service import (
    link_album_artists,
    ensure_artist_genres,
    add_song_info
)
from app.services.album_cover_service import fetch_and_store_album_cover

if not supabase:
    raise Exception("Supabase client not initialized")


def download_csv(url: str) -> List[Dict]:
    """Download and parse CSV from URL."""
    print(f"Downloading CSV from {url}...")
    response = requests.get(url)
    response.raise_for_status()
    
    # Parse CSV
    csv_content = response.text
    reader = csv.DictReader(csv_content.splitlines())
    artists = list(reader)
    
    print(f"Downloaded {len(artists)} artists from CSV")
    return artists


def get_random_artists(artists: List[Dict], count: int = 150) -> List[Dict]:
    """Randomly select artists from the list."""
    if len(artists) <= count:
        return artists
    
    return random.sample(artists, count)


def search_artist_on_spotify(artist_name: str, token: str) -> Optional[Dict]:
    """Search for an artist on Spotify."""
    try:
        # Clean artist name (remove extra spaces, handle special cases)
        clean_name = artist_name.strip()
        
        # Handle special cases like "Joey + Rory" -> "Joey and Rory"
        clean_name = clean_name.replace(' + ', ' and ')
        
        query = f"artist:{clean_name}"
        search_response = fetch_spotify_api(
            f"search?q={query}&type=artist&limit=1",
            token
        )
        
        artists = search_response.get('artists', {}).get('items', [])
        if not artists:
            return None
        
        return artists[0]
    except Exception as e:
        print(f"    > Error searching artist: {e}")
        return None


def get_random_album_for_artist(spotify_artist_id: str, token: str) -> Optional[Dict]:
    """Get a random album for an artist."""
    try:
        # Get artist's albums
        albums_response = fetch_spotify_api(
            f"artists/{spotify_artist_id}/albums?include_groups=album,single&limit=50",
            token
        )
        
        albums = albums_response.get('items', [])
        if not albums:
            return None
        
        # Pick a random album
        random_album = random.choice(albums)
        
        # Get full album data
        full_album_data = fetch_spotify_api(f"albums/{random_album['id']}", token)
        
        return full_album_data
    except Exception as e:
        print(f"    > Error getting album: {e}")
        return None


def ingest_album_with_tracks(spotify_album_data: Dict, csv_genre: Optional[str], token: str) -> bool:
    """Ingest an album and its tracks into the database."""
    try:
        # Get label
        label_name = spotify_album_data.get('label', 'Unknown Label')
        
        # Ingest Label
        label_response = supabase.from_("Label").upsert({"name": label_name}, on_conflict='name').execute()
        db_label = label_response.data[0] if label_response.data else None
        
        if not db_label:
            return False
        
        # Ingest Album
        release_date_str = spotify_album_data.get('release_date', '')
        precision = spotify_album_data.get('release_date_precision', 'day')
        
        formatted_release_date = None
        if release_date_str:
            if precision == 'year':
                formatted_release_date = f"{release_date_str}-01-01"
            elif precision == 'month':
                formatted_release_date = f"{release_date_str}-01"
            elif precision == 'day':
                formatted_release_date = release_date_str
        
        album_to_insert = {
            "title": spotify_album_data.get('name', ''),
            "release_date": formatted_release_date,
            "type": spotify_album_data.get('album_type', 'album'),
            "label_id": db_label['label_id']
        }
        
        # Check if album already exists
        album_response = supabase.from_("Album").select("*").eq("title", album_to_insert['title']).limit(1).execute()
        
        if album_response.data:
            db_album = album_response.data[0]
        else:
            album_insert_response = supabase.from_("Album").insert(album_to_insert).execute()
            if album_insert_response.data:
                db_album = album_insert_response.data[0]
            else:
                return False
        
        # Link Album to Artists
        link_album_artists(
            album_id=db_album['album_id'],
            spotify_album_data=spotify_album_data,
            token=token
        )
        
        # Note: Artist genres are handled before album ingestion in main()
        
        # Ingest tracks from album
        tracks = spotify_album_data.get('tracks', {}).get('items', [])
        tracks_ingested = 0
        
        if not tracks:
            print(f"      > No tracks found in album")
            return False
        
        print(f"      > Processing {min(len(tracks), 20)} tracks from album")
        
        for track_item in tracks[:20]:  # Limit to 20 tracks per album
            try:
                track_id = track_item.get('id')
                track_name = track_item.get('name', 'Unknown')
                
                if not track_id:
                    print(f"      > Skipping track (no ID): {track_name}")
                    continue
                
                # Fetch full track data
                from app.services.spotify_service import fetch_spotify_api, ingest_track_from_spotify
                try:
                    full_track_data = fetch_spotify_api(f"tracks/{track_id}", token)
                except Exception as e:
                    print(f"      > Error fetching track data for '{track_name}': {e}")
                    continue
                
                # Ingest track (with ingest_album=False since we already have the album)
                db_track = ingest_track_from_spotify(full_track_data, token=token, ingest_album=False)
                
                if not db_track:
                    print(f"      > Failed to ingest track: {track_name}")
                    continue
                
                # Link Track to Album
                supabase.from_("AlbumTrack").upsert({
                    "album_id": db_album['album_id'],
                    "track_id": db_track['track_id'],
                    "disc_no": track_item.get('disc_number', 1),
                    "track_no": track_item.get('track_number', 1)
                }, on_conflict='album_id, track_id').execute()
                
                # Add song info
                add_song_info(
                    track_id=db_track['track_id'],
                    spotify_track_data=full_track_data,
                    token=token
                )
                
                tracks_ingested += 1
                print(f"      > ✓ Ingested track: {db_track['title']}")
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"      > Error ingesting track '{track_item.get('name', 'Unknown')}': {e}")
                continue
        
        print(f"      > Successfully ingested {tracks_ingested} track(s)")
        
        # Fetch and store album cover
        fetch_and_store_album_cover(
            album_id=db_album['album_id'],
            spotify_album_data=spotify_album_data,
            token=token,
            skip_if_exists=True
        )
        
        return tracks_ingested > 0
        
    except Exception as e:
        print(f"    > Error ingesting album: {e}")
        return False


def main():
    """Main function to bulk ingest artists."""
    print("=" * 60)
    print("Bulk Artist Ingestion Script")
    print("=" * 60)
    
    # CSV URL
    csv_url = "https://gist.githubusercontent.com/mbejda/9912f7a366c62c1f296c/raw/dd94a25492b3062f4ca0dc2bb2cdf23fec0896ea/10000-MTV-Music-Artists-page-1.csv"
    
    # Download and parse CSV
    all_artists = download_csv(csv_url)
    
    # Get current artist count
    current_artists_response = supabase.from_("Artist").select("artist_id", count="exact").execute()
    current_count = current_artists_response.count if hasattr(current_artists_response, 'count') else len(current_artists_response.data or [])
    print(f"\nCurrent artists in database: {current_count}")
    print(f"Target: ~250 artists (need ~{250 - current_count} more)\n")
    
    # Randomly select ~150 artists
    target_count = 50
    selected_artists = get_random_artists(all_artists, target_count)
    print(f"Selected {len(selected_artists)} artists to process\n")
    
    # Get Spotify token
    token = get_spotify_token()
    print("Spotify token acquired.\n")
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for idx, artist_row in enumerate(selected_artists, 1):
        artist_name = artist_row.get('name', '').strip()
        csv_genre = artist_row.get('genre', '').strip() if artist_row.get('genre') else None
        
        if not artist_name:
            skipped_count += 1
            continue
        
        print(f"[{idx}/{len(selected_artists)}] Processing: {artist_name}")
        if csv_genre:
            print(f"  CSV Genre: {csv_genre}")
        
        # Search for artist on Spotify
        spotify_artist = search_artist_on_spotify(artist_name, token)
        
        if not spotify_artist:
            print(f"  > ✗ Artist not found on Spotify")
            error_count += 1
            time.sleep(0.2)
            continue
        
        spotify_artist_id = spotify_artist['id']
        spotify_artist_name = spotify_artist['name']
        print(f"  > Found on Spotify: {spotify_artist_name} (ID: {spotify_artist_id})")
        
        # Check if artist already exists in database
        existing_artist = supabase.from_("Artist").select("artist_id").eq("name", spotify_artist_name).limit(1).execute()
        if existing_artist.data:
            print(f"  > Artist already exists in database, skipping")
            skipped_count += 1
            time.sleep(0.2)
            continue
        
        # Ingest artist
        artist_insert = {"name": spotify_artist_name}
        artist_response = supabase.from_("Artist").upsert(artist_insert, on_conflict='name').execute()
        
        if not artist_response.data:
            print(f"  > ✗ Failed to ingest artist")
            error_count += 1
            time.sleep(0.2)
            continue
        
        db_artist = artist_response.data[0]
        print(f"  > ✓ Ingested Artist: {spotify_artist_name} (ID: {db_artist['artist_id']})")
        
        # Get random album
        album_data = get_random_album_for_artist(spotify_artist_id, token)
        
        if not album_data:
            print(f"  > ✗ No albums found for artist")
            error_count += 1
            time.sleep(0.2)
            continue
        
        album_title = album_data.get('name', 'Unknown')
        print(f"  > Selected album: {album_title}")
        
        # Ensure artist genres first (before album ingestion)
        ensure_artist_genres(
            artist_id=db_artist['artist_id'],
            spotify_artist_id=spotify_artist_id,
            token=token
        )
        
        # If no genres found and CSV genre exists, add it
        ag_check = supabase.from_("ArtistGenre").select("genre_id").eq("artist_id", db_artist['artist_id']).limit(1).execute()
        if not ag_check.data and csv_genre:
            genre_response = supabase.from_("Genre").upsert({"name": csv_genre}, on_conflict='name').execute()
            if genre_response.data:
                db_genre = genre_response.data[0]
                supabase.from_("ArtistGenre").upsert({
                    "artist_id": db_artist['artist_id'],
                    "genre_id": db_genre['genre_id']
                }, on_conflict='artist_id, genre_id').execute()
                print(f"  > Added CSV genre: {csv_genre}")
        
        # Ingest album and tracks
        if ingest_album_with_tracks(album_data, csv_genre, token):
            print(f"  > ✓ Successfully ingested album and tracks")
            success_count += 1
        else:
            print(f"  > ✗ Failed to ingest album")
            error_count += 1
        
        # Rate limiting
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("Bulk ingestion complete!")
    print(f"  Success: {success_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total processed: {len(selected_artists)}")
    print("=" * 60)


if __name__ == "__main__":
    main()

