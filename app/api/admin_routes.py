# app/api/admin_routes.py
from flask import Blueprint, request, jsonify
from app.utils.auth import admin_required, login_required
import app.api.base_routes as base_routes

class AdminRoutes(base_routes.BaseRoutes):
    
    def verify_is_admin(self, user_info: dict) -> bool:
        """Verify if the user has admin privileges."""
        print(f"[AdminRoutes] Verifying admin status for user: {user_info}")
        return user_info.get("role") == "admin"
    
    def create_blueprint(self, app) -> Blueprint:
        admin_bp = Blueprint("admin", __name__)
        admin_service = app.services.admin_service

        @admin_bp.get("/pricing-trends")
        @login_required
        def get_pricing_trends():
            """
            GET /api/admin/pricing-trends

            Query params:
            - include_series: bool (default true)        -> include time-series points
            - granularity: "raw" | "monthly" (default monthly)
            - include_rollups: bool (default true)      -> include portfolio KPIs

            Returns:
            {
                "pricing_trends": {
                "plans": [...],
                "rollups": {...},
                "as_of": "ISO8601"
                }
            }
            """
            if not self.verify_is_admin(request.current_user):
                return jsonify({"error": "Admin privileges required"}), 403

            def _bool_param(name: str, default: bool) -> bool:
                val = request.args.get(name)
                if val is None:
                    return default
                return val.strip().lower() in ("1", "true", "t", "yes", "y", "on")

            include_series = _bool_param("include_series", True)
            include_rollups = _bool_param("include_rollups", True)
            granularity = (request.args.get("granularity") or "monthly").strip().lower()
            if granularity not in ("raw", "monthly"):
                granularity = "monthly"

            try:
                # IMPORTANT: update your service signature to accept these knobs
                pricing_payload = admin_service.get_pricing_trends(
                    include_series=include_series,
                    granularity=granularity,
                    include_rollups=include_rollups,
                )

                return jsonify({"pricing_trends": pricing_payload}), 200

            except Exception as e:
                # Don't leak internals to client; log enough to debug
                print(
                    "[Admin] Error fetching pricing trends",
                    {
                        "error": str(e),
                        "admin_user_id": getattr(request.current_user, "id", None),
                        "include_series": include_series,
                        "granularity": granularity,
                        "include_rollups": include_rollups,
                    }
                )
                return jsonify({"error": "Failed to fetch pricing trends"}), 500

        @admin_bp.get("/competitor-data")
        @login_required
        def get_competitor_data():
            """
            GET /api/admin/competitor-data
            Returns competitor pricing and plan information
            """
            if not self.verify_is_admin(request.current_user):
                return jsonify({"error": "Admin privileges required"}), 403
            
            try:
                competitor_data = admin_service.get_competitor_data()
                return jsonify({"competitors": competitor_data}), 200
            except Exception as e:
                print(f"[Admin] Error fetching competitor data: {e}")
                return jsonify({"error": "Failed to fetch competitor data"}), 500

        @admin_bp.get("/music-analytics")
        @login_required
        def get_music_analytics():
            """
            GET /api/admin/music-analytics
            Returns music analytics data
            """
            if not self.verify_is_admin(request.current_user):
                return jsonify({"error": "Admin privileges required"}), 403
            
            try:
                analytics = admin_service.get_music_analytics()
                return jsonify({"analytics": analytics}), 200
            except Exception as e:
                print(f"[Admin] Error fetching music analytics: {e}")
                return jsonify({"error": "Failed to fetch music analytics"}), 500

        @admin_bp.get("/ml-price-analysis")
        @login_required
        def get_ml_price_analysis():
            """
            GET /api/admin/ml-price-analysis
            Returns ML-based price recommendations (simple analysis)
            """
            
            if not self.verify_is_admin(request.current_user):
                return jsonify({"error": "Admin privileges required"}), 403
            
            try:
                recommendations = admin_service.get_ml_price_analysis()
                return jsonify({"recommendations": recommendations}), 200
            except Exception as e:
                print(f"[Admin] Error generating ML price analysis: {e}")
                return jsonify({"error": "Failed to generate price analysis"}), 500

        @admin_bp.put("/update-price")
        @login_required
        def update_price():
            """
            PUT /api/admin/update-price
            Body: {
                "plan_id": 1,
                "new_price": 9.99
            }
            """
            
            if not self.verify_is_admin(request.current_user):
                return jsonify({"error": "Admin privileges required"}), 403
            
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
        @login_required
        def update_user_status():
            """
            PUT /api/admin/update-user-status
            Body: {
                "user_id": 123,
                "status": "active" | "banned" | "inactive"
            }
            """
            if not self.verify_is_admin(request.current_user):
                return jsonify({"error": "Admin privileges required"}), 403
            
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
        @login_required
        def update_user_role():
            """
            PUT /api/admin/update-user-role
            Body: {
                "user_id": 123,
                "role": "user" | "admin"
            }
            """
            if not self.verify_is_admin(request.current_user):
                return jsonify({"error": "Admin privileges required"}), 403
            
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
        @login_required
        def get_users():
            """
            GET /api/admin/users?page=1&per_page=50
            Returns paginated list of users
            """
            if not self.verify_is_admin(request.current_user):
                return jsonify({"error": "Admin privileges required"}), 403
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
