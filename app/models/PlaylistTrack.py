from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, func, UUID
from sqlalchemy.orm import relationship
from app.db.sqlalchemy_engine import Base


class PlaylistTrack(Base):
    __tablename__ = "PlaylistTrack"

    playlist_id = Column(Integer, ForeignKey("Playlist.playlist_id"), primary_key=True, nullable=False)
    track_id = Column(Integer, primary_key=True, nullable=False)
    date_added = Column(DateTime(timezone=True), primary_key=True, server_default=func.now(), nullable=False)
    added_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    date_removed = Column(DateTime(timezone=True), nullable=True)
    removed_by_user_id = Column(UUID(as_uuid=True), nullable=True)

    playlist = relationship("Playlist", back_populates="tracks")

    def to_dict(self):
        return {
            "id": f"{self.playlist_id}-{self.track_id}",
            "playlist_id": self.playlist_id,
            "track_id": self.track_id,
            "title": None,
            "artist": None,
            "audio_url": None,
            "cover_url": None,
            "duration_ms": None,
            "extra": {},
        }
