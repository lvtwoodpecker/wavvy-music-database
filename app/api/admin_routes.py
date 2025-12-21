# app/api/admin_routes.py
from flask import Blueprint, request, jsonify
from app.utils.auth import admin_required
import app.api.base_routes as base_routes


class AdminRoutes(base_routes.BaseRoutes):
    
    def create_blueprint(self, app) -> Blueprint:
        admin_bp = Blueprint("admin", __name__)
        admin_service = app.services.admin_service

        @admin_bp.get("/pricing-trends")
        @admin_required
        def get_pricing_trends():
            """
            GET /api/admin/pricing-trends
            Returns pricing trends for our subscription plans
            """
            try:
                pricing_data = admin_service.get_pricing_trends()
                return jsonify({"pricing_trends": pricing_data}), 200
            except Exception as e:
                print(f"[Admin] Error fetching pricing trends: {e}")
                return jsonify({"error": "Failed to fetch pricing trends"}), 500

        @admin_bp.get("/competitor-data")
        @admin_required
        def get_competitor_data():
            """
            GET /api/admin/competitor-data
            Returns competitor pricing and plan information
            """
            try:
                competitor_data = admin_service.get_competitor_data()
                return jsonify({"competitors": competitor_data}), 200
            except Exception as e:
                print(f"[Admin] Error fetching competitor data: {e}")
                return jsonify({"error": "Failed to fetch competitor data"}), 500

        @admin_bp.get("/music-analytics")
        @admin_required
        def get_music_analytics():
            """
            GET /api/admin/music-analytics
            Returns music analytics data
            """
            try:
                analytics = admin_service.get_music_analytics()
                return jsonify({"analytics": analytics}), 200
            except Exception as e:
                print(f"[Admin] Error fetching music analytics: {e}")
                return jsonify({"error": "Failed to fetch music analytics"}), 500

        @admin_bp.get("/ml-price-analysis")
        @admin_required
        def get_ml_price_analysis():
            """
            GET /api/admin/ml-price-analysis
            Returns ML-based price recommendations (simple analysis)
            """
            try:
                recommendations = admin_service.get_ml_price_analysis()
                return jsonify({"recommendations": recommendations}), 200
            except Exception as e:
                print(f"[Admin] Error generating ML price analysis: {e}")
                return jsonify({"error": "Failed to generate price analysis"}), 500

        @admin_bp.put("/update-price")
        @admin_required
        def update_price():
            """
            PUT /api/admin/update-price
            Body: {
                "plan_id": 1,
                "new_price": 9.99
            }
            """
            try:
                data = request.get_json() or {}
                plan_id = data.get("plan_id")
                new_price = data.get("new_price")
                
                if not plan_id or new_price is None:
                    return jsonify({"error": "plan_id and new_price are required"}), 400
                
                email = request.current_user.get('email')
                result = admin_service.update_subscription_price(plan_id, new_price, email)
                
                return jsonify({
                    "message": "Price updated successfully",
                    **result
                }), 200
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                print(f"[Admin] Error updating price: {e}")
                return jsonify({"error": "Failed to update price"}), 500

        @admin_bp.put("/update-user-status")
        @admin_required
        def update_user_status():
            """
            PUT /api/admin/update-user-status
            Body: {
                "user_id": 123,
                "status": "active" | "banned" | "inactive"
            }
            """
            try:
                data = request.get_json() or {}
                user_id = data.get("user_id")
                status = data.get("status")
                
                if not user_id or not status:
                    return jsonify({"error": "user_id and status are required"}), 400
                
                result = admin_service.update_user_status(user_id, status)
                
                return jsonify({
                    "message": "User status updated successfully",
                    **result
                }), 200
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                print(f"[Admin] Error updating user status: {e}")
                return jsonify({"error": "Failed to update user status"}), 500

        @admin_bp.put("/update-user-role")
        @admin_required
        def update_user_role():
            """
            PUT /api/admin/update-user-role
            Body: {
                "user_id": 123,
                "role": "user" | "admin"
            }
            """
            try:
                data = request.get_json() or {}
                user_id = data.get("user_id")
                role = data.get("role")
                
                if not user_id or not role:
                    return jsonify({"error": "user_id and role are required"}), 400
                
                result = admin_service.update_user_role(user_id, role)
                
                return jsonify({
                    "message": "User role updated successfully",
                    **result
                }), 200
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                print(f"[Admin] Error updating user role: {e}")
                return jsonify({"error": "Failed to update user role"}), 500

        @admin_bp.get("/users")
        @admin_required
        def get_users():
            """
            GET /api/admin/users?page=1&per_page=50
            Returns paginated list of users
            """
            try:
                page = int(request.args.get('page', 1))
                per_page = int(request.args.get('per_page', 50))
                
                result = admin_service.get_users(page, per_page)
                return jsonify(result), 200
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                print(f"[Admin] Error fetching users: {e}")
                return jsonify({"error": "Failed to fetch users"}), 500

        return admin_bp
