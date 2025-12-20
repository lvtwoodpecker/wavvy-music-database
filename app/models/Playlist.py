from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, UUID, Boolean
from sqlalchemy.orm import relationship
from app.db.sqlalchemy_engine import Base


class Playlist(Base):
    __tablename__ = "Playlist"

    id = Column("playlist_id", Integer, primary_key=True, autoincrement=True)
    name = Column("title", String, nullable=False)
    owner_id = Column("owner_listener_id", UUID(as_uuid=True), ForeignKey("Listener.listener_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    is_collaborative = Column(Boolean, default=False, nullable=False)

    tracks = relationship("PlaylistTrack", back_populates="playlist", cascade="all, delete-orphan", order_by="PlaylistTrack.date_added")

    def to_dict(self, include_tracks: bool = False, db_session=None):
        data = {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_public": self.is_public,
            "is_collaborative": self.is_collaborative,
        }
        if include_tracks:
            # Get Track metadata by joining PlaylistTrack with Track
            track_dicts = []
            if db_session:
                from sqlalchemy import text
                result = db_session.execute(text(
                    'SELECT t.track_id, t.title, a.name, t.audio_file_url, t.duration_ms '
                    'FROM "PlaylistTrack" pt '
                    'JOIN "Track" t ON pt.track_id = t.track_id '
                    'LEFT JOIN "TrackArtist" ta ON t.track_id = ta.track_id '
                    'LEFT JOIN "Artist" a ON ta.artist_id = a.artist_id '
                    'WHERE pt.playlist_id = :playlist_id '
                    'ORDER BY pt.date_added'
                ), {"playlist_id": self.id})
                
                for row in result:
                    track_id, title, artist, audio_url, duration = row
                    track_dicts.append({
                        "id": track_id,
                        "track_id": track_id,
                        "title": title or "Untitled",
                        "artist": artist or "Unknown artist",
                        "audio_url": audio_url,
                        "duration_ms": duration or 0,
                    })
            else:
                # Fallback if no session provided
                for pt in self.tracks:
                    track_dicts.append({
                        "id": pt.track_id,
                        "track_id": pt.track_id,
                        "title": pt.title or "Untitled",
                        "artist": pt.artist or "Unknown artist",
                        "audio_url": pt.audio_url,
                        "duration_ms": pt.duration_ms or 0,
                    })
            data["tracks"] = track_dicts
        return data
