import stripe
from typing import Optional, Callable
from sqlalchemy.orm import Session

SessionFactory = Callable[[], Session]

class StripeCheckoutService:
    def __init__(self, stripe_api_key: str, front_end_url: str, db_session_factory: Optional[SessionFactory] = None):
        stripe.api_key = stripe_api_key
        self.front_end_url = front_end_url
        self._db_session_factory = db_session_factory

    def _get_session(self) -> Session:
        if not self._db_session_factory:
            raise ValueError("Database session factory not configured")
        return self._db_session_factory()

    def _get_stripe_customer_id(self, user_id: int) -> Optional[str]:
        """Get the Stripe customer ID for a user if they have connected their account."""
        if not self._db_session_factory:
            return None
            
        from app.models.StripeAccount import StripeAccount
        db = self._get_session()
        try:
            account = db.query(StripeAccount).filter(StripeAccount.user_id == user_id).first()
            return account.stripe_customer_id if account else None
        except Exception as e:
            print(f"[Stripe Checkout Service] Error fetching stripe customer: {e}")
            return None
        finally:
            db.close()

    def create_checkout_session(
        self,
        user_id: int,
        amount_cents: int,
        payment_for: str,
        currency: str = "usd",
        quantity: int = 1,
        require_connected_account: bool = True,
    ) -> dict:
        """
        Creates a Stripe Checkout Session for a one-time payment.

        Args:
            user_id (int): ID of the Wavvy user making the payment.
            amount_cents (int): Amount in cents.
            payment_for (str): Description of the purchase.
            currency (str): Currency code.
            quantity (int): Quantity being purchased.
            require_connected_account (bool): If True, requires user to have a connected Stripe account.

        Returns:
            dict: {"checkout_url": str, "session_id": str}
            
        Raises:
            ValueError: If user doesn't have a connected Stripe account and require_connected_account is True.
        """
        
        # Check if user has connected Stripe account
        stripe_customer_id = self._get_stripe_customer_id(user_id)
        
        if require_connected_account and not stripe_customer_id:
            raise ValueError("STRIPE_NOT_CONNECTED")

        # Prepare session parameters
        session_params = {
            "mode": "payment",
            "line_items": [
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {"name": f"Wavvy – {payment_for}"},
                        "unit_amount": amount_cents,
                    },
                    "quantity": quantity,
                }
            ],
            "metadata": {
                "userId": str(user_id),
                "payment_for": payment_for,
            },
            "success_url": f"{self.front_end_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{self.front_end_url}/payment-cancelled",
        }
        
        # Add customer if connected
        if stripe_customer_id:
            session_params["customer"] = stripe_customer_id

        session = stripe.checkout.Session.create(**session_params)

        return {
            "checkout_url": session.url,
            "session_id": session.id,
        }
