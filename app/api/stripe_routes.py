from flask import Flask, Blueprint, request, jsonify
from app.services.stripe_service import create_checkout_session

payment_bp = Blueprint('payment_bp', __name__)

@payment_bp.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    data = request.json
    try:
        amount = data.get('amount', 0)
        currency = data.get('currency', 'usd')
        payment_for = data.get('payment_for', 'general')
        payment_intent = create_checkout_session(
            amount_cents = amount, 
            currency=currency, 
            payment_for=payment_for
        )
        return jsonify(payment_intent), 200
    except Exception as e:
        return jsonify(error=str(e)), 400