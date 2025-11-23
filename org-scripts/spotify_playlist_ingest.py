import os
import json
import time
import hashlib
import base64
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

# Import track ingestion function from spotify_data_ingest
from spotify_data_ingest import ingest_track_from_spotify, get_spotify_token

# ---
# 1. SETUP
# ---
load_dotenv()
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
if not supabase_url or not supabase_key:
    raise Exception("Supabase URL or Service Key is missing in .env file")
supabase: Client = create_client(supabase_url, supabase_key)

# ---
# 2. USER/LISTENER CREATION
# ---
def get_or_create_user(username="cedricster", email=None, country="US"):
    """
    Get or create a user in the database.
    
    Args:
        username: Username (default: "cedricster")
        email: Email address (if None, generates fake email)
        country: Country code (default: "US")
    
    Returns:
        User record from database
    """
    if email is None:
        email = f"{username}@wavvy.local"
    
    # Generate a fake password hash (for demo purposes)
    # In production, this should be a proper bcrypt hash
    password_hash = hashlib.sha256(f"{username}_demo_password".encode()).hexdigest()
    
    user_data = {
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "country": country
    }
    
    # Try to get existing user
    existing_user = supabase.from_("User").select("*").eq("username", username).limit(1).execute()
    
    if existing_user.data:
        print(f"Found existing user: {existing_user.data[0]['username']} (ID: {existing_user.data[0]['user_id']})")
        return existing_user.data[0]
    
    # Create new user
    user_response = supabase.from_("User").insert(user_data).execute()
    
    if not user_response.data:
        raise Exception("Failed to create user")
    
    print(f"Created user: {user_response.data[0]['username']} (ID: {user_response.data[0]['user_id']})")
    return user_response.data[0]

def get_or_create_listener(user_id):
    """
    Get or create a listener linked to a user.
    
    Args:
        user_id: User ID to link listener to
    
    Returns:
        Listener record from database
    """
    # Check if listener already exists for this user
    existing_listener = supabase.from_("Listener").select("*").eq("user_id", user_id).limit(1).execute()
    
    if existing_listener.data:
        print(f"Found existing listener (ID: {existing_listener.data[0]['listener_id']})")
        return existing_listener.data[0]
    
    # Create new listener
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

# ---
# 3. SPOTIFY API HELPERS
# ---
def fetch_spotify_api(endpoint, token, retry_count=0, max_retries=2):
    """
    Fetch data from Spotify API with error handling and rate limiting.
    """
    url = f"https://api.spotify.com/v1/{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 1))
            if retry_count < max_retries:
                print(f"  > Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return fetch_spotify_api(endpoint, token, retry_count + 1, max_retries)
            else:
                raise Exception(f"Spotify API Rate Limit: Max retries exceeded")
        
        if response.status_code == 403:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Forbidden')
            raise Exception(f"Spotify API Forbidden (403): {error_msg}")
        
        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {}).get('message', response.text)
            raise Exception(f"Spotify API Error ({response.status_code}): {error_msg}")
        
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {str(e)}")

def get_user_playlists(user_token, limit=50):
    """
    Fetch user's playlists from Spotify API.
    Requires user authentication token (OAuth).
    
    Args:
        user_token: Spotify user access token (from OAuth flow)
        limit: Maximum number of playlists to fetch
    
    Returns:
        List of playlist objects
    """
    all_playlists = []
    url = f"https://api.spotify.com/v1/me/playlists?limit={min(limit, 50)}"
    
    while url and len(all_playlists) < limit:
        time.sleep(0.2)  # Rate limiting
        data = fetch_spotify_api(url.replace("https://api.spotify.com/v1/", ""), user_token)
        
        playlists = data.get('items', [])
        all_playlists.extend(playlists)
        
        url = data.get('next')  # Get next page URL
        
        if not url:
            break
    
    return all_playlists[:limit]

def get_playlist_tracks(user_token, playlist_id):
    """
    Fetch tracks from a specific playlist.
    
    Args:
        user_token: Spotify user access token
        playlist_id: Spotify playlist ID
    
    Returns:
        List of track objects with added_at timestamp
    """
    all_tracks = []
    url = f"playlists/{playlist_id}/tracks?limit=100"
    
    while url:
        time.sleep(0.2)  # Rate limiting
        if url.startswith("http"):
            endpoint = url.replace("https://api.spotify.com/v1/", "")
        else:
            endpoint = url
        
        data = fetch_spotify_api(endpoint, user_token)
        
        items = data.get('items', [])
        all_tracks.extend(items)
        
        url = data.get('next')  # Get next page URL
        
        if not url:
            break
    
    return all_tracks

def get_recently_played_tracks(user_token, limit=50, after=None, before=None):
    """
    Fetch user's recently played tracks from Spotify.
    Requires 'user-read-recently-played' scope.
    
    Args:
        user_token: Spotify user access token
        limit: Maximum number of tracks to fetch (1-50)
        after: Unix timestamp in milliseconds - get tracks after this time
        before: Unix timestamp in milliseconds - get tracks before this time
    
    Returns:
        List of track objects with played_at timestamp
    """
    endpoint = f"me/player/recently-played?limit={min(limit, 50)}"
    if after:
        endpoint += f"&after={after}"
    if before:
        endpoint += f"&before={before}"
    
    try:
        data = fetch_spotify_api(endpoint, user_token)
        return data.get('items', [])
    except Exception as e:
        print(f"Error fetching recently played tracks: {e}")
        return []

# ---
# 4. PLAYLIST INGESTION
# ---
def find_track_by_spotify_id(spotify_track_id):
    """
    Find a track in the database by Spotify ID (via ISRC or title matching).
    This is a simplified version - you may need to enhance this.
    """
    # First, try to find by searching for tracks that might match
    # Since we don't store Spotify IDs directly, we'll need to match by ISRC or title
    # For now, return None and we'll handle it in the ingestion
    return None

def find_track_by_isrc_or_title(isrc=None, title=None, duration_ms=None):
    """
    Find a track in the database by ISRC, or by title+duration if ISRC not available.
    """
    if isrc:
        track_response = supabase.from_("Track").select("*").eq("isrc", isrc).limit(1).execute()
        if track_response.data:
            return track_response.data[0]
    
    if title and duration_ms:
        track_response = supabase.from_("Track").select("*").eq("title", title).eq("duration_ms", duration_ms).limit(1).execute()
        if track_response.data:
            return track_response.data[0]
    
    return None

def ingest_playlist_from_spotify(playlist_data, listener_id, user_token):
    """
    Ingest a playlist from Spotify API data.
    
    Args:
        playlist_data: Playlist object from Spotify API
        listener_id: Listener ID who owns the playlist
        user_token: Spotify user access token (for fetching tracks)
    """
    playlist_name = playlist_data.get('name', 'Unnamed Playlist')
    playlist_id_spotify = playlist_data.get('id')
    is_public = playlist_data.get('public', True)
    is_collaborative = playlist_data.get('collaborative', False)
    created_at = playlist_data.get('created_at') or datetime.now(timezone.utc).isoformat()
    
    print(f"\nProcessing playlist: {playlist_name}")
    
    # Create or get playlist
    playlist_to_insert = {
        "owner_listener_id": listener_id,
        "title": playlist_name,
        "created_at": created_at,
        "is_public": is_public,
        "is_collaborative": is_collaborative
    }
    
    # Check if playlist already exists (by title and owner)
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
    
    # Fetch tracks from playlist
    try:
        tracks_data = get_playlist_tracks(user_token, playlist_id_spotify)
        print(f"  > Found {len(tracks_data)} tracks in playlist")
        
        added_count = 0
        skipped_count = 0
        ingested_count = 0
        max_tracks_to_ingest = 8  # Limit to 8 tracks per playlist to keep it light
        
        # Get client credentials token for track ingestion
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
            
            # Try to find track in database
            isrc = spotify_track.get('external_ids', {}).get('isrc')
            track_title = spotify_track.get('name')
            duration_ms = spotify_track.get('duration_ms')
            
            db_track = find_track_by_isrc_or_title(isrc=isrc, title=track_title, duration_ms=duration_ms)
            
            # If track not found and we haven't exceeded the limit, try to ingest it
            if not db_track and client_token and ingested_count < max_tracks_to_ingest:
                print(f"    [{idx}] Track not in database, attempting to ingest: {track_title}")
                db_track = ingest_track_from_spotify(spotify_track, token=client_token)
                if db_track:
                    ingested_count += 1
                    print(f"      > Successfully ingested track: {track_title}")
                    time.sleep(0.2)  # Small delay to respect rate limits
                else:
                    print(f"      > Failed to ingest track: {track_title}")
            
            if not db_track:
                print(f"    [{idx}] Skipping track (not in database): {track_title}")
                skipped_count += 1
                continue
            
            # Add track to playlist
            playlist_track_data = {
                "playlist_id": db_playlist['playlist_id'],
                "track_id": db_track['track_id'],
                "date_added": added_at,
                "added_by_user_id": listener_id
            }
            
            # Check if already added
            existing_pt = supabase.from_("PlaylistTrack").select("*").eq("playlist_id", db_playlist['playlist_id']).eq("track_id", db_track['track_id']).eq("date_added", added_at).limit(1).execute()
            
            if not existing_pt.data:
                supabase.from_("PlaylistTrack").insert(playlist_track_data).execute()
                added_count += 1
            else:
                skipped_count += 1
        
        print(f"  > Added {added_count} tracks, ingested {ingested_count} new tracks, skipped {skipped_count} tracks")
        
    except Exception as e:
        print(f"  > Error fetching tracks: {e}")

def ingest_playlists_from_spotify_api(username="cedricster", user_token=None, limit=50):
    """
    Main function to ingest playlists from Spotify API.
    
    Args:
        username: Username for the user account
        user_token: Spotify user access token (required for OAuth)
        limit: Maximum number of playlists to ingest
    """
    if not user_token:
        print("ERROR: User access token is required.")
        print("\nTo get a user token:")
        print("1. Go to: https://developer.spotify.com/console/")
        print("2. Find 'Get Current User's Playlists' endpoint")
        print("3. Click 'Get Token' button")
        print("4. Add scopes: playlist-read-private, playlist-read-collaborative")
        print("5. Copy the token and set SPOTIFY_USER_TOKEN in .env")
        return
    
    try:
        # Create/get user and listener
        user = get_or_create_user(username=username)
        listener = get_or_create_listener(user['user_id'])
        
        # Fetch playlists
        print(f"\nFetching playlists from Spotify...")
        playlists = get_user_playlists(user_token, limit=limit)
        print(f"Found {len(playlists)} playlists")
        
        # Ingest each playlist
        for playlist in playlists:
            ingest_playlist_from_spotify(playlist, listener['listener_id'], user_token)
            time.sleep(0.5)  # Rate limiting between playlists
        
        print(f"\n✓ Successfully ingested {len(playlists)} playlists!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

def ingest_listening_history(username="cedricster", user_token=None, limit=50, max_tracks_to_ingest=10):
    """
    Ingest user's listening history from Spotify into PlayHistory table.
    
    Args:
        username: Username for the user account
        user_token: Spotify user access token (required)
        limit: Maximum number of recent tracks to fetch (default: 50)
        max_tracks_to_ingest: Maximum new tracks to ingest if not in database (default: 10)
    """
    if not user_token:
        print("ERROR: User access token is required.")
        print("Make sure your token has 'user-read-recently-played' scope")
        return
    
    try:
        # Get or create user and listener
        user = get_or_create_user(username=username)
        listener = get_or_create_listener(user['user_id'])
        
        # Get client credentials token for track ingestion
        try:
            client_token = get_spotify_token()
        except Exception as e:
            print(f"Warning: Could not get client token for track ingestion: {e}")
            client_token = None
        
        print(f"\nFetching recently played tracks (limit: {limit})...")
        recently_played = get_recently_played_tracks(user_token, limit=limit)
        
        if not recently_played:
            print("No recently played tracks found or error occurred.")
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
            
            # Get played_at timestamp (Unix timestamp in milliseconds)
            played_at_ms = item.get('played_at')
            if not played_at_ms:
                skipped_count += 1
                continue
            
            # Convert to ISO format timestamp
            try:
                # Spotify returns ISO format string like "2024-01-15T10:30:00.000Z"
                played_at_dt = datetime.fromisoformat(played_at_ms.replace('Z', '+00:00'))
                played_at_iso = played_at_dt.isoformat()
            except:
                # Fallback: try parsing as Unix timestamp
                try:
                    played_at_dt = datetime.fromtimestamp(int(played_at_ms) / 1000, tz=timezone.utc)
                    played_at_iso = played_at_dt.isoformat()
                except:
                    played_at_iso = datetime.now(timezone.utc).isoformat()
            
            # Find track in database
            isrc = spotify_track.get('external_ids', {}).get('isrc')
            track_title = spotify_track.get('name')
            duration_ms = spotify_track.get('duration_ms')
            
            db_track = find_track_by_isrc_or_title(isrc=isrc, title=track_title, duration_ms=duration_ms)
            
            # If track not found and we haven't exceeded the limit, try to ingest it
            if not db_track and client_token and ingested_count < max_tracks_to_ingest:
                print(f"  [{idx}] Track not in database, attempting to ingest: {track_title}")
                db_track = ingest_track_from_spotify(spotify_track, token=client_token)
                if db_track:
                    ingested_count += 1
                    print(f"    > Successfully ingested track: {track_title}")
                    time.sleep(0.2)
                else:
                    print(f"    > Failed to ingest track: {track_title}")
            
            if not db_track:
                print(f"  [{idx}] Skipping track (not in database): {track_title}")
                skipped_count += 1
                continue
            
            # Add to play history
            play_history_data = {
                "listener_id": listener['listener_id'],
                "track_id": db_track['track_id'],
                "played_at": played_at_iso,
                "is_skip": False  # Spotify doesn't provide skip info, default to False
            }
            
            # Check if already exists (same listener, track, and timestamp)
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

# ---
# 5. OAUTH HELPER
# ---
def generate_oauth_url():
    """
    Generate OAuth URL for user to authorize the app.
    Returns the authorization URL.
    """
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    redirect_uri = "http://localhost:8888/callback"  # Default redirect URI
    
    if not client_id:
        print("Warning: SPOTIFY_CLIENT_ID not found in .env")
        client_id = input("Enter your Spotify Client ID: ").strip()
    
    scopes = "playlist-read-private playlist-read-collaborative"
    auth_url = (
        f"https://accounts.spotify.com/authorize?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scopes.replace(' ', '%20')}"
    )
    
    return auth_url

def exchange_code_for_token(auth_code, redirect_uri="http://localhost:8888/callback"):
    """
    Exchange authorization code for access token.
    This requires a server to receive the callback, or manual code extraction.
    """
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise Exception("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET required in .env")
    
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri
    }
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code != 200:
        raise Exception(f"Failed to exchange code: {response.text}")
    
    return response.json().get('access_token')

# ---
# 6. RUN THE SCRIPT
# ---
if __name__ == "__main__":
    print("Spotify Data Ingestion Script")
    print("=" * 50)
    
    # Get user token from environment or prompt
    user_token = os.environ.get("SPOTIFY_USER_TOKEN")
    
    if not user_token:
        print("\nTo use this script, you need a Spotify user access token.")
        print("Get one using get_token.py or set SPOTIFY_USER_TOKEN in .env")
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
        ingest_playlists_from_spotify_api(username=username, user_token=user_token, limit=limit)
    
    if choice in ["2", "3"]:
        history_limit_input = input("Enter max number of recent tracks to fetch (default: 50): ").strip()
        history_limit = int(history_limit_input) if history_limit_input else 50
        ingest_listening_history(username=username, user_token=user_token, limit=history_limit)

