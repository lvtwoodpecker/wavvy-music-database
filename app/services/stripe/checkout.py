import stripe

class StripeCheckoutService:
    def __init__(self, stripe_api_key: str, front_end_url: str):
        stripe.api_key = stripe_api_key
        self.front_end_url = front_end_url

    def create_checkout_session(
        self,
        user_id: int,
        amount_cents: int,
        payment_for: str,
        currency: str = "usd",
        quantity: int = 1,
    ) -> dict:
        """
        Creates a Stripe Checkout Session for a one-time payment.

        Args:
            user_id (int): ID of the Wavvy user making the payment.
            amount_cents (int): Amount in cents.
            payment_for (str): Description of the purchase.
            currency (str): Currency code.
            quantity (int): Quantity being purchased.

        Returns:
            dict: {"checkout_url": str, "session_id": str}
        """

        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {"name": f"Wavvy – {payment_for}"},
                        "unit_amount": amount_cents,
                    },
                    "quantity": quantity,
                }
            ],
            metadata={
                "userId": str(user_id),
                "payment_for": payment_for,
            },
            success_url=f"{self.front_end_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{self.front_end_url}/payment-cancelled",
        )

        return {
            "checkout_url": session.url,
            "session_id": session.id,
        }
