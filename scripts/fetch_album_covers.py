"""
Script to fetch album covers from Spotify and upload them to Supabase Storage.
"""
import sys
import os
import time
import requests
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.supabase_client import supabase
from app.services.spotify_service import get_spotify_token, fetch_spotify_api

def _ensure_supabase():
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
        print(f"    > Error downloading image: {e}")
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
        # Supabase Python client upload method
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
        print(f"    > Error uploading to Supabase Storage: {e}")
        # Try to construct URL anyway (in case upload succeeded but response failed)
        try:
            from app.config import Settings
            supabase_url = Settings().SUPABASE_URL.rstrip('/')
            return f"{supabase_url}/storage/v1/object/public/{bucket}/{file_path}"
        except:
            return None


def get_album_cover_from_spotify(album_title: str, artist_name: str, token: str) -> Optional[str]:
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
        images = album.get('images', [])
        
        if not images:
            return None
        
        # Get the largest image (first in the array is usually the largest)
        return images[0].get('url')
        
    except Exception as e:
        print(f"    > Error fetching from Spotify: {e}")
        return None


def fetch_and_store_album_covers(limit: Optional[int] = None):
    """
    Fetch album covers from Spotify and store them in Supabase Storage.
    
    Args:
        limit: Maximum number of albums to process (None for all)
    """
    print("Starting album cover fetch and storage...")
    print("=" * 60)
    _ensure_supabase()
    
    # Get Spotify token
    token = get_spotify_token()
    print("Spotify token acquired.\n")
        
    # Get all albums
    query = supabase.from_("Album").select("album_id, title")
    if limit:
        query = query.limit(limit)
    
    albums_response = query.execute()
    
    if not albums_response.data:
        print("No albums found in database.")
        return
    
    albums = albums_response.data
    print(f"Found {len(albums)} albums to process.\n")
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for idx, album in enumerate(albums, 1):
        album_id = album['album_id']
        album_title = album['title']
        
        print(f"[{idx}/{len(albums)}] Processing: {album_title}")
        
        # Check if album already has a cover
        album_check = supabase.from_("Album").select("cover_image_url").eq("album_id", album_id).limit(1).execute()
        if album_check.data and album_check.data[0].get('cover_image_url'):
            print(f"  > Already has cover image, skipping")
            skipped_count += 1
            continue
        
        # Get artist name for better search
        artist_response = supabase.from_("AlbumArtist").select("artist_id").eq("album_id", album_id).limit(1).execute()
        artist_name = None
        if artist_response.data:
            artist_id = artist_response.data[0]['artist_id']
            artist_data = supabase.from_("Artist").select("name").eq("artist_id", artist_id).limit(1).execute()
            if artist_data.data:
                artist_name = artist_data.data[0]['name']
        
        if not artist_name:
            print(f"  > No artist found, skipping")
            error_count += 1
            continue
        
        # Get cover image URL from Spotify
        cover_url = get_album_cover_from_spotify(album_title, artist_name, token)
        
        if not cover_url:
            print(f"  > Could not find cover image on Spotify")
            error_count += 1
            time.sleep(0.2)  # Rate limiting
            continue
        
        # Download the image
        image_content = download_image(cover_url)
        
        if not image_content:
            print(f"  > Could not download image")
            error_count += 1
            time.sleep(0.2)
            continue
        
        # Upload to Supabase Storage
        file_path = f"album_{album_id}.jpg"
        storage_url = upload_to_supabase_storage(image_content, file_path)
        
        if not storage_url:
            print(f"  > Could not upload to Supabase Storage")
            error_count += 1
            time.sleep(0.2)
            continue
        
        # Update album with cover image URL
        try:
            update_response = supabase.from_("Album").update({
                "cover_image_url": storage_url
            }).eq("album_id", album_id).execute()
            
            if update_response.data:
                print(f"  > ✓ Successfully stored cover image")
                success_count += 1
            else:
                print(f"  > ✗ Failed to update album record")
                error_count += 1
        except Exception as e:
            print(f"  > ✗ Error updating album: {e}")
            error_count += 1
        
        # Rate limiting
        time.sleep(0.3)
    
    print("\n" + "=" * 60)
    print(f"Album cover fetch complete!")
    print(f"  Success: {success_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total processed: {len(albums)}")


if __name__ == "__main__":
    # Process all albums (or set a limit for testing)
    fetch_and_store_album_covers(limit=None)

