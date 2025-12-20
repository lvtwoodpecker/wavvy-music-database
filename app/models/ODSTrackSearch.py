from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.sql import func
from app.db.sqlalchemy_engine import Base


class ODSTrackSearch(Base):
    """
    ORM model for the ods_track_search table.
    
    This table provides a denormalized view of track data optimized for search operations.
    It includes Full-Text Search (FTS) with tsvector and trigram indexes for fuzzy matching.
    
    Attributes:
        track_id: Primary key, references Track table
        title: Track title
        artist_names: Comma-separated list of artist names
        album_title: Album title
        genre_names: Comma-separated list of genre names
        duration_ms: Track duration in milliseconds
        audio_file_url: URL to the audio file
        cover_image_url: URL to the album cover image
        search_vector: PostgreSQL tsvector for full-text search
        updated_at: Timestamp of last update
    """
    
    __tablename__ = "ods_track_search"
    
    track_id = Column(BigInteger, primary_key=True)
    title = Column(String, nullable=False)
    artist_names = Column(Text)
    album_title = Column(String)
    genre_names = Column(Text)
    duration_ms = Column(Integer)
    audio_file_url = Column(Text)
    cover_image_url = Column(Text)
    search_vector = Column(TSVECTOR)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ODSTrackSearch(track_id={self.track_id}, title='{self.title}', artist='{self.artist_names}')>"
    
    def to_dict(self):
        """Convert model instance to dictionary for API responses."""
        return {
            "track_id": self.track_id,
            "title": self.title,
            "artist_names": self.artist_names,
            "album_title": self.album_title,
            "genre_names": self.genre_names,
            "duration_ms": self.duration_ms,
            "audio_file_url": self.audio_file_url,
            "cover_image_url": self.cover_image_url,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
