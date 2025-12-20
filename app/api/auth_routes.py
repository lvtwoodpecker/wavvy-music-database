# app/api/auth_routes.py
from flask import Blueprint, request, jsonify
import re
from app.utils.auth import (
    hash_password, 
    verify_password, 
    generate_token, 
    login_required
)
from app.services.user.user_service import UserService
import app.api.base_routes as base_routes
from datetime import datetime

class AuthRoutes(base_routes.BaseRoutes):
    
    def create_blueprint(self, app) -> Blueprint:
        auth_bp = Blueprint("auth", __name__)
        user_service : UserService = app.services.user_service

        @auth_bp.post("/signup")
        def signup():
            """
            POST /api/auth/signup
            Body: {
                "email": "user@example.com",
                "password": "password123",
                "username": "username",
                "first_name": "John",
                "last_name": "Doe",
                "country": "US"
            }
            """
            data = request.get_json() or {}
            
            # Extract and validate required fields
            email = data.get("email", "").strip()
            password = data.get("password", "")
            username = data.get("username", "").strip()
            first_name = data.get("first_name", "").strip()
            last_name = data.get("last_name", "").strip()
            country = data.get("country", "US").strip().upper()
            
            # Validation
            errors = []
            
            if not email:
                errors.append("Email is required")
            elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                errors.append("Invalid email format")
            
            if not password:
                errors.append("Password is required")
            elif len(password) < 8:
                errors.append("Password must be at least 8 characters")
            
            if not username:
                errors.append("Username is required")
            
            if not first_name:
                errors.append("First name is required")
            
            if not last_name:
                errors.append("Last name is required")
            
            if not re.match(r'^[A-Z]{2}$', country):
                errors.append("Country must be a valid 2-letter code (e.g., US, CA)")
            
            if errors:
                return jsonify({"error": ", ".join(errors)}), 400
            
            try:
                # Check if user already exists
                existing_user = user_service.find_user_service.get_user_by_email(email)
                if existing_user:
                    return jsonify({"error": "Email already exists"}), 400
                
                # Hash password
                password_hashed = hash_password(password)
                
                # Create listener user (default user type)
                user_response = user_service.user_creation_service.create_listener(
                    email=email,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    password_hash=password_hashed,
                    country=country
                )
                
                # Generate JWT token
                token = generate_token(user_response["user_id"], email)
                print("Generated token:", token)
                
                # Remove password_hash from response
                user_response.pop("password_hash", None)
                return jsonify({
                    "token": token,
                    "user": user_response
                }), 201
                
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                print("[Auth] Error during signup:", e)
                return jsonify({"error": "Failed to create account"}), 500


        @auth_bp.post("/login")
        def login():
            """
            POST /api/auth/login
            Body: { 
                "email": "user@example.com",
                "password": "password123"
            }
            """
            data = request.get_json() or {}
            email = data.get("email", "").strip()
            password = data.get("password", "")

            if not email or not password:
                return jsonify({"error": "Email and password are required"}), 400

            try:
                user = user_service.find_user_service.get_user_by_email(email)
                if not user:
                    return jsonify({"error": "Invalid credentials"}), 401
                
                # Verify password
                if not verify_password(password, user.password_hash):
                    return jsonify({"error": "Invalid credentials"}), 401
                
                # Generate JWT token
                token = generate_token(user.user_id, user.email)
                
                # Remove password_hash from response
                print("User logged in successfully:", user.role)
                user_response = user.to_dict()
                
                return jsonify({
                    "token": token,
                    "user": user_response
                }), 200
                
            except Exception as e:
                print("[Auth] Error logging in:", e)
                return jsonify({"error": "Failed to login"}), 500

        @auth_bp.post("/change-password")
        @login_required
        def change_password():
            """
            POST /api/auth/change-password
            Headers: Authorization: Bearer <token>
            Body: { "old_password": "...", "new_password": "..." }
            """
            data = request.get_json() or {}
            old_password = data.get("old_password", "")
            new_password = data.get("new_password", "")
            if not old_password or not new_password:
                return jsonify({"error": "old_password and new_password are required"}), 400
            user_id = request.current_user["user_id"]
            ok = user_service.password_reset_service.change_password(
                user_id=user_id,
                old_password=old_password,
                new_password_hash=hash_password(new_password),
                verify_fn=verify_password
            )
            if not ok:
                return jsonify({"error": "Invalid old password or user not found"}), 400
            return jsonify({"message": "Password updated"}), 200

        @auth_bp.post("/request-password-reset")
        def request_password_reset():
            """
            POST /api/auth/request-password-reset
            Body: { "email": "user@example.com" }
            Returns message and, in development, the token for convenience.
            """
            data = request.get_json() or {}
            email = data.get("email", "").strip()
            if not email:
                return jsonify({"error": "email is required"}), 400
            token = user_service.password_reset_service.request_reset(email)
            # Avoid user enumeration; always success message
            if token:
                print(f"[PasswordReset] token for {email}: {token}")
                return jsonify({"message": "Reset initiated", "token": token}), 200
            else:
                return jsonify({"message": "If the email exists, a reset was initiated"}), 200

        @auth_bp.post("/reset-password")
        def reset_password():
            """
            POST /api/auth/reset-password
            Body: { "token": "...", "new_password": "..." }
            """
            data = request.get_json() or {}
            token = data.get("token", "")
            new_password = data.get("new_password", "")
            if not token or not new_password:
                return jsonify({"error": "token and new_password are required"}), 400
            ok = user_service.password_reset_service.reset_with_token(
                token=token,
                new_password_hash=hash_password(new_password)
            )
            if not ok:
                return jsonify({"error": "Invalid or expired token"}), 400
            return jsonify({"message": "Password has been reset"}), 200
            
        @auth_bp.route("/signup-advertiser", methods=["POST"])
        @login_required
        def signup_advertiser():
            """
            POST /api/auth/signup-advertiser
            Headers: Authorization: Bearer <token>
            Body: {
                "company_name": "Company Inc."
            }
            """
            
            data = request.get_json() or {}
            company_name = data.get("company_name", "").strip()
            
            if not company_name:
                return jsonify({"error": "Company name is required"}), 400
            
            try:
                # current_user is set by @login_required decorator
                user_id = request.current_user["user_id"]
                email = request.current_user["email"]
                
                # Upgrade user to advertiser
                user = user_service.user_creation_service.create_advertiser(
                    user_id=user_id,
                    email=email,
                    company_name=company_name
                )
                
                # Remove password_hash from response
                user_response =  {
                    "email": user["email"],
                    "username": user["username"],
                    "role": user["role"],
                    "company_name": company_name
                }
            
                return jsonify({
                    "user": user_response
                }), 200
                
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                print("[Auth] Error upgrading to advertiser:", e)
                return jsonify({"error": "Failed to upgrade account"}), 500

        @auth_bp.get("/me")
        @login_required
        def get_current_user():
            """
            GET /api/auth/me
            Headers: Authorization: Bearer <token>
            
            Returns current user information based on JWT token
            """
            try:
                # current_user is set by @login_required decorator
                user_id = request.current_user["user_id"]
                email = request.current_user["email"]
                
                # Fetch full user data from database
                user = user_service.find_user_service.get_user_by_email(email)
                if not user:
                    return jsonify({"error": "User not found"}), 404
                
                # Remove password_hash from response
                user_response = user.to_dict()
                
                return jsonify({"user": user_response}), 200
                
            except Exception as e:
                print("[Auth] Error fetching current user:", e)
                return jsonify({"error": "Failed to fetch user"}), 500
            
        return auth_bp
