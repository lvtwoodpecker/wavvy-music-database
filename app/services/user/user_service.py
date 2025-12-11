# app/services/user/user_service.py

from typing import Optional, Callable

from app.services import service
from app.services.stripe.stripe_service import StripeService
from app.services.user.create_user_account import UserCreationService
from app.services.user.account_status import UserStatusService
from app.services.user.find_user import FindUserService

from sqlalchemy.orm import Session

SessionFactory = Callable[[], Session]


class UserService(service.Service):
    """Service for managing User-related operations."""

    def __init__(self, app, stripe_service: StripeService):
        super().__init__(app)

        # Shared dependencies
        self._stripe_service = stripe_service
        self._db_session_factory: SessionFactory = app.db_session_factory
        # If you ever need Supabase in sub-services:
        # self._supabase = app.supabase

        # Sub-services (lazy-init)
        self._user_creation_service: Optional[UserCreationService] = None
        self._find_user_service: Optional[FindUserService] = None
        self._user_update_service: Optional[UserStatusService] = None

    # --- Properties ---
    @property
    def stripe_service(self) -> StripeService:
        return self._stripe_service

    @property
    def find_user_service(self) -> FindUserService:
        if self._find_user_service is None:
            self._find_user_service = self.create_find_user_service()
        return self._find_user_service

    @property
    def user_creation_service(self) -> UserCreationService:
        if self._user_creation_service is None:
            self._user_creation_service = self.create_user_service()
        return self._user_creation_service

    @property
    def user_status_service(self) -> UserStatusService:
        if self._user_update_service is None:
            self._user_update_service = self.create_user_status_service()
        return self._user_update_service

    # --- Factory Methods for Sub-services ---

    def create_user_service(self) -> UserCreationService:
        """
        Creates and returns a UserCreationService instance.

        Injects:
        - db_session_factory for ORM
        - stripe_service
        - find_user_service
        - user_status_service
        """
        return UserCreationService(
            db_session_factory=self._db_session_factory,
            stripe_service=self._stripe_service,
            find_user_service=self.find_user_service,
            user_status_service=self.user_status_service,
        )

    def create_user_status_service(self) -> UserStatusService:
        """
        Creates and returns a UserStatusService instance.
        Injects db_session_factory so it can update user rows using ORM.
        """
        return UserStatusService(
            db_session_factory=self._db_session_factory,
        )

    def create_find_user_service(self) -> FindUserService:
        """
        Creates and returns a FindUserService instance.
        Injects db_session_factory so it can query users with ORM.
        """
        return FindUserService(
            db_session_factory=self._db_session_factory,
        )

    def create_service(self):
        """
        Kept for backwards compatibility if something calls it.
        Eagerly instantiates all sub-services.
        """
        _ = self.find_user_service
        _ = self.user_status_service
        _ = self.user_creation_service
