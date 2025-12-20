from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.sqlalchemy_engine import SessionLocal
from app.models import Playlist, PlaylistTrack


class PlaylistService:
    def __init__(self, app):
        self.app = app

    def create_service(self):
        return self

    def _session(self) -> Session:
        return SessionLocal()

    # Playlists
    def list_playlists(self, owner_id: int) -> List[Playlist]:
        with self._session() as db:
            stmt = select(Playlist).where(Playlist.owner_id == owner_id)
            return list(db.scalars(stmt).all())

    def create_playlist(self, owner_id: int, name: str, description: Optional[str] = None) -> Playlist:
        with self._session() as db:
            pl = Playlist(name=name, owner_id=owner_id)
            db.add(pl)
            db.commit()
            db.refresh(pl)
            return pl

    def get_playlist(self, playlist_id: int, owner_id: int) -> Optional[Playlist]:
        with self._session() as db:
            stmt = select(Playlist).where(Playlist.id == playlist_id, Playlist.owner_id == owner_id)
            return db.scalars(stmt).first()

    def delete_playlist(self, playlist_id: int, owner_id: int) -> bool:
        with self._session() as db:
            stmt = select(Playlist).where(Playlist.id == playlist_id, Playlist.owner_id == owner_id)
            pl = db.scalars(stmt).first()
            if not pl:
                return False
            db.delete(pl)
            db.commit()
            return True

    # Tracks
    def add_track(self, playlist_id: int, owner_id, track: Dict[str, Any]) -> Optional[PlaylistTrack]:
        with self._session() as db:
            # verify playlist ownership
            stmt = select(Playlist).where(Playlist.id == playlist_id, Playlist.owner_id == owner_id)
            pl = db.scalars(stmt).first()
            if not pl:
                return None
            pt = PlaylistTrack(
                playlist_id=playlist_id,
                track_id=track.get("track_id"),
            )
            db.add(pt)
            db.commit()
            db.refresh(pt)
            return pt

    def remove_track(self, playlist_id: int, track_id: int, owner_id) -> bool:
        with self._session() as db:
            # verify playlist ownership
            stmt = select(Playlist).where(Playlist.id == playlist_id, Playlist.owner_id == owner_id)
            pl = db.scalars(stmt).first()
            if not pl:
                return False
            # Remove track using composite key (playlist_id, track_id, date_added)
            # Get the track to delete
            tstmt = select(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id, PlaylistTrack.track_id == track_id)
            tr = db.scalars(tstmt).first()
            if not tr:
                return False
            db.delete(tr)
            db.commit()
            return True

    def reorder_tracks(self, playlist_id: int, new_order_ids: List[int], owner_id) -> bool:
        with self._session() as db:
            # verify playlist ownership
            stmt = select(Playlist).where(Playlist.id == playlist_id, Playlist.owner_id == owner_id)
            pl = db.scalars(stmt).first()
            if not pl:
                return False
            # For now, just verify that all tracks exist
            for track_id in new_order_ids:
                tstmt = select(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id, PlaylistTrack.track_id == track_id)
                if not db.scalars(tstmt).first():
                    return False
            return True
