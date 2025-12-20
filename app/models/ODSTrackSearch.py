# app/models/ods_track_search.py
from __future__ import annotations

from sqlalchemy import BigInteger, Integer, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column
from app.db.sqlalchemy_engine import Base

class ODSTrackSearch(Base):
    """
    Denormalized read model for fast search.
    Backfilled/refreshed from OLTP tables (Track, Artist, Album, Genre).
    
    Uses both FTS (full-text search) and trigram similarity for flexible matching.
    """
    __tablename__ = "ods_track_search"
    __table_args__ = (
        # indexes (FTS + trigram). Note: trigram indexes must be created via SQL migration
        # if your environment doesn't support gin_trgm_ops directly here.
        Index("ods_track_search_tsv_idx", "search_tsv", postgresql_using="gin"),
    )

    track_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    track_title: Mapped[str] = mapped_column(Text, nullable=False)
    artist_names: Mapped[str] = mapped_column(Text, nullable=False, default="")
    album_titles: Mapped[str] = mapped_column(Text, nullable=False, default="")
    genre_names: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # normalized columns for trigram search (avoid unaccent() in index expression)
    track_title_norm: Mapped[str | None] = mapped_column(Text)
    artist_names_norm: Mapped[str | None] = mapped_column(Text)
    album_titles_norm: Mapped[str | None] = mapped_column(Text)

    search_tsv: Mapped[str | None] = mapped_column(TSVECTOR)

    duration_ms: Mapped[int | None] = mapped_column(Integer)
    spotify_id: Mapped[str | None] = mapped_column(Text)
    date_added: Mapped[object | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<ODSTrackSearch(track_id={self.track_id}, title='{self.track_title}', artist='{self.artist_names}')>"
    
    def to_dict(self):
        """Convert model instance to dictionary for API responses."""
        return {
            "track_id": self.track_id,
            "title": self.track_title,
            "artist_names": self.artist_names,
            "album_title": self.album_titles,
            "genre_names": self.genre_names,
            "duration_ms": self.duration_ms,
            "spotify_id": self.spotify_id,
            "date_added": self.date_added.isoformat() if self.date_added else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
