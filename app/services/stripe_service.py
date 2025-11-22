import stripe 
from app.config import settings

stripe.api_key = settings.STRIPE_API_KEY
success_url = "http://localhost:3000/payment-success"
cancel_url = "http://localhost:3000/payment-cancel"

def create_checkout_session(amount_cents: int, currency: str, payment_for: str):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': f'Wavvy - {payment_for}',
                    },
                    'unit_amount': amount_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session.url
    except Exception as e:
        print(f"Error creating checkout session: {e}")
        return None