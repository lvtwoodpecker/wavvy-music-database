"""
Spotify playlist and listening history ingestion script.
"""
import sys
import os
import time
import hashlib
from datetime import datetime, timezone

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.spotify_service import (
    get_spotify_token,
    fetch_spotify_api,
    ingest_track_from_spotify
)
from app.services.track_info_and_relationship_service import add_song_info
from app.db.supabase_client import supabase
from app.config import settings

if not supabase:
    raise Exception("Supabase client not initialized")


def get_or_create_user(username="cedricster", email=None, country="US"):
    """Get or create a user in the database."""
    if email is None:
        email = f"{username}@wavvy.local"
    
    password_hash = hashlib.sha256(f"{username}_demo_password".encode()).hexdigest()
    
    user_data = {
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "country": country
    }
    
    existing_user = supabase.from_("User").select("*").eq("username", username).limit(1).execute()
    
    if existing_user.data:
        print(f"Found existing user: {existing_user.data[0]['username']} (ID: {existing_user.data[0]['user_id']})")
        return existing_user.data[0]
    
    user_response = supabase.from_("User").insert(user_data).execute()
    
    if not user_response.data:
        raise Exception("Failed to create user")
    
    print(f"Created user: {user_response.data[0]['username']} (ID: {user_response.data[0]['user_id']})")
    return user_response.data[0]


def get_or_create_listener(user_id):
    """Get or create a listener linked to a user."""
    existing_listener = supabase.from_("Listener").select("*").eq("user_id", user_id).limit(1).execute()
    
    if existing_listener.data:
        print(f"Found existing listener (ID: {existing_listener.data[0]['listener_id']})")
        return existing_listener.data[0]
    
    listener_data = {
        "user_id": user_id,
        "ad_free": False,
        "payment_amt": 0.00
    }
    
    listener_response = supabase.from_("Listener").insert(listener_data).execute()
    
    if not listener_response.data:
        raise Exception("Failed to create listener")
    
    print(f"Created listener (ID: {listener_response.data[0]['listener_id']})")
    return listener_response.data[0]


def get_user_playlists(user_token, limit=50, retry_with_new_token=True):
    """Fetch user's playlists from Spotify API."""
    all_playlists = []
    url = f"me/playlists?limit={min(limit, 120)}"
    
    while url and len(all_playlists) < limit:
        time.sleep(0.2)
        if url.startswith("http"):
            endpoint = url.replace("https://api.spotify.com/v1/", "")
        else:
            endpoint = url
        
        try:
            data = fetch_spotify_api(endpoint, user_token)
            playlists = data.get('items', [])
            all_playlists.extend(playlists)
            url = data.get('next')
            
            if not url:
                break
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "expired" in error_msg.lower() or "Unauthorized" in error_msg:
                if retry_with_new_token:
                    print(f"\nToken expired: {error_msg}")
                    new_token = handle_token_expired()
                    if new_token:
                        user_token = new_token
                        continue  # Retry with new token
                    else:
                        break  # User chose to exit
                else:
                    raise
            else:
                raise
    
    return all_playlists[:limit], user_token  # Return updated token


def get_playlist_tracks(user_token, playlist_id, retry_with_new_token=True):
    """Fetch tracks from a specific playlist."""
    all_tracks = []
    url = f"playlists/{playlist_id}/tracks?limit=100"
    
    while url:
        time.sleep(0.2)
        if url.startswith("http"):
            endpoint = url.replace("https://api.spotify.com/v1/", "")
        else:
            endpoint = url
        
        try:
            data = fetch_spotify_api(endpoint, user_token)
            items = data.get('items', [])
            all_tracks.extend(items)
            url = data.get('next')
            
            if not url:
                break
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "expired" in error_msg.lower() or "Unauthorized" in error_msg:
                if retry_with_new_token:
                    print(f"\nToken expired: {error_msg}")
                    new_token = handle_token_expired()
                    if new_token:
                        user_token = new_token
                        continue  # Retry with new token
                    else:
                        break  # User chose to exit
                else:
                    raise
            else:
                raise
    
    return all_tracks, user_token  # Return updated token


def handle_token_expired():
    """Handle expired token by prompting user to get a new one."""
    print("\n" + "="*60)
    print("⚠️  TOKEN EXPIRED - New token required")
    print("="*60)
    print("\nYour Spotify access token has expired.")
    print("\nOptions:")
    print("1. Run the token getter script now")
    print("2. Enter a new token manually")
    print("3. Exit and get token later")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        print("\nOpening token getter...")
        import subprocess
        try:
            # Get the script directory and construct absolute path
            script_dir = os.path.dirname(os.path.abspath(__file__))
            token_script_path = os.path.join(script_dir, "get_token.py")
            project_root = os.path.dirname(script_dir)
            
            # Run from project root to ensure imports work
            subprocess.run(["python", token_script_path], cwd=project_root, check=False)
            print("\nAfter getting your token, run this script again with:")
            print("  SPOTIFY_USER_TOKEN=your_new_token python scripts/spotify_playlist_ingest.py")
        except Exception as e:
            print(f"Could not run token getter: {e}")
            print("Please run manually: python scripts/get_token.py")
        return None
    elif choice == "2":
        new_token = input("Enter your new Spotify user access token: ").strip()
        if new_token:
            return new_token
        return None
    else:
        print("Exiting. Get a new token and try again.")
        return None


def get_recently_played_tracks(user_token, limit=50, retry_with_new_token=True):
    """Fetch user's recently played tracks from Spotify.
    
    Returns:
        If retry_with_new_token is True: (tracks_list, token) tuple
        If retry_with_new_token is False: tracks_list only
    """
    endpoint = f"me/player/recently-played?limit={min(limit, 50)}"
    
    try:
        data = fetch_spotify_api(endpoint, user_token)
        tracks = data.get('items', [])
        if retry_with_new_token:
            return tracks, user_token
        return tracks
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "expired" in error_msg.lower() or "Unauthorized" in error_msg:
            if retry_with_new_token:
                print(f"\nToken expired: {error_msg}")
                new_token = handle_token_expired()
                if new_token:
                    # Retry with new token
                    try:
                        data = fetch_spotify_api(endpoint, new_token)
                        tracks = data.get('items', [])
                        return tracks, new_token  # Return token too so caller can update it
                    except Exception as e2:
                        print(f"Error with new token: {e2}")
                        return [], new_token
                return [], user_token
            else:
                print(f"Error fetching recently played tracks: {e}")
                return []
        else:
            print(f"Error fetching recently played tracks: {e}")
            if retry_with_new_token:
                return [], user_token
            return []


def find_track_by_isrc_or_title(isrc=None, title=None, duration_ms=None):
    """Find a track in the database by ISRC or title+duration."""
    if isrc:
        track_response = supabase.from_("Track").select("*").eq("isrc", isrc).limit(1).execute()
        if track_response.data:
            return track_response.data[0]
    
    if title and duration_ms:
        track_response = supabase.from_("Track").select("*").eq("title", title).eq("duration_ms", duration_ms).limit(1).execute()
        if track_response.data:
            return track_response.data[0]
    
    return None


def ingest_playlist_from_spotify(playlist_data, listener_id, user_token, max_tracks_to_ingest=10):
    """Ingest a playlist from Spotify API data.
    
    Args:
        playlist_data: Spotify playlist data
        listener_id: Database listener ID
        user_token: Spotify user access token
        max_tracks_to_ingest: Maximum number of new tracks to ingest from this playlist
    """
    playlist_name = playlist_data.get('name', 'Unnamed Playlist')
    playlist_id_spotify = playlist_data.get('id')
    is_public = playlist_data.get('public', True)
    is_collaborative = playlist_data.get('collaborative', False)
    created_at = playlist_data.get('created_at') or datetime.now(timezone.utc).isoformat()
    
    print(f"\nProcessing playlist: {playlist_name}")
    
    playlist_to_insert = {
        "owner_listener_id": listener_id,
        "title": playlist_name,
        "created_at": created_at,
        "is_public": is_public,
        "is_collaborative": is_collaborative
    }
    
    existing_playlist = supabase.from_("Playlist").select("*").eq("title", playlist_name).eq("owner_listener_id", listener_id).limit(1).execute()
    
    if existing_playlist.data:
        db_playlist = existing_playlist.data[0]
        print(f"  > Using existing playlist: {playlist_name} (ID: {db_playlist['playlist_id']})")
    else:
        playlist_response = supabase.from_("Playlist").insert(playlist_to_insert).execute()
        if not playlist_response.data:
            print(f"  > Failed to create playlist: {playlist_name}")
            return
        db_playlist = playlist_response.data[0]
        print(f"  > Created playlist: {playlist_name} (ID: {db_playlist['playlist_id']})")
    
    try:
        tracks_data, user_token = get_playlist_tracks(user_token, playlist_id_spotify)
        print(f"  > Found {len(tracks_data)} tracks in playlist")
        
        added_count = 0
        skipped_count = 0
        ingested_count = 0
        
        try:
            client_token = get_spotify_token()
        except Exception as e:
            print(f"  > Warning: Could not get client token for track ingestion: {e}")
            client_token = None
        
        for idx, track_item in enumerate(tracks_data, 1):
            if not track_item.get('track') or track_item['track'] is None:
                skipped_count += 1
                continue
            
            spotify_track = track_item['track']
            added_at = track_item.get('added_at', datetime.now(timezone.utc).isoformat())
            
            isrc = spotify_track.get('external_ids', {}).get('isrc')
            track_title = spotify_track.get('name')
            duration_ms = spotify_track.get('duration_ms')
            
            db_track = find_track_by_isrc_or_title(isrc=isrc, title=track_title, duration_ms=duration_ms)
            
            if not db_track and client_token and ingested_count < max_tracks_to_ingest:
                print(f"    [{idx}] Track not in database, attempting to ingest: {track_title}")
                db_track = ingest_track_from_spotify(spotify_track, token=client_token, ingest_album=True)
                if db_track:
                    ingested_count += 1
                    print(f"      > Successfully ingested track: {track_title}")
                    
                    # Add song info: audio features, genres, etc.
                    add_song_info(
                        track_id=db_track['track_id'],
                        spotify_track_data=spotify_track,
                        token=client_token
                    )
                    
                    # Fetch album cover if album was created
                    if spotify_track.get('album'):
                        from app.services.album_cover_service import fetch_and_store_album_cover
                        from app.services.spotify_service import fetch_spotify_api
                        # Get album_id from AlbumTrack relationship
                        at_response = supabase.from_("AlbumTrack").select("album_id").eq("track_id", db_track['track_id']).limit(1).execute()
                        if at_response.data:
                            album_id = at_response.data[0]['album_id']
                            # Fetch full album data for cover
                            album_id_spotify = spotify_track['album'].get('id')
                            if album_id_spotify:
                                try:
                                    full_album_data = fetch_spotify_api(f"albums/{album_id_spotify}", client_token)
                                    fetch_and_store_album_cover(
                                        album_id=album_id,
                                        spotify_album_data=full_album_data,
                                        token=client_token,
                                        skip_if_exists=True
                                    )
                                except Exception:
                                    pass  # Silently fail if cover fetch fails
                    
                    time.sleep(0.2)
                else:
                    print(f"      > Failed to ingest track: {track_title}")
            
            if not db_track:
                print(f"    [{idx}] Skipping track (not in database): {track_title}")
                skipped_count += 1
                continue
            
            # For existing tracks, add song info if missing
            if db_track:
                add_song_info(
                    track_id=db_track['track_id'],
                    spotify_track_data=spotify_track,
                    token=client_token
                )
            
            playlist_track_data = {
                "playlist_id": db_playlist['playlist_id'],
                "track_id": db_track['track_id'],
                "date_added": added_at,
                "added_by_user_id": listener_id
            }
            
            existing_pt = supabase.from_("PlaylistTrack").select("*").eq("playlist_id", db_playlist['playlist_id']).eq("track_id", db_track['track_id']).eq("date_added", added_at).limit(1).execute()
            
            if not existing_pt.data:
                supabase.from_("PlaylistTrack").insert(playlist_track_data).execute()
                added_count += 1
            else:
                skipped_count += 1
        
        print(f"  > Added {added_count} tracks, ingested {ingested_count} new tracks, skipped {skipped_count} tracks")
        
    except Exception as e:
        print(f"  > Error fetching tracks: {e}")


def ingest_playlists_from_spotify_api(username="cedricster", user_token=None, limit=50, max_tracks_per_playlist=10):
    """Main function to ingest playlists from Spotify API.
    
    Args:
        username: Username for the user/listener
        user_token: Spotify user access token
        limit: Maximum number of playlists to fetch
        max_tracks_per_playlist: Maximum number of new tracks to ingest per playlist
    """
    if not user_token:
        print("ERROR: User access token is required.")
        return
    
    try:
        user = get_or_create_user(username=username)
        listener = get_or_create_listener(user['user_id'])
        
        print(f"\nFetching playlists from Spotify...")
        playlists, user_token = get_user_playlists(user_token, limit=limit)
        print(f"Found {len(playlists)} playlists")
        
        for playlist in playlists:
            ingest_playlist_from_spotify(playlist, listener['listener_id'], user_token, max_tracks_to_ingest=max_tracks_per_playlist)
            time.sleep(0.5)
        
        print(f"\n✓ Successfully ingested {len(playlists)} playlists!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()


def ingest_listening_history(username="cedricster", user_token=None, limit=50, max_tracks_to_ingest=10):
    """Ingest user's listening history from Spotify into PlayHistory table."""
    if not user_token:
        print("ERROR: User access token is required.")
        return
    
    try:
        user = get_or_create_user(username=username)
        listener = get_or_create_listener(user['user_id'])
        
        try:
            client_token = get_spotify_token()
        except Exception as e:
            print(f"Warning: Could not get client token for track ingestion: {e}")
            client_token = None
        
        print(f"\nFetching recently played tracks (limit: {limit})...")
        recently_played, user_token = get_recently_played_tracks(user_token, limit=limit)
        
        if not recently_played:
            print("\n⚠️  No recently played tracks found or error occurred.")
            print("Make sure your token has 'user-read-recently-played' scope")
            return
        
        print(f"Found {len(recently_played)} recently played tracks")
        
        added_count = 0
        skipped_count = 0
        ingested_count = 0
        
        for idx, item in enumerate(recently_played, 1):
            spotify_track = item.get('track')
            if not spotify_track:
                skipped_count += 1
                continue
            
            played_at_ms = item.get('played_at')
            if not played_at_ms:
                skipped_count += 1
                continue
            
            try:
                played_at_dt = datetime.fromisoformat(played_at_ms.replace('Z', '+00:00'))
                played_at_iso = played_at_dt.isoformat()
            except:
                try:
                    played_at_dt = datetime.fromtimestamp(int(played_at_ms) / 1000, tz=timezone.utc)
                    played_at_iso = played_at_dt.isoformat()
                except:
                    played_at_iso = datetime.now(timezone.utc).isoformat()
            
            isrc = spotify_track.get('external_ids', {}).get('isrc')
            track_title = spotify_track.get('name')
            duration_ms = spotify_track.get('duration_ms')
            
            db_track = find_track_by_isrc_or_title(isrc=isrc, title=track_title, duration_ms=duration_ms)
            
            if not db_track and client_token and ingested_count < max_tracks_to_ingest:
                print(f"  [{idx}] Track not in database, attempting to ingest: {track_title}")
                db_track = ingest_track_from_spotify(spotify_track, token=client_token)
                if db_track:
                    ingested_count += 1
                    print(f"    > Successfully ingested track: {track_title}")
                    
                    # Add song info: audio features, genres, etc.
                    add_song_info(
                        track_id=db_track['track_id'],
                        spotify_track_data=spotify_track,
                        token=client_token
                    )
                    
                    time.sleep(0.2)
                else:
                    print(f"    > Failed to ingest track: {track_title}")
            
            if not db_track:
                print(f"  [{idx}] Skipping track (not in database): {track_title}")
                skipped_count += 1
                continue
            
            # For existing tracks, add song info if missing
            if db_track:
                add_song_info(
                    track_id=db_track['track_id'],
                    spotify_track_data=spotify_track,
                    token=client_token
                )
            
            play_history_data = {
                "listener_id": listener['listener_id'],
                "track_id": db_track['track_id'],
                "played_at": played_at_iso,
                "is_skip": False
            }
            
            existing_ph = supabase.from_("PlayHistory").select("*").eq(
                "listener_id", listener['listener_id']
            ).eq("track_id", db_track['track_id']).eq("played_at", played_at_iso).limit(1).execute()
            
            if not existing_ph.data:
                try:
                    supabase.from_("PlayHistory").insert(play_history_data).execute()
                    added_count += 1
                except Exception as e:
                    print(f"    > Error adding to play history: {e}")
                    skipped_count += 1
            else:
                skipped_count += 1
        
        print(f"\n✓ Listening history ingestion complete!")
        print(f"  Added: {added_count} plays")
        print(f"  Ingested: {ingested_count} new tracks")
        print(f"  Skipped: {skipped_count} tracks")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Spotify Data Ingestion Script")
    print("=" * 50)
    
    # Try to get token from env or settings
    user_token = os.environ.get("SPOTIFY_USER_TOKEN") or getattr(settings, 'SPOTIFY_USER_TOKEN', None)
    
    if not user_token:
        print("\nTo use this script, you need a Spotify user access token.")
        print("IMPORTANT: The token must include these scopes:")
        print("  - playlist-read-private")
        print("  - playlist-read-collaborative")
        print("  - user-read-recently-played (for listening history)")
        print("\nGet a new token using: python scripts/get_token.py")
        print("Or set SPOTIFY_USER_TOKEN in your .env file")
        print()
        user_token = input("Enter your Spotify user access token (or press Enter to skip): ").strip()
        
        if not user_token:
            print("No token provided. Exiting.")
            exit(0)
    
    username = input("Enter username (default: cedricster): ").strip() or "cedricster"
    
    print("\nWhat would you like to ingest?")
    print("1. Playlists")
    print("2. Listening History")
    print("3. Both")
    choice = input("Enter choice (1-3, default: 1): ").strip() or "1"
    
    if choice in ["1", "3"]:
        limit_input = input("Enter max number of playlists to ingest (default: 50): ").strip()
        limit = int(limit_input) if limit_input else 50
        
        tracks_per_playlist_input = input("Enter max number of new tracks to ingest per playlist (default: 10): ").strip()
        max_tracks_per_playlist = int(tracks_per_playlist_input) if tracks_per_playlist_input else 10
        
        ingest_playlists_from_spotify_api(
            username=username, 
            user_token=user_token, 
            limit=limit,
            max_tracks_per_playlist=max_tracks_per_playlist
        )
    
    if choice in ["2", "3"]:
        history_limit_input = input("Enter max number of recent tracks to fetch (default: 50): ").strip()
        history_limit = int(history_limit_input) if history_limit_input else 50
        ingest_listening_history(username=username, user_token=user_token, limit=history_limit)

