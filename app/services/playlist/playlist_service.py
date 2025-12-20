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
    def add_track(self, playlist_id: int, owner_id: int, track: Dict[str, Any]) -> Optional[PlaylistTrack]:
        with self._session() as db:
            # verify playlist ownership
            stmt = select(Playlist).where(Playlist.id == playlist_id, Playlist.owner_id == owner_id)
            pl = db.scalars(stmt).first()
            if not pl:
                return None
            position = (pl.tracks[-1].position + 1) if pl.tracks else 0
            pt = PlaylistTrack(
                playlist_id=playlist_id,
                position=position,
                track_id=track.get("track_id"),
                title=track.get("title", "Untitled"),
                artist=track.get("artist"),
                audio_url=track.get("audio_url", ""),
                cover_url=track.get("cover_url"),
                duration_ms=track.get("duration_ms"),
                extra=track.get("extra"),
            )
            db.add(pt)
            db.commit()
            db.refresh(pt)
            return pt

    def remove_track(self, playlist_id: int, track_id: int, owner_id: int) -> bool:
        with self._session() as db:
            # verify playlist ownership
            stmt = select(Playlist).where(Playlist.id == playlist_id, Playlist.owner_id == owner_id)
            pl = db.scalars(stmt).first()
            if not pl:
                return False
            tstmt = select(PlaylistTrack).where(PlaylistTrack.id == track_id, PlaylistTrack.playlist_id == playlist_id)
            tr = db.scalars(tstmt).first()
            if not tr:
                return False
            db.delete(tr)
            # re-number positions
            for i, track in enumerate(sorted(pl.tracks, key=lambda x: x.position)):
                track.position = i
            db.commit()
            return True

    def reorder_tracks(self, playlist_id: int, new_order_ids: List[int], owner_id: int) -> bool:
        with self._session() as db:
            # verify playlist ownership
            stmt = select(Playlist).where(Playlist.id == playlist_id, Playlist.owner_id == owner_id)
            pl = db.scalars(stmt).first()
            if not pl:
                return False
            id_to_track = {t.id: t for t in pl.tracks}
            if set(id_to_track.keys()) != set(new_order_ids):
                return False
            for pos, tid in enumerate(new_order_ids):
                id_to_track[tid].position = pos
            db.commit()
            return True
