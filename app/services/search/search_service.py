
from typing import Optional, Callable

from app.services import service
from app.services.search.search_repository import SearchRepository
from app.services.search.search_track import SearchTrack


from sqlalchemy.orm import Session

SessionFactory = Callable[[], Session]

class SearchService(service.Service):
    """Service for managing User-related operations.
    
    This service aggregates sub-services for user creation, status management, and user lookups.
    It depends on StripeService for handling Stripe-related operations during user creation.
    """

    def __init__(self, app):
        super().__init__(app)
        self.create_service()
        
    def create_service(self):
        # repo has to be created first
        self._repo = self._create_repo()
        self._track_search = self._create_track_search()
        
    @property
    def stripe_service(self) -> SearchRepository:
        if self._repo is None:
            self._repo = self._create_repo()
        return self._repo

    @property
    def track_search(self) -> SearchTrack:
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
