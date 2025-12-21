from typing import List, Dict, Any
from app.db.supabase_client import SupabaseClient


class LibraryService:
    """Fetch tracks for the library/now playing queue."""

    def __init__(self, app):
        self.app = app
        self.supabase = app.supabase if hasattr(app, "supabase") else None

    def create_service(self):
        return self

    def list_tracks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return tracks with album/artist/cover hydrated for the player UI."""
        if not self.supabase:
            return []

        table_candidates = ["Track"]
        select_clause = (
            "track_id,title,duration_ms,audio_file_url,"
            "AlbumTrack(track_no,Album(title,cover_image_url)),"
            "TrackArtist(Artist(name))"
        )

        for tbl in table_candidates:
            try:
                resp = self.supabase.table(tbl).select(select_clause).limit(limit).execute()
                if not hasattr(resp, "data") or not resp.data:
                    continue

                enriched: List[Dict[str, Any]] = []
                for row in resp.data:
                    album_track = (row.get("AlbumTrack") or [])
                    album_entry = album_track[0] if album_track else {}
                    album_info = album_entry.get("Album") or {}
                    track_artists = row.get("TrackArtist") or []
                    first_artist = track_artists[0].get("Artist") if track_artists else {}

                    enriched.append({
                        "track_id": row.get("track_id"),
                        "title": row.get("title"),
                        "duration_ms": row.get("duration_ms"),
                        "audio_file_url": row.get("audio_file_url"),
                        "album_title": album_info.get("title"),
                        "cover_image_url": album_info.get("cover_image_url"),
                        "artist_name": first_artist.get("name"),
                        "track_no": album_entry.get("track_no"),
                    })

                return enriched
            except Exception as e:
                print(f"[LibraryService] Failed to fetch tracks from {tbl}: {e}")
                continue

        return []
