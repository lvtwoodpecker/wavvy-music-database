# app/models/Track.py
from __future__ import annotations

from datetime import datetime
from sqlalchemy import BigInteger, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column,relationship
from app.db.sqlalchemy_engine import Base


class Track(Base):
    __tablename__ = "Track"
    __table_args__ = {"schema": "public"}

    track_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    title: Mapped[str] = mapped_column(Text, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    isrc: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)  

    audio_file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    spotify_id: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)

    date_added: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),   
        nullable=False,             
    )

    playlist_entries = relationship("PlaylistTrack", back_populates="track")
    play_history = relationship("PlayHistory", back_populates="track")

    def __repr__(self):
        return f"<Track(track_id={self.track_id}, title='{self.title}')>"
