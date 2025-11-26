from app.services import service
from app.services.stripe.checkout import StripeCheckoutService
from app.services.stripe.create_stripe_account import StripeAccountService

class StripeService(service.Service):
    """Service for managing Stripe-related operations."""
    def __init__(self, app):
        # supper defines settings and db properties
        super().__init__(app)
        self.create_service()
        
    def create_service(self):
        """Creates and returns the StripeService instance."""
        self._checkout_service = self._create_stripe_checkout_service()
        self._stripe_account_service = self._create_stripe_account_service()
        
    # --- Properties ---
    @property
    def checkout_service(self) -> StripeCheckoutService:
        return self._checkout_service
    
    @property
    def stripe_account_service(self) -> StripeAccountService:
        return self._stripe_account_service
        
    # --- Private Methods ---
    def _create_stripe_checkout_service(self) -> StripeCheckoutService:
        front_end_url = self.settings.FRONTEND_URL
        return StripeCheckoutService(front_end_url=front_end_url)
    
    def _create_stripe_account_service(self) -> StripeAccountService:
        return StripeAccountService(stripe_api_key=self.settings.STRIPE_API_KEY)
    
    