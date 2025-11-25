import stripe 
from app.config import settings

if not settings.STRIPE_API_KEY:
    raise ValueError("STRIPE_API_KEY is not set in environment variables.")

stripe.api_key = settings.STRIPE_API_KEY
SUCCESS_URL = f"{settings.FRONTEND_URL}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
CANCEL_URL = f"{settings.FRONTEND_URL}/payment-cancelled"

def create_checkout_session(
    user_id: str, 
    amount_cents: int, 
    payment_for: str, 
    currency: str = "usd") -> str:
    
    """
    Creates a Stripe Checkout Session in TEST MODE and returns the redirect URL.
    """
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Wavvy - {payment_for}",
                    },
                    "unit_amount": amount_cents,  # in cents
                },
                "quantity": 1,
            }
        ],
        success_url=f"{settings.FRONTEND_URL}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_URL}/payment-cancelled",
        metadata={
            "userId": user_id,
        },
    )
    return {"checkout_url": session.url}
