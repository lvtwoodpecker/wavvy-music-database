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
        user_service = app.services.user_service
        
        # ---- Stripe Checkout Session Creation ----
        @bp.route('/create-checkout-session', methods=['POST'])
        @login_required
        def create_session():
            """ Creates a Stripe Checkout Session and returns the session URL.
            
            Headers:
                Authorization: Bearer <token>
            
            Expects JSON body with:
            {
                "amount": integer,            # Amount in cents
                "currency": "string",         # Currency code, e.g. "usd" (optional, defaults to "usd")
                "payment_for": "string"       # Description of what the payment is for
            }
            Returns:
            {
                "checkout_url": "string",     # URL to redirect the user to Stripe Checkout
                "session_id": "string"        # Session ID for tracking
            }
            """
            
            data = request.json
            
            if settings.PAYMENTS_PROVIDER != "stripe":
                return jsonify(error="Payments provider not supported"), 400
            
            # Get user from authenticated token
            user_id = request.current_user["user_id"]
            
            # Get payment details from request
            amount = data.get('amount') if data.get('amount') is not None else data.get('amount_cents')
            currency = data.get('currency', 'usd')
            payment_for = data.get('payment_for', 'general')
            
            if amount is None:
                return jsonify({"error": "Amount is required"}), 400
            
            try:
                payment_intent = stripe_service.checkout_service.create_checkout_session(
                    user_id=user_id,
                    amount_cents=amount,
                    currency=currency,
                    payment_for=payment_for,
                    require_connected_account=True
                )
                return jsonify(payment_intent), 200
            except ValueError as e:
                # Handle user not having connected Stripe account
                error_code = str(e)
                if error_code == "STRIPE_NOT_CONNECTED":
                    return jsonify({
                        "error": "User must connect a Stripe account before making payments. Please connect your account in Settings.",
                        "error_code": "STRIPE_NOT_CONNECTED"
                    }), 400
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                print(f"Error creating checkout session: {e}")
                return jsonify({"error": "Failed to create checkout session"}), 500

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
                user = user_service.find_user_service.get_user_by_id(user_id)
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

        @bp.route('/subscription/activate', methods=['POST'])
        @login_required
        def activate_subscription():
            """Create a subscription history entry for the user and return status."""
            from datetime import datetime, timedelta
            from app.models.SubscriptionHistory import SubscriptionHistory
            from app.db.sqlalchemy_engine import SessionLocal

            try:
                data = request.json or {}
                user_id = request.current_user["user_id"]
                plan_id = data.get("plan_id")
                plan_name = data.get("plan_name", "Premium Monthly")

                # Monthly plan: expire in 30 days from now
                started_at = datetime.utcnow()
                expires_at = started_at + timedelta(days=30)

                db = SessionLocal()
                # Optional: mark previous active subscriptions as canceled
                db.query(SubscriptionHistory).filter(
                    SubscriptionHistory.user_id == user_id,
                    SubscriptionHistory.status == "active"
                ).update({"status": "canceled", "canceled_at": started_at})

                sub = SubscriptionHistory(
                    user_id=user_id,
                    plan_id=plan_id,
                    plan_name=plan_name,
                    status="active",
                    started_at=started_at,
                    expires_at=expires_at,
                )
                db.add(sub)
                db.commit()
                db.refresh(sub)
                return jsonify({"subscription": sub.to_dict()}), 200
            except Exception as e:
                print(f"Error activating subscription: {e}")
                return jsonify({"error": "Failed to activate subscription"}), 500
            finally:
                try:
                    db.close()
                except Exception:
                    pass

        @bp.route('/subscription/cancel', methods=['POST'])
        @login_required
        def cancel_subscription():
            from datetime import datetime
            from app.models.SubscriptionHistory import SubscriptionHistory
            from app.db.sqlalchemy_engine import SessionLocal

            try:
                user_id = request.current_user["user_id"]
                db = SessionLocal()
                now = datetime.utcnow()
                active = db.query(SubscriptionHistory).filter(
                    SubscriptionHistory.user_id == user_id,
                    SubscriptionHistory.status == "active"
                ).order_by(SubscriptionHistory.started_at.desc()).first()

                if not active:
                    return jsonify({"error": "No active subscription"}), 404

                active.status = "canceled"
                active.canceled_at = now
                db.commit()
                db.refresh(active)
                return jsonify({"subscription": active.to_dict()}), 200
            except Exception as e:
                print(f"Error canceling subscription: {e}")
                return jsonify({"error": "Failed to cancel subscription"}), 500
            finally:
                try:
                    db.close()
                except Exception:
                    pass

        @bp.route('/subscription/status', methods=['GET'])
        @login_required
        def subscription_status():
            from datetime import datetime
            from app.models.SubscriptionHistory import SubscriptionHistory
            from app.db.sqlalchemy_engine import SessionLocal

            try:
                user_id = request.current_user["user_id"]
                db = SessionLocal()
                # Prefer the most recent ACTIVE subscription; otherwise, fall back to the latest record
                active_sub = db.query(SubscriptionHistory).filter(
                    SubscriptionHistory.user_id == user_id,
                    SubscriptionHistory.status == "active"
                ).order_by(SubscriptionHistory.started_at.desc()).first()

                sub = active_sub or db.query(SubscriptionHistory).filter(
                    SubscriptionHistory.user_id == user_id
                ).order_by(SubscriptionHistory.started_at.desc()).first()

                if not sub:
                    return jsonify({"subscription": None}), 200

                # If expired, update status
                now = datetime.utcnow()
                if sub.status == "active" and sub.expires_at and sub.expires_at < now:
                    sub.status = "expired"
                    db.commit()
                    db.refresh(sub)

                return jsonify({"subscription": sub.to_dict()}), 200
            except Exception as e:
                print(f"Error fetching subscription status: {e}")
                return jsonify({"error": "Failed to fetch subscription status"}), 500
            finally:
                try:
                    db.close()
                except Exception:
                    pass

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