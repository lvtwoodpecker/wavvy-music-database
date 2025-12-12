from app.services import service
from app.services.stripe.checkout import StripeCheckoutService
from app.services.stripe.create_stripe_account import StripeAccountService

class StripeService(service.Service):
    """Service for managing Stripe-related operations."""
    
    def __init__(self, app):
        super().__init__(app)
        self.create_service()

    def create_service(self):
        self._checkout_service = self._create_stripe_checkout_service()
        self._stripe_account_service = self._create_stripe_account_service()

    # -------- Properties --------

    @property
    def checkout_service(self) -> StripeCheckoutService:
        return self._checkout_service

    @property
    def stripe_account_service(self) -> StripeAccountService:
        return self._stripe_account_service

    # -------- Factory Methods --------

    def _create_stripe_checkout_service(self) -> StripeCheckoutService:
        return StripeCheckoutService(
            stripe_api_key=self.settings.STRIPE_API_KEY,
            front_end_url=self.settings.BACKEND_URL  # should be FRONTEND_URL if you have it
        )

    def _create_stripe_account_service(self) -> StripeAccountService:
        return StripeAccountService(
            stripe_api_key=self.settings.STRIPE_API_KEY,
            db_session_factory=self.db_session_factory
        )
