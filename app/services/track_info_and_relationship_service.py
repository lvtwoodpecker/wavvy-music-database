"""
Service for managing track relationships and information: TrackArtist, TrackGenre, AlbumTrack, 
audio features, and other related metadata. Centralizes all track-related data management.
"""
from typing import Optional, Dict, List
from app.db.supabase_client import supabase
from app.services.spotify_service import fetch_spotify_api, get_spotify_token
from app.services.reccobeats_service import ReccoBeatsService



def _fetch_and_save_audio_features(track_id: int, track_title: str, 
                                   artist_name: Optional[str] = None,
                                   duration_ms: Optional[int] = None,
                                   spotify_track_id: Optional[str] = None) -> bool:
    """
    Internal function to fetch audio features for a track and save them to the database.
    Also updates the track's spotify_id if not already set.
    
    Args:
        track_id: Database track_id
        track_title: Track title
        artist_name: Optional artist name for better matching
        duration_ms: Optional duration in milliseconds for better matching
        spotify_track_id: Optional Spotify track ID if already known
    
    Returns:
        True if audio features were successfully saved, False otherwise
    """
    try:
        # Get Spotify track ID if not provided
        if not spotify_track_id:
            spotify_track_id = ReccoBeatsService.get_spotify_track_id(
                track_title, artist_name, duration_ms
            )
            if not spotify_track_id:
                return False
        
        # Update track with spotify_id if not already set
        track_response = supabase.from_("Track").select("spotify_id").eq("track_id", track_id).limit(1).execute()
        if track_response.data and not track_response.data[0].get('spotify_id'):
            supabase.from_("Track").update({"spotify_id": spotify_track_id}).eq("track_id", track_id).execute()
        
        # Get audio features from ReccoBeats
        features = ReccoBeatsService.get_audio_features(spotify_track_id)
        
        if not features:
            return False
        
        # Validate and prepare for insertion
        audio_features_to_insert = {
            "track_id": track_id,
            "tempo": features.get('tempo', 0),
            "loudness": features.get('loudness', 0),
            "danceability": features.get('danceability', 0),
            "energy": features.get('energy'),
            "valence": features.get('valence'),
            "acousticness": features.get('acousticness')
        }
        
        # Validate tempo and loudness constraints
        if audio_features_to_insert['tempo'] > 0 and -60 <= audio_features_to_insert['loudness'] <= 10:
            audio_features_response = supabase.from_("AudioFeatures").upsert(
                audio_features_to_insert, 
                on_conflict='track_id'
            ).execute()
            
            return bool(audio_features_response.data)
        
        return False
        
    except Exception:
        return False


def link_track_artists(track_id: int, spotify_track_data: Dict, token: Optional[str] = None) -> int:
    """
    Link all artists from a Spotify track to the database track.
    Creates artists if they don't exist.
    
    Args:
        track_id: Database track_id
        spotify_track_data: Full Spotify track object with artists array
        token: Optional Spotify token (will fetch if not provided)
    
    Returns:
        Number of artists linked
    """
    if not token:
        token = get_spotify_token()
    
    artists = spotify_track_data.get('artists', [])
    if not artists:
        return 0
    
    linked_count = 0
    for idx, artist_data in enumerate(artists):
        artist_name = artist_data.get('name')
        artist_spotify_id = artist_data.get('id')
        
        if not artist_name:
            continue
        
        # Get or create artist
        artist_response = supabase.from_("Artist").select("*").eq("name", artist_name).limit(1).execute()
        
        if not artist_response.data:
            # Create artist if doesn't exist
            artist_to_insert = {
                "name": artist_name,
                "type": 'Solo'  # Default, can be updated later
            }
            artist_response = supabase.from_("Artist").insert(artist_to_insert).execute()
            if not artist_response.data:
                continue
        
        db_artist = artist_response.data[0]
        
        # Link TrackArtist
        role = 'Main' if idx == 0 else 'Featured'
        supabase.from_("TrackArtist").upsert({
            "track_id": track_id,
            "artist_id": db_artist['artist_id'],
            "role": role
        }, on_conflict='track_id, artist_id, role').execute()
        
        linked_count += 1
    
    return linked_count


def link_track_genres(track_id: int, spotify_track_data: Optional[Dict] = None,
                     token: Optional[str] = None) -> int:
    """
    Link all genres from track's artists to the track.
    Fetches artist data if needed to get genres.
    
    Args:
        track_id: Database track_id
        spotify_track_data: Optional full Spotify track object
        token: Optional Spotify token (will fetch if not provided)
    
    Returns:
        Number of genres linked
    """
    if not token:
        token = get_spotify_token()
    
    all_genres = set()
    
    # If we have spotify_track_data, use it to get artist Spotify IDs and fetch genres
    if spotify_track_data:
        artists = spotify_track_data.get('artists', [])
        artist_spotify_ids = [a.get('id') for a in artists if a.get('id')]
        
        # Fetch genres from Spotify API for all artists
        for artist_spotify_id in artist_spotify_ids:
            try:
                artist_data = fetch_spotify_api(f"artists/{artist_spotify_id}", token)
                artist_genres = artist_data.get('genres', [])
                all_genres.update(artist_genres)
            except Exception:
                pass
    else:
        # Get artists from TrackArtist table and try to get genres from ArtistGenre
        track_artists_response = supabase.from_("TrackArtist").select("artist_id").eq("track_id", track_id).execute()
        if track_artists_response.data:
            for ta in track_artists_response.data:
                artist_id = ta['artist_id']
                artist_genres_response = supabase.from_("ArtistGenre").select("genre_id").eq("artist_id", artist_id).execute()
                if artist_genres_response.data:
                    for ag in artist_genres_response.data:
                        genre_response = supabase.from_("Genre").select("name").eq("genre_id", ag['genre_id']).limit(1).execute()
                        if genre_response.data:
                            all_genres.add(genre_response.data[0]['name'])
    
    # Link all genres to track
    genres_linked = 0
    for genre_name in all_genres:
        if not genre_name:
            continue
        
        # Get or create genre
        genre_response = supabase.from_("Genre").upsert({"name": genre_name}, on_conflict='name').execute()
        if genre_response.data:
            db_genre = genre_response.data[0]
            supabase.from_("TrackGenre").upsert({
                "track_id": track_id,
                "genre_id": db_genre['genre_id']
            }, on_conflict='track_id, genre_id').execute()
            genres_linked += 1
    
    return genres_linked


def link_album_artists(album_id: int, spotify_album_data: Dict, token: Optional[str] = None) -> int:
    """
    Link all artists from a Spotify album to the database album.
    
    Args:
        album_id: Database album_id
        spotify_album_data: Full Spotify album object with artists array
        token: Optional Spotify token (will fetch if not provided)
    
    Returns:
        Number of artists linked
    """
    if not token:
        token = get_spotify_token()
    
    artists = spotify_album_data.get('artists', [])
    if not artists:
        return 0
    
    linked_count = 0
    for artist_data in artists:
        artist_name = artist_data.get('name')
        if not artist_name:
            continue
        
        # Get artist from database
        artist_response = supabase.from_("Artist").select("*").eq("name", artist_name).limit(1).execute()
        if artist_response.data:
            db_artist = artist_response.data[0]
            supabase.from_("AlbumArtist").upsert({
                "album_id": album_id,
                "artist_id": db_artist['artist_id']
            }, on_conflict='album_id, artist_id').execute()
            linked_count += 1
    
    return linked_count


def ensure_artist_genres(artist_id: int, spotify_artist_id: Optional[str] = None,
                        token: Optional[str] = None) -> int:
    """
    Ensure an artist has all their genres linked in ArtistGenre table.
    Fetches from Spotify if needed.
    
    Args:
        artist_id: Database artist_id
        spotify_artist_id: Optional Spotify artist ID
        token: Optional Spotify token (will fetch if not provided)
    
    Returns:
        Number of genres linked
    """
    if not token:
        token = get_spotify_token()
    
    artist_response = supabase.from_("Artist").select("name").eq("artist_id", artist_id).limit(1).execute()
    if not artist_response.data:
        return 0
    
    artist_name = artist_response.data[0]['name']
    
    if not spotify_artist_id:
        try:
            search_data = fetch_spotify_api(f"search?q={artist_name}&type=artist&limit=1", token)
            if search_data.get('artists', {}).get('items'):
                spotify_artist_id = search_data['artists']['items'][0]['id']
        except Exception:
            return 0
    
    if not spotify_artist_id:
        return 0
    
    try:
        artist_data = fetch_spotify_api(f"artists/{spotify_artist_id}", token)
        artist_genres = artist_data.get('genres', [])
        
        if not artist_genres:
            try:
                related_artists_response = fetch_spotify_api(f"artists/{spotify_artist_id}/related-artists", token)
                all_genres = set()
                for related_artist in related_artists_response.get('artists', [])[:10]:
                    related_genres = related_artist.get('genres', [])
                    if related_genres:
                        all_genres.update(related_genres)
                if all_genres:
                    artist_genres = list(all_genres)[:5]
            except Exception:
                return 0
        
        if not artist_genres:
            return 0
        
        genres_linked = 0
        for genre_name in artist_genres:
            if not genre_name:
                continue
            
            try:
                genre_response = supabase.from_("Genre").upsert({"name": genre_name}, on_conflict='name').execute()
                if genre_response.data:
                    db_genre = genre_response.data[0]
                    ag_response = supabase.from_("ArtistGenre").upsert({
                        "artist_id": artist_id,
                        "genre_id": db_genre['genre_id']
                    }, on_conflict='artist_id, genre_id').execute()
                    if ag_response.data or not ag_response.error:
                        genres_linked += 1
            except Exception:
                pass
        
        return genres_linked
    except Exception:
        return 0


def add_song_info(track_id: int, spotify_track_data: Optional[Dict] = None, 
                 spotify_track_id: Optional[str] = None, token: Optional[str] = None) -> Dict[str, bool]:
    """
    Add song information: audio features, genres, and other related metadata.
    This is a one-stop method to ensure a track has all its metadata.

    """
    results = {
        'audio_features': False,
        'genres': False,
        'success': False
    }
    
    # Get track data from database
    track_response = supabase.from_("Track").select("track_id, title, duration_ms, spotify_id").eq("track_id", track_id).limit(1).execute()
    if not track_response.data:
        return results
    
    db_track = track_response.data[0]
    
    # Get Spotify track ID
    if not spotify_track_id:
        spotify_track_id = db_track.get('spotify_id')
        if spotify_track_data and 'id' in spotify_track_data:
            spotify_track_id = spotify_track_data['id']
    
    # Get token if not provided
    if not token:
        try:
            token = get_spotify_token()
        except Exception:
            return results
    
    # Get artist name for better matching
    artist_name = None
    
    if spotify_track_data:
        artists = spotify_track_data.get('artists', [])
        if artists:
            artist_name = artists[0].get('name')
    elif spotify_track_id:
        try:
            spotify_track_data = fetch_spotify_api(f"tracks/{spotify_track_id}", token)
            artists = spotify_track_data.get('artists', [])
            if artists:
                artist_name = artists[0].get('name')
        except Exception as e:
            pass
    
    # 1. Fetch and save audio features
    try:
        af_response = supabase.from_("AudioFeatures").select("track_id").eq("track_id", track_id).limit(1).execute()
        if not af_response.data:
            success = _fetch_and_save_audio_features(
                track_id=track_id,
                track_title=db_track['title'],
                artist_name=artist_name,
                duration_ms=db_track['duration_ms'],
                spotify_track_id=spotify_track_id
            )
            results['audio_features'] = success
        else:
            results['audio_features'] = True  # Already exists
    except Exception as e:
        pass
    
    # 2. Link genres to track (from all artists)
    try:
        genres_linked = link_track_genres(
            track_id=track_id,
            spotify_track_data=spotify_track_data,
            token=token
        )
        results['genres'] = genres_linked > 0
    except Exception as e:
        pass
    
    results['success'] = results['audio_features'] or results['genres']
    return results


# Alias for backward compatibility with audio_features_ingest.py
def fetch_and_save_audio_features(track_id: int, track_title: str, 
                                  artist_name: Optional[str] = None,
                                  duration_ms: Optional[int] = None,
                                  spotify_track_id: Optional[str] = None) -> bool:
    """
    Fetch audio features for a track and save them to the database.
    Public wrapper for backward compatibility.
    """
    return _fetch_and_save_audio_features(track_id, track_title, artist_name, duration_ms, spotify_track_id)

