from sqlalchemy import Column, BigInteger, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.sqlalchemy_engine import Base


class PlaylistTrack(Base):
    __tablename__ = "PlaylistTrack"
    __table_args__ = {"schema": "public"} 

    playlist_id = Column(
        BigInteger,
        ForeignKey("public.Playlist.playlist_id", ondelete="CASCADE"), 
        primary_key=True,
        nullable=False,
    )

    track_id = Column(
        BigInteger,
        ForeignKey("public.Track.track_id", ondelete="CASCADE"), 
        primary_key=True,
        nullable=False,
    )

    date_added = Column(
        DateTime(timezone=True),
        primary_key=True,
        server_default=func.now(),
        nullable=False,
    )

    added_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.Listener.listener_id", ondelete="SET NULL"),  # matches DB
        nullable=True,
    )

    date_removed = Column(DateTime(timezone=True), nullable=True)

    removed_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.Listener.listener_id", ondelete="SET NULL"),  # matches DB
        nullable=True,
    )

    playlist = relationship("Playlist", back_populates="tracks")
    track = relationship("Track", back_populates="playlist_entries")

    def to_dict(self):
        return {
            "id": f"{self.playlist_id}-{self.track_id}-{self.date_added.isoformat() if self.date_added else ''}",
            "playlist_id": self.playlist_id,
            "track_id": self.track_id,
            # you can populate these if you join Track/Artist
            "title": None,
            "artist": None,
            "audio_url": None,
            "cover_url": None,
            "duration_ms": None,
            "extra": {},
        }
