#  User API routes for managing user-related endpoints
from flask import Blueprint, request, jsonify
from app.api.routes import Routes

class UserRoutes(Routes):
    
    def create_blueprint(self, app) -> Blueprint:
        bp = Blueprint('users', __name__)
        
        # --- Create Listener User -----
        @bp.route('/create-listener', methods=['POST'])
        def api_create_listener():
            """API endpoint to create a new listener user."""
            data = request.json
            
            try:
                user = self.services.user_service.user_creation_service.create_listener(
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
            
            
        # --- Create Advertiser User -----
        @bp.route('/create-advertiser', methods=['POST'])
        def api_create_advertiser():
            """API endpoint to create a new advertiser user."""
            data = request.json
            
            try:
                user = self.services.user_service.user_creation_service.create_advertiser(
                    email=data['email'],
                    username=data['user_name'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    password_hash=data['password_hash'],
                    company_name=data['company_name'],
                    country=data['country']
                )
                return jsonify(user), 201
            except Exception as e:
                print("[Users] Error creating advertiser:", e)
                return jsonify({"error": "Failed to create advertiser"}), 500
            
        
        return bp
    

    