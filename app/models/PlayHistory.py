from sqlalchemy import Column, Integer, UUID, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from app.db.sqlalchemy_engine import Base


class PlayHistory(Base):
    __tablename__ = "PlayHistory"

    play_history_id = Column(Integer, primary_key=True, autoincrement=True)
    listener_id = Column(UUID(as_uuid=True), nullable=False)
    track_id = Column(Integer, nullable=False)
    played_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_skip = Column(Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            "play_history_id": self.play_history_id,
            "listener_id": self.listener_id,
            "track_id": self.track_id,
            "played_at": self.played_at.isoformat() if self.played_at else None,
            "is_skip": self.is_skip,
        }
