"""
SearchRepository provides data access methods for the ods_track_search table.
Handles all database queries for search operations using SQLAlchemy ORM.
"""

from typing import List, Optional, Dict, Any, Callable
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session
from app.models.ODSTrackSearch import ODSTrackSearch

SessionFactory = Callable[[], Session]


class SearchRepository:
    """
    Repository for search-related database operations.
    
    Provides methods for:
    - Full-text search using PostgreSQL tsvector
    - Fuzzy search using trigram similarity
    - Hybrid search combining FTS and fuzzy matching
    """
    
    def __init__(self, db_session_factory: SessionFactory):
        """
        Initialize the SearchRepository.
        
        Args:
            db_session_factory: Factory function to create database sessions
        """
        self.db_session_factory = db_session_factory
    
    def search_tracks_fts(
        self, 
        query: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[ODSTrackSearch]:
        """
        Search tracks using Full-Text Search (FTS).
        
        Uses PostgreSQL's tsvector and tsquery for ranked full-text search.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            List of ODSTrackSearch objects matching the query, ordered by relevance
        """
        with self.db_session_factory() as session:
            # Create tsquery from search string
            ts_query = func.plainto_tsquery('english', query)
            
            # Search using tsvector and rank results
            results = (
                session.query(ODSTrackSearch)
                .filter(ODSTrackSearch.search_vector.op('@@')(ts_query))
                .order_by(
                    func.ts_rank(ODSTrackSearch.search_vector, ts_query).desc()
                )
                .limit(limit)
                .offset(offset)
                .all()
            )
            
            return results
    
    def search_tracks_fuzzy(
        self, 
        query: str, 
        limit: int = 50, 
        similarity_threshold: float = 0.3
    ) -> List[ODSTrackSearch]:
        """
        Search tracks using trigram fuzzy matching.
        
        Uses PostgreSQL's pg_trgm extension for fuzzy string matching.
        Useful for handling typos and partial matches.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List of ODSTrackSearch objects matching the query, ordered by similarity
        """
        with self.db_session_factory() as session:
            # Use trigram similarity for fuzzy matching
            results = (
                session.query(ODSTrackSearch)
                .filter(
                    or_(
                        func.similarity(ODSTrackSearch.title, query) > similarity_threshold,
                        func.similarity(ODSTrackSearch.artist_names, query) > similarity_threshold,
                        func.similarity(ODSTrackSearch.album_title, query) > similarity_threshold
                    )
                )
                .order_by(
                    func.greatest(
                        func.similarity(ODSTrackSearch.title, query),
                        func.similarity(ODSTrackSearch.artist_names, query),
                        func.similarity(ODSTrackSearch.album_title, query)
                    ).desc()
                )
                .limit(limit)
                .all()
            )
            
            return results
    
    def search_tracks_hybrid(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0,
        fuzzy_threshold: float = 0.3
    ) -> List[ODSTrackSearch]:
        """
        Hybrid search combining FTS and fuzzy matching.
        
        First tries FTS, then falls back to fuzzy search if few results found.
        Provides best of both worlds: exact matching and typo tolerance.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            fuzzy_threshold: Minimum similarity for fuzzy matching
            
        Returns:
            List of ODSTrackSearch objects matching the query
        """
        # Try FTS first
        fts_results = self.search_tracks_fts(query, limit=limit, offset=offset)
        
        # If FTS returns enough results, use those
        if len(fts_results) >= min(10, limit):
            return fts_results
        
        # Otherwise, combine with fuzzy search results
        fuzzy_results = self.search_tracks_fuzzy(
            query, 
            limit=limit - len(fts_results),
            similarity_threshold=fuzzy_threshold
        )
        
        # Combine and deduplicate based on track_id
        seen_ids = {track.track_id for track in fts_results}
        combined_results = list(fts_results)
        
        for track in fuzzy_results:
            if track.track_id not in seen_ids:
                combined_results.append(track)
                seen_ids.add(track.track_id)
        
        return combined_results[:limit]
    
    def get_track_by_id(self, track_id: int) -> Optional[ODSTrackSearch]:
        """
        Get a single track by ID from the search index.
        
        Args:
            track_id: Track ID to retrieve
            
        Returns:
            ODSTrackSearch object or None if not found
        """
        with self.db_session_factory() as session:
            return session.query(ODSTrackSearch).filter(
                ODSTrackSearch.track_id == track_id
            ).first()
    
    def refresh_search_index(self) -> bool:
        """
        Refresh the entire search index from source tables.
        
        This calls the refresh_ods_track_search() PostgreSQL function
        to rebuild the denormalized search table.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_session_factory() as session:
                session.execute(text("SELECT refresh_ods_track_search()"))
                session.commit()
                return True
        except Exception as e:
            print(f"Error refreshing search index: {e}")
            return False
    
    def get_total_tracks(self) -> int:
        """
        Get the total number of tracks in the search index.
        
        Returns:
            Total count of tracks
        """
        with self.db_session_factory() as session:
            return session.query(func.count(ODSTrackSearch.track_id)).scalar()
