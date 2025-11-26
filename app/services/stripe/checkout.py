import stripe 

class StripeCheckoutService:
    def __init__(self, front_end_url: str):
        self.front_end_url = front_end_url
        
    def create_checkout_session(
        self,
        user_id: str, 
        amount_cents: int, 
        payment_for: str, 
        currency: str = "usd",
        quantity: int = 1
        ) -> str:
        
        """
        Creates a Stripe Checkout Session for a payment.
        Args:
            user_id (str): The ID of the user making the payment.
            amount_cents (int): The amount to be charged in cents.
            payment_for (str): Description of what the payment is for.
            currency (str): Currency code (default is 'usd').
            quantity (int): Quantity of the item being purchased (default is 1).
        """
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": f"Wavvy - {payment_for}",
                        },
                        "unit_amount": amount_cents,  # in cents
                    },
                    "quantity": quantity,
                }
            ],
            success_url=f"{self.front_end_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{self.front_end_url}/payment-cancelled",
            metadata={
                "userId": user_id,
            },
        )
        return {"checkout_url": session.url}
