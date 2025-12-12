from flask import Flask, Blueprint, request, jsonify
import app.api.base_routes as base_routes
from app.services.stripe.stripe_service import StripeService
from app.utils.auth import login_required
import stripe

class StripeRoutes(base_routes.BaseRoutes):

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

        # ---- Stripe Account Connection ----
        @bp.route('/connect', methods=['POST'])
        @login_required
        def connect_stripe_account():
            """
            Creates or retrieves a Stripe Customer for the authenticated user.
            
            Headers:
                Authorization: Bearer <token>
            
            Returns:
            {
                "stripe_customer_id": "string",
                "status": "created" | "existing",
                "message": "string"
            }
            """
            try:
                # Get user info from token
                user_id = request.current_user["user_id"]
                email = request.current_user["email"]
                
                # Get user from database to get full name
                user = app.services.user_service.find_user_service.get_user_by_id(user_id)
                if not user:
                    return jsonify({"error": "User not found"}), 404
                
                full_name = f"{user.first_name} {user.last_name}"
                
                # Create or get Stripe customer
                result = stripe_service.stripe_account_service.create_or_get_stripe_customer(
                    user_id=user_id,
                    email=email,
                    name=full_name
                )
                
                message = "Stripe account connected successfully" if result["status"] == "created" else "Stripe account already connected"
                
                return jsonify({
                    "stripe_customer_id": result["stripe_customer_id"],
                    "status": result["status"],
                    "message": message
                }), 200
                
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                print(f"Error connecting Stripe account: {e}")
                return jsonify({"error": "Failed to connect Stripe account"}), 500

        @bp.route('/status', methods=['GET'])
        @login_required
        def get_stripe_status():
            """
            Gets the Stripe account status for the authenticated user.
            
            Headers:
                Authorization: Bearer <token>
            
            Returns:
            {
                "connected": boolean,
                "stripe_customer_id": "string" | null,
                "created_at": "string" | null
            }
            """
            try:
                user_id = request.current_user["user_id"]
                
                # Check if user has a Stripe account
                stripe_account = stripe_service.stripe_account_service.get_stripe_account_by_user_id(user_id)
                
                if stripe_account:
                    return jsonify({
                        "connected": True,
                        "stripe_customer_id": stripe_account.stripe_customer_id,
                        "created_at": stripe_account.created_at.isoformat()
                    }), 200
                else:
                    return jsonify({
                        "connected": False,
                        "stripe_customer_id": None,
                        "created_at": None
                    }), 200
                    
            except Exception as e:
                print(f"Error getting Stripe status: {e}")
                return jsonify({"error": "Failed to get Stripe status"}), 500

        @bp.route('/webhook', methods=['POST'])
        def stripe_webhook():
            """
            Handles Stripe webhook events.
            
            Listens for events like:
            - customer.updated
            - customer.deleted
            """
            payload = request.get_data()
            sig_header = request.headers.get('Stripe-Signature')
            webhook_secret = settings.STRIPE_WEBHOOK_SECRET
            
            if not webhook_secret:
                print("[Stripe Webhook] Warning: STRIPE_WEBHOOK_SECRET not configured")
                return jsonify({"error": "Webhook secret not configured"}), 500
            
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, webhook_secret
                )
            except ValueError as e:
                print(f"[Stripe Webhook] Invalid payload: {e}")
                return jsonify({"error": "Invalid payload"}), 400
            except stripe.error.SignatureVerificationError as e:
                print(f"[Stripe Webhook] Invalid signature: {e}")
                return jsonify({"error": "Invalid signature"}), 400
            
            # Handle the event
            event_type = event['type']
            print(f"[Stripe Webhook] Received event: {event_type}")
            
            if event_type == 'customer.updated':
                customer = event['data']['object']
                print(f"[Stripe Webhook] Customer updated: {customer['id']}")
                # Could update local database if needed
                
            elif event_type == 'customer.deleted':
                customer = event['data']['object']
                print(f"[Stripe Webhook] Customer deleted: {customer['id']}")
                # Could mark account as inactive in database
                
            else:
                print(f"[Stripe Webhook] Unhandled event type: {event_type}")
            
            return jsonify({"status": "success"}), 200

        return bp