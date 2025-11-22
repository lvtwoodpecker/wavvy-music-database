#  User API routes for managing user-related endpoints
from flask import Blueprint, request, jsonify
from app.services.stripe_create_user_service import create_advertiser, create_listener
from app.services.stripe_create_user_service import get_user_by_email

# create the blueprint for user routes
user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/create-listener', methods=['POST'])
def api_create_listener():
    """API endpoint to create a new listener user."""
    data = request.json
    
    try:
        user = create_listener(
            email=data['email'],
            username=data['user_name'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            password_hash=data['password_hash'],
            country=data['country']
        )
        return jsonify(user), 201
    except Exception as e:
        print("[Users] Error creating listener:", e)
        return jsonify({"error": "Failed to create listener"}), 500
    
    
@user_bp.route('/create-advertiser', methods=['POST'])
def api_create_advertiser():
    """API endpoint to create a new advertiser user."""
    data = request.json
    
    try:
        user = create_advertiser(
            email=data['email'],
            username=data['user_name'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            password_hash=data['password_hash'],
            country=data['country'],
            company_name=data['company_name']
        )
        return jsonify(user), 201
    except Exception as e:
        print("[Users] Error creating advertiser:", e)
        return jsonify({"error": "Failed to create advertiser"}), 500
    