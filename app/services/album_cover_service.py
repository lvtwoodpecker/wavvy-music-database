"""
Service for fetching and storing album covers from Spotify to Supabase Storage.
"""
import time
import requests
from typing import Optional

from app.db.supabase_client import supabase
from app.services.spotify_service import get_spotify_token, fetch_spotify_api

def _ensure_supabase():
    """Ensure Supabase client is available before use."""
    if supabase is None:
        raise RuntimeError("Supabase client not initialized")


def download_image(url: str) -> Optional[bytes]:
    """Download an image from a URL."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        print(f"      > Error downloading image: {e}")
        return None


def upload_to_supabase_storage(file_content: bytes, file_path: str, bucket: str = "album-covers") -> Optional[str]:
    """
    Upload a file to Supabase Storage.
    
    Args:
        file_content: Binary content of the file
        file_path: Path within the bucket (e.g., "album_123.jpg")
        bucket: Storage bucket name (default: "album-covers")
    
    Returns:
        Public URL of the uploaded file, or None if failed
    """
    try:
        _ensure_supabase()
        # Upload file to Supabase Storage
        response = supabase.storage.from_(bucket).upload(
            file_path,
            file_content,
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )
        
        # Construct public URL manually
        # Format: https://{project_ref}.supabase.co/storage/v1/object/public/{bucket}/{path}
        from app.config import Settings
        supabase_url = Settings().SUPABASE_URL.rstrip('/')
        public_url = f"{supabase_url}/storage/v1/object/public/{bucket}/{file_path}"
        
        return public_url
    except Exception as e:
        # Try to construct URL anyway (in case upload succeeded but response failed)
        try:
            from app.config import Settings
            supabase_url = Settings().SUPABASE_URL.rstrip('/')
            return f"{supabase_url}/storage/v1/object/public/{bucket}/{file_path}"
        except:
            return None


def get_album_cover_from_spotify_data(spotify_album_data: dict) -> Optional[str]:
    """
    Extract album cover URL from Spotify album data.
    
    Args:
        spotify_album_data: Full album object from Spotify API
    
    Returns:
        URL of the largest available cover image, or None if not found
    """
    try:
        images = spotify_album_data.get('images', [])
        if not images:
            return None
        
        # Get the largest image (first in the array is usually the largest)
        return images[0].get('url')
    except Exception:
        return None


def search_album_cover_on_spotify(album_title: str, artist_name: str, token: str) -> Optional[str]:
    """
    Search Spotify for an album and get its cover image URL.
    
    Args:
        album_title: Title of the album
        artist_name: Name of the artist
        token: Spotify access token
    
    Returns:
        URL of the largest available cover image, or None if not found
    """
    try:
        # Search for the album
        query = f"album:{album_title} artist:{artist_name}"
        search_response = fetch_spotify_api(
            f"search?q={query}&type=album&limit=1",
            token
        )
        
        albums = search_response.get('albums', {}).get('items', [])
        if not albums:
            return None
        
        album = albums[0]
        return get_album_cover_from_spotify_data(album)
        
    except Exception:
        return None


def fetch_and_store_album_cover(album_id: int, spotify_album_data: Optional[dict] = None, 
                                token: Optional[str] = None, skip_if_exists: bool = True) -> bool:
    """
    Fetch album cover from Spotify and store it in Supabase Storage.
    
    Args:
        album_id: Database album_id
        spotify_album_data: Optional full album data from Spotify API (if available, avoids extra API call)
        token: Optional Spotify access token (will be fetched if not provided)
        skip_if_exists: If True, skip if album already has a cover_image_url
    
    Returns:
        True if cover was successfully stored, False otherwise
    """
    try:
        _ensure_supabase()
        # Check if album already has a cover
        if skip_if_exists:
            album_check = supabase.from_("Album").select("cover_image_url").eq("album_id", album_id).limit(1).execute()
            if album_check.data and album_check.data[0].get('cover_image_url'):
                return True  # Already has cover
        
        # Get Spotify token if not provided
        if not token:
            token = get_spotify_token()
        
        # Get cover URL
        cover_url = None
        
        if spotify_album_data:
            # Use provided album data
            cover_url = get_album_cover_from_spotify_data(spotify_album_data)
        else:
            # Need to search for the album
            album_response = supabase.from_("Album").select("title").eq("album_id", album_id).limit(1).execute()
            if not album_response.data:
                return False
            
            album_title = album_response.data[0]['title']
            
            # Get artist name for better search
            artist_response = supabase.from_("AlbumArtist").select("artist_id").eq("album_id", album_id).limit(1).execute()
            artist_name = None
            if artist_response.data:
                artist_id = artist_response.data[0]['artist_id']
                artist_data = supabase.from_("Artist").select("name").eq("artist_id", artist_id).limit(1).execute()
                if artist_data.data:
                    artist_name = artist_data.data[0]['name']
            
            if not artist_name:
                return False
            
            cover_url = search_album_cover_on_spotify(album_title, artist_name, token)
        
        if not cover_url:
            return False
        
        # Download the image
        image_content = download_image(cover_url)
        if not image_content:
            return False
        
        # Upload to Supabase Storage
        file_path = f"album_{album_id}.jpg"
        storage_url = upload_to_supabase_storage(image_content, file_path)
        
        if not storage_url:
            return False
        
        # Update album with cover image URL
        update_response = supabase.from_("Album").update({
            "cover_image_url": storage_url
        }).eq("album_id", album_id).execute()
        
        return bool(update_response.data)
        
    except Exception as e:
        print(f"      > Error fetching/storing album cover: {e}")
        return False

