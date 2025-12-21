from sqlalchemy import Column, BigInteger, String, ForeignKey, DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.sqlalchemy_engine import Base
from sqlalchemy import text



class Playlist(Base):
    __tablename__ = "Playlist"
    __table_args__ = {"schema": "public"} 

    id = Column("playlist_id", BigInteger, primary_key=True, autoincrement=True) 
    name = Column("title", String, nullable=True) 
    owner_id = Column(
        "owner_listener_id",
        UUID(as_uuid=True),
        ForeignKey("public.Listener.listener_id", ondelete="SET NULL"), 
        nullable=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    is_public = Column(Boolean, server_default="true", nullable=False)        
    is_collaborative = Column(Boolean, server_default="false", nullable=False) 

    tracks = relationship(
        "PlaylistTrack",
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="PlaylistTrack.date_added",
    )

    def to_dict(self, include_tracks: bool = False, db_session=None):
        data = {
            "id": self.id,
            "name": self.name,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_public": self.is_public,
            "is_collaborative": self.is_collaborative,
        }

        if include_tracks:
            track_dicts = []

            if db_session:
                result = db_session.execute(
                    text(
                        'SELECT t.track_id, t.title, a.name, t.audio_file_url, t.duration_ms '
                        'FROM public."PlaylistTrack" pt '
                        'JOIN public."Track" t ON pt.track_id = t.track_id '
                        'LEFT JOIN public."TrackArtist" ta ON t.track_id = ta.track_id '
                        'LEFT JOIN public."Artist" a ON ta.artist_id = a.artist_id '
                        'WHERE pt.playlist_id = :playlist_id '
                        'ORDER BY pt.date_added'
                    ),
                    {"playlist_id": self.id},
                )

                for track_id, title, artist, audio_url, duration in result:
                    track_dicts.append({
                        "id": track_id,
                        "track_id": track_id,
                        "title": title or "Untitled",
                        "artist": artist or "Unknown artist",
                        "audio_url": audio_url,
                        "duration_ms": duration or 0,
                    })
            else:
                for pt in self.tracks:
                    track_dicts.append({
                        "id": pt.track_id,
                        "track_id": pt.track_id,
                        "title": getattr(pt, "title", None) or "Untitled",
                        "artist": getattr(pt, "artist", None) or "Unknown artist",
                        "audio_url": getattr(pt, "audio_url", None),
                        "duration_ms": getattr(pt, "duration_ms", 0) or 0,
                    })

            data["tracks"] = track_dicts

        return data
