# app/api/auth_routes.py

from flask import Blueprint, request, jsonify
from app.services.stripe_create_user_service import get_user_by_email

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/login")
def login():
    """
    POST /api/auth/login
    Body: { "email": "user@gmail.com" }
    """
    data = request.get_json() or {}
    email = data.get("email")

    if not email:
        return jsonify({"error": "email is required"}), 400

    try:
        user = get_user_by_email(email)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # In a real app you’d issue a JWT or session here.
        # For the project, just return the user record.
        
        # TODO: return a token instead
        return jsonify({"user": user}), 200
    except Exception as e:
        print("[Auth] Error logging in:", e)
        return jsonify({"error": "Failed to login"}), 500
