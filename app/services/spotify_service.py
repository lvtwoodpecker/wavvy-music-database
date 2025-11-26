"""
Spotify API service with reusable functions for data ingestion.
"""
import os
import base64
import time
import requests
from datetime import datetime, timezone
from typing import Dict, Optional
from bs4 import BeautifulSoup
from app.config import settings
from app.db.supabase_client import supabase

if not supabase:
    raise Exception("Supabase client not initialized")


def get_spotify_token(client_id=None, client_secret=None):
    """
    Get Spotify client credentials token.
    
    Args:
        client_id: Spotify client ID (defaults to SPOTIFY_CLIENT_ID_C from config)
        client_secret: Spotify client secret (defaults to SPOTIFY_CLIENT_SECRET_C from config)
    
    Returns:
        Access token string
    """
    client_id = client_id or os.environ.get("SPOTIFY_CLIENT_ID") or settings.SPOTIFY_CLIENT_ID_C
    client_secret = client_secret or os.environ.get("SPOTIFY_CLIENT_SECRET") or settings.SPOTIFY_CLIENT_SECRET_C
    
    if not client_id or not client_secret:
        raise Exception("Spotify Client ID and Secret are required")
    
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code != 200:
        raise Exception(f"Failed to get Spotify token: {response.text}")
    
    return response.json().get('access_token')


def fetch_spotify_api(endpoint, token, retry_count=0, max_retries=2):
    """
    Fetch data from Spotify API with error handling and rate limiting.
    
    Args:
        endpoint: API endpoint (without base URL)
        token: Spotify access token
        retry_count: Current retry attempt
        max_retries: Maximum number of retries
    
    Returns:
        JSON response data
    """
    url = f"https://api.spotify.com/v1/{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 1))
            if retry_count < max_retries:
                print(f"      > Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return fetch_spotify_api(endpoint, token, retry_count + 1, max_retries)
            else:
                raise Exception(f"Spotify API Rate Limit: Max retries exceeded")
        
        if response.status_code == 401:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unauthorized')
            raise Exception(f"Spotify API Unauthorized (401): {error_msg}. The access token expired or is invalid.")
        
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


def get_preview_url_workaround(track_id):
    """
    Scrapes the Spotify web player to find the preview URL when the main API returns null.
    """
    try:
        page_url = f"https://open.spotify.com/track/{track_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(page_url, headers=headers)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        audio_tag = soup.find('meta', property='og:audio')
        
        if audio_tag and audio_tag.get('content'):
            return audio_tag['content']
        
        return None
    except Exception as e:
        print(f"    > Workaround Exception: {e}")
        return None


def _ingest_album_and_label_from_track(spotify_track: Dict, db_track: Dict, token: str):
    """Helper function to ingest album and label from a track's album data."""
    try:
        spotify_album = spotify_track.get('album')
        if not spotify_album:
            return
        
        # Get full album data if we only have basic info
        album_id = spotify_album.get('id')
        if not album_id:
            return
        
        # Fetch full album data to get label
        full_album_data = fetch_spotify_api(f"albums/{album_id}", token)
        label_name = full_album_data.get('label', 'Unknown Label')
        
        # Ingest Label
        label_response = supabase.from_("Label").upsert({"name": label_name}, on_conflict='name').execute()
        db_label = label_response.data[0] if label_response.data else None
        
        if not db_label:
            return
        
        # Ingest Album
        release_date_str = full_album_data.get('release_date', '')
        precision = full_album_data.get('release_date_precision', 'day')
        
        formatted_release_date = None
        if release_date_str:
            if precision == 'year':
                formatted_release_date = f"{release_date_str}-01-01"
            elif precision == 'month':
                formatted_release_date = f"{release_date_str}-01"
            elif precision == 'day':
                formatted_release_date = release_date_str
        
        album_to_insert = {
            "title": full_album_data.get('name', ''),
            "release_date": formatted_release_date,
            "type": full_album_data.get('album_type', 'album'),
            "label_id": db_label['label_id']
        }
        
        album_response = supabase.from_("Album").select("*").eq("title", album_to_insert['title']).limit(1).execute()
        
        if album_response.data:
            db_album = album_response.data[0]
        else:
            album_insert_response = supabase.from_("Album").insert(album_to_insert).execute()
            if album_insert_response.data:
                db_album = album_insert_response.data[0]
            else:
                return
        
        # Link Album to Artists
        from app.services.track_info_and_relationship_service import link_album_artists
        link_album_artists(
            album_id=db_album['album_id'],
            spotify_album_data=full_album_data,
            token=token
        )
        
        # Link Track to Album
        supabase.from_("AlbumTrack").upsert({
            "album_id": db_album['album_id'],
            "track_id": db_track['track_id'],
            "disc_no": spotify_track.get('disc_number', 1),
            "track_no": spotify_track.get('track_number', 1)
        }, on_conflict='album_id, track_id').execute()
        
    except Exception:
        # Silently fail - album/label ingestion is optional
        pass


def ingest_track_from_spotify(spotify_track, token=None, ingest_album=True):
    """
    Ingest a single track from Spotify API data into the database.
    Handles track creation/update, artist linking, album/label ingestion, and metadata.
    
    Args:
        spotify_track: Track object from Spotify API
        token: Spotify access token (if None, will get client credentials token)
        ingest_album: Whether to ingest album and label information (default: True)
    
    Returns:
        Database track record or None if failed
    """
    if token is None:
        token = get_spotify_token()
    
    try:
        isrc = spotify_track.get('external_ids', {}).get('isrc')
        preview_url = spotify_track.get('preview_url')
        
        if not preview_url:
            preview_url = get_preview_url_workaround(spotify_track['id'])
        
        current_timestamp = datetime.now(timezone.utc).isoformat()
        
        track_to_insert = {
            "title": spotify_track['name'],
            "duration_ms": spotify_track['duration_ms'],
            "isrc": isrc,
            "spotify_id": spotify_track['id'],  # Store Spotify track ID
            "audio_file_url": preview_url,
            "date_added": current_timestamp
        }
        
        # Check for existing track
        existing_track = supabase.from_("Track").select("*").eq("title", track_to_insert['title']).eq("duration_ms", track_to_insert['duration_ms']).limit(1).execute()
        
        if existing_track.data:
            db_track = existing_track.data[0]
            update_data = {"date_added": current_timestamp}
            if isrc and not db_track.get('isrc'):
                update_data['isrc'] = isrc
            if preview_url and not db_track.get('audio_file_url'):
                update_data['audio_file_url'] = preview_url
            if spotify_track['id'] and not db_track.get('spotify_id'):
                update_data['spotify_id'] = spotify_track['id']
            
            if update_data:
                update_response = supabase.from_("Track").update(update_data).eq("track_id", db_track['track_id']).execute()
                if update_response.data:
                    db_track = update_response.data[0]
            
            # Ensure all track artists are linked (even for existing tracks)
            from app.services.track_info_and_relationship_service import link_track_artists
            link_track_artists(
                track_id=db_track['track_id'],
                spotify_track_data=spotify_track,
                token=token
            )
            
            # Ingest album and label if requested
            if ingest_album and spotify_track.get('album'):
                _ingest_album_and_label_from_track(spotify_track, db_track, token)
            
            return db_track
        else:
            # Insert new track
            if isrc:
                track_response = supabase.from_("Track").upsert(track_to_insert, on_conflict='isrc').execute()
            else:
                track_response = supabase.from_("Track").insert(track_to_insert).execute()
            
            if not track_response.data:
                track_response = supabase.from_("Track").select("*").eq("title", track_to_insert['title']).eq("duration_ms", track_to_insert['duration_ms']).limit(1).execute()
                if not track_response.data:
                    return None
            
            db_track = track_response.data[0]
            
            # Link track to artist(s) if available
            from app.services.track_info_and_relationship_service import link_track_artists
            link_track_artists(
                track_id=db_track['track_id'],
                spotify_track_data=spotify_track,
                token=token
            )
            
            # Ingest album and label if requested
            if ingest_album and spotify_track.get('album'):
                _ingest_album_and_label_from_track(spotify_track, db_track, token)
            
            return db_track
    except Exception as e:
        print(f"      > Error ingesting track: {e}")
        return None

