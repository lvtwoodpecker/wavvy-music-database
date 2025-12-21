from sqlalchemy import Column, DateTime, Boolean, ForeignKey, func, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.sqlalchemy_engine import Base


class PlayHistory(Base):
    __tablename__ = "PlayHistory"
    __table_args__ = {"schema": "public"}  

    listener_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.Listener.listener_id", ondelete="CASCADE"), 
        primary_key=True,
        nullable=False,
    )

    track_id = Column(
        BigInteger,
        ForeignKey("public.Track.track_id", ondelete="CASCADE"), 
        primary_key=True,
        nullable=False,
    )

    played_at = Column(
        DateTime(timezone=True),
        primary_key=True,
        server_default=func.now(),
        nullable=False,
    )

    is_skip = Column(Boolean, default=False, nullable=False)

    # optional but nice
    listener = relationship("Listener", back_populates="play_history")
    track = relationship("Track", back_populates="play_history")     

    def to_dict(self):
        return {
            "listener_id": str(self.listener_id) if self.listener_id else None,
            "track_id": self.track_id,
            "played_at": self.played_at.isoformat() if self.played_at else None,
            "is_skip": self.is_skip,
        }
