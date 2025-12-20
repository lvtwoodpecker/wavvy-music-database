# app/models/Track.py
from __future__ import annotations

from sqlalchemy import BigInteger, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.sqlalchemy_engine import Base


class Track(Base):
    """
    Track model representing songs in the database.
    """
    __tablename__ = "Track"

    track_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    audio_file_url: Mapped[str | None] = mapped_column(Text)
    spotify_id: Mapped[str | None] = mapped_column(Text)
    date_added: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<Track(track_id={self.track_id}, title='{self.title}')>"
