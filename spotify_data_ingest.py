import os
import base64
import requests
import json
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client, Client

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
# 2. SPOTIFY AUTH
# ---
def get_spotify_token():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    
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
        JSON response data or None if error
    """
    url = f"https://api.spotify.com/v1/{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        
        # Handle rate limiting (429) - retry after delay
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 1))
            if retry_count < max_retries:
                print(f"      > Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return fetch_spotify_api(endpoint, token, retry_count + 1, max_retries)
            else:
                raise Exception(f"Spotify API Rate Limit: Max retries exceeded")
        
        # Handle forbidden (403) - likely permission issue or rate limit
        if response.status_code == 403:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Forbidden')
            raise Exception(f"Spotify API Forbidden (403): {error_msg}. This may be due to rate limiting or insufficient permissions.")
        
        # Handle other errors
        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {}).get('message', response.text)
            raise Exception(f"Spotify API Error ({response.status_code}): {error_msg}")
        
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error fetching from Spotify API: {str(e)}")

# SPOTIFY WORKAROUND FUNCTION
def get_preview_url_workaround(track_id):
    """
    Scrapes the Spotify web player to find the preview URL
    when the main API returns null.
    """
    try:
        page_url = f"https://open.spotify.com/track/{track_id}"
        # Set a User-Agent to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(page_url, headers=headers)
        if response.status_code != 200:
            return None
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the <meta property="og:audio" content="..."> tag
        audio_tag = soup.find('meta', property='og:audio')
        
        # If the tag was found and it has a 'content' attribute...
        if audio_tag and audio_tag.get('content'):
            return audio_tag['content'] # Return the URL!
            
        # If we get here, the tag wasn't found
        return None
        
    except Exception as e:
        print(f"    > Workaround Exception: {e}")
        return None
# ---
# 3. TRACK INGESTION HELPER
# ---
def ingest_track_from_spotify(spotify_track, token=None):
    """
    Ingest a single track from Spotify API data into the database.
    This is a reusable function that can be called from other scripts.
    
    Args:
        spotify_track: Track object from Spotify API
        token: Spotify access token (if None, will get client credentials token)
    
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
            
            if update_data:
                update_response = supabase.from_("Track").update(update_data).eq("track_id", db_track['track_id']).execute()
                if update_response.data:
                    db_track = update_response.data[0]
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
            artists = spotify_track.get('artists', [])
            for artist_data in artists:
                artist_name = artist_data.get('name')
                if artist_name:
                    # Find or create artist
                    artist_response = supabase.from_("Artist").select("*").eq("name", artist_name).limit(1).execute()
                    if artist_response.data:
                        db_artist = artist_response.data[0]
                        supabase.from_("TrackArtist").upsert({
                            "track_id": db_track['track_id'],
                            "artist_id": db_artist['artist_id'],
                            "role": 'Main' if artists.index(artist_data) == 0 else 'Featured'
                        }, on_conflict='track_id, artist_id, role').execute()
            
            return db_track
    except Exception as e:
        print(f"      > Error ingesting track: {e}")
        return None

# ---
# 4. MAIN INGESTION FUNCTION
# ---
def ingest_data(artist_name):
    try:
        print("Starting ingestion process...")
        token = get_spotify_token()
        print("Spotify token acquired.")

        # ---
        # STEP 1: Ingest Artist
        # ---
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

        # ---
        # STEP 1a: Ingest Genres for Artist
        # ---
        artist_genres = spotify_artist.get('genres', [])
        for genre_name in artist_genres:
            if genre_name:  # Skip empty genres
                genre_response = supabase.from_("Genre").upsert({"name": genre_name}, on_conflict='name').execute()
                if genre_response.data:
                    db_genre = genre_response.data[0]
                    # Link genre to artist
                    supabase.from_("ArtistGenre").upsert({
                        "artist_id": db_artist['artist_id'],
                        "genre_id": db_genre['genre_id']
                    }, on_conflict='artist_id, genre_id').execute()
                    print(f"  > Linked Genre: {db_genre['name']} to Artist")

        # ---
        # STEP 2: Ingest Albums
        # ---
        print(f"Fetching albums for {db_artist['name']}...")
        albums_data = fetch_spotify_api(f"artists/{spotify_artist['id']}/albums?include_groups=album,single&limit=3", token)

        for spotify_album in albums_data['items']:
            # Add small delay to respect rate limits
            time.sleep(1)  # 500ms delay between requests
            full_album_data = fetch_spotify_api(f"albums/{spotify_album['id']}", token)
            label_name = full_album_data.get('label', 'Unknown Label')

            # ---
            # STEP 2a: Ingest Label
            # ---
            label_response = supabase.from_("Label").upsert({"name": label_name}, on_conflict='name').execute()
            db_label = label_response.data[0]
            print(f"  > Ingested Label: {db_label['name']}")

            # ---
            # STEP 2b: Ingest Album
            # ---
            release_date_str = full_album_data['release_date']
            precision = full_album_data['release_date_precision']
            
            formatted_release_date = None
            if precision == 'year':
                # e.g., "1973" -> "1973-01-01"
                formatted_release_date = f"{release_date_str}-01-01"
            elif precision == 'month':
                # e.g., "1973-05" -> "1973-05-01"
                formatted_release_date = f"{release_date_str}-01"
            elif precision == 'day':
                # e.g., "1973-05-15" -> "1973-05-15"
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
                isrc = spotify_track.get('external_ids', {}).get('isrc')
                
                preview_url = spotify_track.get('preview_url') # Gets the 30-sec URL (or None)
                
                if not preview_url:
                    preview_url = get_preview_url_workaround(spotify_track['id'])

                # Get current timestamp for date_added
                current_timestamp = datetime.now(timezone.utc).isoformat()
                
                track_to_insert = {
                    "title": spotify_track['name'],
                    "duration_ms": spotify_track['duration_ms'],
                    "isrc": isrc,
                    "audio_file_url": preview_url,
                    "date_added": current_timestamp
                }
                
                # Check for existing track by title+duration_ms (prevents duplicates)
                existing_track = supabase.from_("Track").select("*").eq("title", track_to_insert['title']).eq("duration_ms", track_to_insert['duration_ms']).limit(1).execute()
                
                if existing_track.data:
                    # Track with same title and duration already exists - update date_added and other fields
                    db_track = existing_track.data[0]
                    # Always update date_added, and update ISRC and audio_file_url if they're not set
                    update_data = {
                        "date_added": current_timestamp  # Always update date_added for duplicates
                    }
                    if isrc and not db_track.get('isrc'):
                        update_data['isrc'] = isrc
                    if preview_url and not db_track.get('audio_file_url'):
                        update_data['audio_file_url'] = preview_url
                    
                    update_response = supabase.from_("Track").update(update_data).eq("track_id", db_track['track_id']).execute()
                    if update_response.data:
                        db_track = update_response.data[0]
                    
                    print(f"    > Updated existing Track: {db_track['title']} (Audio: {'Yes' if db_track.get('audio_file_url') else 'No'})")
                else:
                    # No duplicate found - insert new track
                    # If ISRC exists, use it for upsert (in case ISRC is duplicate)
                    if isrc:
                        track_response = supabase.from_("Track").upsert(track_to_insert, on_conflict='isrc').execute()
                    else:
                        track_response = supabase.from_("Track").insert(track_to_insert).execute()
                    
                    if not track_response.data:
                        # Fallback: try to select again (race condition handling)
                        track_response = supabase.from_("Track").select("*").eq("title", track_to_insert['title']).eq("duration_ms", track_to_insert['duration_ms']).limit(1).execute()
                        if not track_response.data:
                            print(f"    > Skipping Track (failed insert/select): {spotify_track['name']}")
                            continue
                    
                    db_track = track_response.data[0]
                    print(f"    > Ingested Track: {db_track['title']} (Audio: {'Yes' if preview_url else 'No'})")

                # Link Track to Album
                supabase.from_("AlbumTrack").upsert({
                    "album_id": db_album['album_id'],
                    "track_id": db_track['track_id'],
                    "disc_no": spotify_track['disc_number'],
                    "track_no": spotify_track['track_number']
                }, on_conflict='album_id, track_id').execute()

                # Link Track to Artist
                supabase.from_("TrackArtist").upsert({
                    "track_id": db_track['track_id'],
                    "artist_id": db_artist['artist_id'],
                    "role": 'Main'
                }, on_conflict='track_id, artist_id, role').execute()

                # ---
                # STEP 3a: Link Genres to Track (using artist genres)
                # ---
                for genre_name in artist_genres:
                    if genre_name:
                        genre_response = supabase.from_("Genre").select("*").eq("name", genre_name).limit(1).execute()
                        if genre_response.data:
                            db_genre = genre_response.data[0]
                            supabase.from_("TrackGenre").upsert({
                                "track_id": db_track['track_id'],
                                "genre_id": db_genre['genre_id']
                            }, on_conflict='track_id, genre_id').execute()

                # ---
                # STEP 3b: Ingest Audio Features
                # ---
                # Add small delay to respect rate limits (especially for audio-features endpoint)
                time.sleep(0.1)  # 100ms delay between audio-features requests
                
                try:
                    audio_features_data = fetch_spotify_api(f"audio-features/{spotify_track['id']}", token)
                    
                    # Check if all required fields are present and valid
                    if audio_features_data and 'tempo' in audio_features_data and 'loudness' in audio_features_data:
                        audio_features_to_insert = {
                            "track_id": db_track['track_id'],
                            "tempo": audio_features_data.get('tempo', 0),
                            "loudness": audio_features_data.get('loudness', 0),
                            "danceability": audio_features_data.get('danceability', 0),
                            "energy": audio_features_data.get('energy'),
                            "valence": audio_features_data.get('valence'),
                            "acousticness": audio_features_data.get('acousticness')
                        }
                        
                        # Validate tempo and loudness constraints
                        if audio_features_to_insert['tempo'] > 0 and -60 <= audio_features_to_insert['loudness'] <= 10:
                            audio_features_response = supabase.from_("AudioFeatures").upsert(
                                audio_features_to_insert, 
                                on_conflict='track_id'
                            ).execute()
                            if audio_features_response.data:
                                print(f"      > Ingested Audio Features for track")
                        else:
                            print(f"      > Skipped Audio Features (invalid tempo/loudness)")
                    else:
                        print(f"      > No audio features available for track")
                except Exception as e:
                    # Audio features are optional - log error but continue processing
                    error_msg = str(e)
                    if "403" in error_msg or "Forbidden" in error_msg:
                        print(f"      > Skipped Audio Features (403 Forbidden - may be rate limited or require different permissions)")
                    elif "429" in error_msg or "Rate Limit" in error_msg:
                        print(f"      > Skipped Audio Features (Rate limited - will retry on next run)")
                    else:
                        print(f"      > Skipped Audio Features: {error_msg}")

                # ---
                # STEP 3c: Ingest Work Credits (if ISRC is available, we can create a work entry)
                # ---
                # Note: Spotify doesn't provide ISWC or composer information directly
                # We'll create a work entry based on the track title if ISRC is available
                # This is a placeholder - real ISWC data would need to come from another source
                if isrc:
                    try:
                        # Check if work with same title already exists
                        work_response = supabase.from_("Work").select("*").eq("title", spotify_track['name']).limit(1).execute()
                        
                        if work_response.data:
                            db_work = work_response.data[0]
                        else:
                            # Create a work entry with the track title (ISWC would need external data)
                            work_to_insert = {
                                "title": spotify_track['name']
                            }
                            work_response = supabase.from_("Work").insert(work_to_insert).execute()
                            if work_response.data:
                                db_work = work_response.data[0]
                            else:
                                print(f"      > Failed to create work entry")
                                continue
                        
                        # Link work to track
                        supabase.from_("TrackWork").upsert({
                            "track_id": db_track['track_id'],
                            "work_id": db_work['work_id']
                        }, on_conflict='track_id, work_id').execute()
                        
                        # Link composer to work (using main artist as composer)
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

# ---
# 4. RUN THE SCRIPT
# ---
if __name__ == "__main__":
    # clear old data by running this in Supabase SQL:
    # TRUNCATE "Artist", "Label", "Album", "Track" CASCADE;

    band = input("What band? ")
    ingest_data(band)
