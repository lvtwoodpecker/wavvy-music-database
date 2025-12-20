"""
SearchService provides business logic for track search operations.
Uses SearchRepository for data access and adds additional processing/validation.
"""

from typing import List, Dict, Any, Optional
from flask import Flask
from app.services.service import Service
from app.services.search.search_repository import SearchRepository


class SearchService(Service):
    """
    Service for managing search operations.
    
    Provides high-level search functionality with:
    - Query validation and preprocessing
    - Result formatting
    - Search mode selection (FTS, fuzzy, hybrid)
    """
    
    def __init__(self, app: Flask):
        """
        Initialize the SearchService.
        
        Args:
            app: Flask application instance
        """
        super().__init__(app)
        self.create_service()
    
    def create_service(self):
        """Initialize the search repository."""
        self._repository = SearchRepository(self.db_session_factory)
    
    @property
    def repository(self) -> SearchRepository:
        """Get the search repository."""
        return self._repository
    
    def search(
        self,
        query: str,
        mode: str = "hybrid",
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search for tracks based on query string.
        
        Args:
            query: Search query string
            mode: Search mode - "fts" (full-text), "fuzzy", or "hybrid" (default)
            limit: Maximum number of results to return (1-100)
            offset: Number of results to skip for pagination
            
        Returns:
            Dictionary containing:
                - results: List of track dictionaries
                - query: Original query string
                - count: Number of results returned in this response
                - limit: Applied limit
                - offset: Applied offset
        """
        # Validate and sanitize inputs
        query = self._sanitize_query(query)
        if not query:
            return {
                "results": [],
                "query": "",
                "count": 0,
                "limit": limit,
                "offset": offset
            }
        
        # Clamp limit to reasonable range
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        
        # Execute search based on mode
        if mode == "fts":
            results = self._repository.search_tracks_fts(query, limit, offset)
        elif mode == "fuzzy":
            results = self._repository.search_tracks_fuzzy(query, limit)
        else:  # hybrid (default)
            results = self._repository.search_tracks_hybrid(query, limit, offset)
        
        # Convert results to dictionaries
        tracks = [track.to_dict() for track in results]
        
        return {
            "results": tracks,
            "query": query,
            "count": len(tracks),  # Number of results returned in this response
            "limit": limit,
            "offset": offset
        }
    
    def search_by_title(self, title: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search tracks specifically by title.
        
        Args:
            title: Track title to search for
            limit: Maximum number of results
            
        Returns:
            List of track dictionaries
        """
        result = self.search(title, mode="hybrid", limit=limit)
        return result["results"]
    
    def search_by_artist(self, artist: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search tracks by artist name.
        
        Args:
            artist: Artist name to search for
            limit: Maximum number of results
            
        Returns:
            List of track dictionaries
        """
        result = self.search(artist, mode="hybrid", limit=limit)
        return result["results"]
    
    def get_track(self, track_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single track by ID.
        
        Args:
            track_id: Track ID to retrieve
            
        Returns:
            Track dictionary or None if not found
        """
        track = self._repository.get_track_by_id(track_id)
        return track.to_dict() if track else None
    
    def refresh_index(self) -> bool:
        """
        Refresh the search index from source tables.
        
        This should be called after bulk updates to Track, Artist, or Album data.
        
        Returns:
            True if successful, False otherwise
        """
        return self._repository.refresh_search_index()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get search index statistics.
        
        Returns:
            Dictionary with index statistics
        """
        total_tracks = self._repository.get_total_tracks()
        return {
            "total_tracks": total_tracks,
            "index_name": "ods_track_search"
        }
    
    def _sanitize_query(self, query: str) -> str:
        """
        Sanitize and prepare search query.
        
        Args:
            query: Raw query string
            
        Returns:
            Sanitized query string
        """
        if not query:
            return ""
        
        # Strip whitespace and convert to string
        query = str(query).strip()
        
        # Limit query length to prevent abuse
        max_length = 200
        if len(query) > max_length:
            query = query[:max_length]
        
        return query
