import os
import base64
import requests
import json
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

def fetch_spotify_api(endpoint, token):
    url = f"https://api.spotify.com/v1/{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Spotify API Error: {response.text}")
        
    return response.json()

# ---
# 2b. SPOTIFY WORKAROUND FUNCTION (NEW)
# ---
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
# 3. MAIN INGESTION FUNCTION
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
        # STEP 2: Ingest Albums
        # ---
        print(f"Fetching albums for {db_artist['name']}...")
        albums_data = fetch_spotify_api(f"artists/{spotify_artist['id']}/albums?include_groups=album,single&limit=5", token)

        for spotify_album in albums_data['items']:
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
            album_to_insert = {
                "title": full_album_data['name'],
                "release_date": full_album_data['release_date'],
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

            # ---
            # STEP 2c: Link Album and Artist
            # ---
            supabase.from_("AlbumArtist").upsert({
                "album_id": db_album['album_id'],
                "artist_id": db_artist['artist_id']
            }, on_conflict='album_id, artist_id').execute()

            # ---
            # STEP 2d: Ingest Tracks
            # ---
            for spotify_track in full_album_data['tracks']['items']:
                isrc = spotify_track.get('external_ids', {}).get('isrc')
                
                preview_url = spotify_track.get('preview_url') # Gets the 30-sec URL (or None)
                
                if not preview_url:
                    print(f"    > No direct preview. Trying workaround for '{spotify_track['name']}'...")
                    preview_url = get_preview_url_workaround(spotify_track['id'])

                track_to_insert = {
                    "title": spotify_track['name'],
                    "duration_ms": spotify_track['duration_ms'],
                    "isrc": isrc,
                    "audio_file_url": preview_url # Add the URL to the new column
                }
                
                if isrc:
                    track_response = supabase.from_("Track").upsert(track_to_insert, on_conflict='isrc').execute()
                else:
                    track_response = supabase.from_("Track").insert(track_to_insert).execute()

                if not track_response.data:
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
