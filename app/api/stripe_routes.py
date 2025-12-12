from flask import Flask, Blueprint, request, jsonify
from app.api.routes import Routes
from app.services.stripe.stripe_service import StripeService

class StripeRoutes(Routes):

    def create_blueprint(self, app) -> Blueprint:
        bp = Blueprint('stripe', __name__)
        settings = app.settings
        stripe_service: StripeService = app.services.stripe_service
        
        # ---- Stripe Checkout Session Creation ----
        @bp.route('/create-checkout-session', methods=['POST'])
        def create_session():
            """ Creates a Stripe Checkout Session and returns the session URL.
            
            Expects JSON body with:
            {
                "user_id": "string",          # ID of the user making the payment
                "amount": integer,            # Amount in cents
                "currency": "string",         # Currency code, e.g. "usd"
                "payment_for": "string"       # Description of what the payment is for
            }
            Returns:
            {
                "url": "string"               # URL to redirect the user to Stripe Checkout
            }
            """
            
            data = request.json
            
            if settings.PAYMENTS_PROVIDER != "stripe":
                return jsonify(error="Payments provider not supported"), 400
            
            # for now, we add fallback defaults for testing
            user_id = data.get('user_id', 'anonymous')
            amount = data.get('amount', 0)
            currency = data.get('currency', 'usd')
            payment_for = data.get('payment_for', 'general')  
            
            try:

                payment_intent = stripe_service.checkout_service.create_checkout_session(
                    user_id=user_id,
                    amount_cents=amount,
                    currency=currency,
                    payment_for=payment_for
                )
                return jsonify(payment_intent), 200
            except Exception as e:
                print(f"Error creating checkout session: {e}")
                return jsonify({"error": f"Failed to create checkout session: {e}"}), 500

        return bp