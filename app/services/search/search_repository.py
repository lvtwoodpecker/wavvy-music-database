# app/services/search/search_repository.py
from __future__ import annotations

import logging
from typing import List, Callable
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.ODSTrackSearch import ODSTrackSearch
from app.services.search.search_types import TrackSearchHit

SessionFactory = Callable[[], Session]

logger = logging.getLogger(__name__)


class SearchRepository:
    """
    Repository for search-related database operations.
    
    Provides methods for FTS (full-text search) and trigram similarity matching.
    """
    
    def __init__(self, db_session_factory: SessionFactory) -> None:
        self._db_session_factory = db_session_factory

    def _get_session(self) -> Session:
        return self._db_session_factory()
    
    def fts_search(self, q: str, limit: int) -> List[TrackSearchHit]:
        """
        Full-text search using PostgreSQL tsvector.
        
        Args:
            q: Search query string
            limit: Maximum results to return
            
        Returns:
            List of TrackSearchHit objects ranked by relevance
        """
        tsq = func.websearch_to_tsquery("simple", func.unaccent(q))
        rank = func.ts_rank_cd(ODSTrackSearch.search_tsv, tsq)

        stmt = (
            select(
                ODSTrackSearch.track_id,
                ODSTrackSearch.track_title,
                ODSTrackSearch.artist_names,
                ODSTrackSearch.album_titles,
                ODSTrackSearch.genre_names,
                rank.label("score"),
            )
            .where(ODSTrackSearch.search_tsv.op("@@")(tsq))
            .order_by(rank.desc())
            .limit(limit)
        )

        rows = self._get_session().execute(stmt).all()
        return [
            TrackSearchHit(
                track_id=r.track_id,
                track_title=r.track_title,
                artist_names=r.artist_names,
                album_titles=r.album_titles,
                genre_names=r.genre_names,
                score=float(r.score or 0.0),
                source="fts",
            )
            for r in rows
        ]

    def trigram_search(self, q: str, limit: int) -> List[TrackSearchHit]:
        """
        Trigram similarity search for fuzzy matching.
        
        Args:
            q: Search query string
            limit: Maximum results to return
            
        Returns:
            List of TrackSearchHit objects ordered by similarity score
        """
        q_norm = func.lower(func.unaccent(q))
        score = func.greatest(
            func.similarity(ODSTrackSearch.track_title_norm, q_norm),
            func.similarity(ODSTrackSearch.artist_names_norm, q_norm),
            func.similarity(ODSTrackSearch.album_titles_norm, q_norm),
        )

        # `%` operator in Postgres trigram is exposed as `.op('%')`
        trigram_filter = (
            ODSTrackSearch.track_title_norm.op("%")(q_norm)
            | ODSTrackSearch.artist_names_norm.op("%")(q_norm)
            | ODSTrackSearch.album_titles_norm.op("%")(q_norm)
        )

        stmt = (
            select(
                ODSTrackSearch.track_id,
                ODSTrackSearch.track_title,
                ODSTrackSearch.artist_names,
                ODSTrackSearch.album_titles,
                ODSTrackSearch.genre_names,
                score.label("score"),
            )
            .where(trigram_filter)
            .order_by(score.desc())
            .limit(limit)
        )

        rows = self._get_session().execute(stmt).all()
        return [
            TrackSearchHit(
                track_id=r.track_id,
                track_title=r.track_title,
                artist_names=r.artist_names,
                album_titles=r.album_titles,
                genre_names=r.genre_names,
                score=float(r.score or 0.0),
                source="trigram",
            )
            for r in rows
        ]
    
    def refresh_search_index(self) -> bool:
        """
        Refresh the entire search index from source tables.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self._get_session()
            session.execute(text("SELECT refresh_ods_track_search()"))
            session.commit()
            logger.info("Search index refreshed successfully")
            return True
        except Exception as e:
            logger.error(f"Error refreshing search index: {e}", exc_info=True)
            return False
    
    def get_total_tracks(self) -> int:
        """
        Get the total number of tracks in the search index.
        
        Returns:
            Total count of tracks
        """
        session = self._get_session()
        return session.query(func.count(ODSTrackSearch.track_id)).scalar()
