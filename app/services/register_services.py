from app.services.user.user_service import UserService
from app.services.stripe.stripe_service import StripeService
from app.services.playlist.playlist_service import PlaylistService
from app.services.library.library_service import LibraryService


class APIServices:
    
    """ 
    Aggregates all API services for easy access.
    Keeps references to individual services like UserService and StripeService.
    This class is initialized with the main application instance.
    
    Attributes:
        user_service (UserService): Service for user-related operations.
        stripe_service (StripeService): Service for Stripe-related operations.
    
    Methods:
        create_services(): Initializes all services.
    """
    
    def __init__(self, app):
        self._stripe_service = StripeService(app)
        self._user_service = UserService(app, stripe_service=self._stripe_service)
        self._playlist_service = PlaylistService(app)
        self._library_service = LibraryService(app)
    
    @property
    def user_service(self) -> UserService:
        return self._user_service
    
    @property
    def stripe_service(self) -> StripeService:
        return self._stripe_service
    
    @property
    def playlist_service(self) -> PlaylistService:
        return self._playlist_service

    @property
    def library_service(self) -> LibraryService:
        return self._library_service
    
    def create_services(self):
        self._stripe_service.create_service()
        self._user_service.create_service()
        self._playlist_service.create_service()
        self._library_service.create_service()