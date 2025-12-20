from typing import Callable

from app.services import service
from app.services.search.search_repository import SearchRepository
from app.services.search.search_track import SearchTrack

from sqlalchemy.orm import Session

SessionFactory = Callable[[], Session]

class SearchService(service.Service):
    """
    Service for managing search operations.
    
    Aggregates SearchRepository and SearchTrack for track searching.
    Provides methods for FTS, trigram, and hybrid search.
    """

    def __init__(self, app):
        super().__init__(app)
        self.create_service()
        
    def create_service(self):
        # repo has to be created first
        self._repo = self._create_repo()
        self._track_search = self._create_track_search()
        
    @property
    def repository(self) -> SearchRepository:
        """Get the search repository."""
        if self._repo is None:
            self._repo = self._create_repo()
        return self._repo

    @property
    def track_search(self) -> SearchTrack:
        """Get the track search service."""
        if self._track_search is None:
            self._track_search = self._create_track_search()
        return self._track_search
    
    def _create_repo(self) -> SearchRepository:
        return SearchRepository(
            db_session_factory=self._db_session_factory,
        )
        
    def _create_track_search(self) -> SearchTrack:
        return SearchTrack(
            repo=self._repo
        )
    
    # Convenience methods for API routes
    def search(self, query: str, limit: int = 25) -> dict:
        """
        Search for tracks using hybrid FTS + trigram approach.
        
        Args:
            query: Search query string
            limit: Maximum results to return
            
        Returns:
            Dictionary with query, results, and search method used
        """
        return self._track_search.search_tracks(query, limit=limit)
    
    def refresh_index(self) -> bool:
        """Refresh the search index from source tables."""
        return self._repo.refresh_search_index()
    
    def get_stats(self) -> dict:
        """Get search index statistics."""
        return {
            "total_tracks": self._repo.get_total_tracks(),
            "index_name": "ods_track_search"
        }
