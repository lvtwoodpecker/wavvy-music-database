from app.services import service
from app.services.stripe.stripe_service import StripeService
from app.services.user.create_user_account import UserCreationService
from app.services.user.account_status import UserStatusService
from app.services.user.find_user import FindUserService

class UserService(service.Service):
    
    """Service for managing User-related operations."""
    def __init__(self, app, stripe_service: StripeService):
        self._stripe_service = stripe_service
        self._user_creation_service: UserCreationService | None = None
        self._find_user_service: FindUserService | None = None
        self._user_update_service: UserStatusService | None = None
        
        super().__init__(app)
        
    # --- Properties ---
    @property
    def stripe_service(self) -> StripeService:
        return self._stripe_service
    
    @property
    def find_user_service(self) -> FindUserService:
        return self._find_user_service
    
    @property
    def user_creation_service(self) -> UserCreationService:
        return self._user_creation_service
    
    @property
    def user_status_service(self) -> UserStatusService:
        return self._user_update_service
    
    # --- Service Methods ---
    def create_user_service(self) -> UserCreationService:
        """Creates and returns a UserCreationService instance."""
        return UserCreationService(
            stripe_service=self._stripe_service,
            find_user_service=self._find_user_service,
            user_status_service=self._user_update_service
        )
        
    def create_user_status_service(self) -> UserStatusService:
        """Creates and returns a UserStatusService instance."""
        return UserStatusService()
    
    def create_find_user_service(self) -> FindUserService:
        """Creates and returns a FindUserService instance."""
        return FindUserService()
    
    def create_service(self):
        """Creates and returns the UserService instance."""
        self._find_user_service = self.create_find_user_service()
        self._user_update_service = self.create_user_status_service()
        self._user_creation_service = self.create_user_service()