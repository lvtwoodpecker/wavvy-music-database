# app/services/user/user_service.py

from typing import Optional, Callable

from app.services import service
from app.services.pricing.subscription_pricing_service import SubscriptionPricingService

from sqlalchemy.orm import Session

SessionFactory = Callable[[], Session]


class PricingService(service.Service):
    """Service for managing User-related operations.
    
    This service aggregates sub-services for user creation, status management, and user lookups.
    It depends on StripeService for handling Stripe-related operations during user creation.
    """

    def __init__(self, app):
        super().__init__(app)
        self.create_service()

    def create_service(self):
        self._subscription_pricing_service = self._create_subscription_pricing_service()
        
    # --- Properties ---
    @property
    def subscription_pricing_service(self) -> SubscriptionPricingService:
        if self._subscription_pricing_service is None:
            self._subscription_pricing_service = self._create_subscription_pricing_service()
        return self._subscription_pricing_service
    
    def _create_subscription_pricing_service(self) -> SubscriptionPricingService:
        return SubscriptionPricingService(
            db_session_factory=self._db_session_factory
        )