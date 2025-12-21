# app/api/admin_routes.py
from flask import Blueprint, request, jsonify
from app.utils.auth import admin_required
from app.models.User import UserRole
import app.api.base_routes as base_routes
from datetime import datetime, timedelta
from sqlalchemy import func, case, and_
from app.models.SubscriptionPlanPrice import SubscriptionPlanPrice
from app.models.SubscriptionPlan import SubscriptionPlan
from app.models.User import User
from app.models.Competitor import Competitor
from app.models.CompetitorSubscriptionPlan import CompetitorSubscriptionPlan
from app.models.CompetitorSubscriptionPriceSnapshot import CompetitorSubscriptionPriceSnapshot
from app.models.Track import Track
from app.models.PlayHistory import PlayHistory
from decimal import Decimal


class AdminRoutes(base_routes.BaseRoutes):
    
    def create_blueprint(self, app) -> Blueprint:
        admin_bp = Blueprint("admin", __name__)
        db_session_factory = app.db_session_factory

        @admin_bp.get("/pricing-trends")
        @admin_required
        def get_pricing_trends():
            """
            GET /api/admin/pricing-trends
            Returns pricing trends for our subscription plans
            """
            try:
                db = db_session_factory()
                
                # Get all subscription plans with their price history
                plans = db.query(SubscriptionPlan).all()
                
                pricing_data = []
                for plan in plans:
                    price_history = db.query(SubscriptionPlanPrice)\
                        .filter(SubscriptionPlanPrice.plan_id == plan.plan_id)\
                        .order_by(SubscriptionPlanPrice.effective_from.desc())\
                        .all()
                    
                    pricing_data.append({
                        "plan_id": plan.plan_id,
                        "plan_name": plan.name,
                        "current_price": float(plan.price_usd),
                        "feature_set": plan.feature_set,
                        "price_history": [
                            {
                                "price": float(ph.price),
                                "effective_from": ph.effective_from.isoformat() if ph.effective_from else None,
                                "changed_by": ph.changed_by_user_id
                            }
                            for ph in price_history
                        ]
                    })
                
                db.close()
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
                db = db_session_factory()
                
                competitors = db.query(Competitor).all()
                
                competitor_data = []
                for competitor in competitors:
                    plans = db.query(CompetitorSubscriptionPlan)\
                        .filter(CompetitorSubscriptionPlan.competitor_id == competitor.competitor_id)\
                        .all()
                    
                    plans_data = []
                    for plan in plans:
                        # Get latest price snapshot
                        latest_price = db.query(CompetitorSubscriptionPriceSnapshot)\
                            .filter(CompetitorSubscriptionPriceSnapshot.competitor_plan_id == plan.competitor_plan_id)\
                            .order_by(CompetitorSubscriptionPriceSnapshot.observed_at.desc())\
                            .first()
                        
                        plans_data.append({
                            "plan_id": plan.competitor_plan_id,
                            "plan_name": plan.plan_name,
                            "billing_period": plan.billing_period,
                            "is_student": plan.is_student,
                            "is_family": plan.is_family,
                            "max_accounts": plan.max_accounts,
                            "feature_set": plan.feature_set,
                            "latest_price": float(latest_price.price) if latest_price else None,
                            "latest_price_date": latest_price.observed_at.isoformat() if latest_price else None
                        })
                    
                    competitor_data.append({
                        "competitor_id": competitor.competitor_id,
                        "name": competitor.name,
                        "website": competitor.website,
                        "notes": competitor.notes,
                        "plans": plans_data
                    })
                
                db.close()
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
                db = db_session_factory()
                
                # Total tracks
                total_tracks = db.query(func.count(Track.track_id)).scalar() or 0
                
                # Top played tracks
                top_tracks = db.query(
                    Track.track_title,
                    Track.track_artist,
                    func.count(PlayHistory.play_id).label('play_count')
                ).join(
                    PlayHistory, PlayHistory.track_id == Track.track_id
                ).group_by(
                    Track.track_id, Track.track_title, Track.track_artist
                ).order_by(
                    func.count(PlayHistory.play_id).desc()
                ).limit(10).all()
                
                # Play count by date (last 30 days)
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                plays_by_date = db.query(
                    func.date(PlayHistory.played_at).label('date'),
                    func.count(PlayHistory.play_id).label('play_count')
                ).filter(
                    PlayHistory.played_at >= thirty_days_ago
                ).group_by(
                    func.date(PlayHistory.played_at)
                ).order_by(
                    func.date(PlayHistory.played_at)
                ).all()
                
                analytics = {
                    "total_tracks": total_tracks,
                    "top_tracks": [
                        {
                            "title": track.track_title,
                            "artist": track.track_artist,
                            "play_count": track.play_count
                        }
                        for track in top_tracks
                    ],
                    "plays_by_date": [
                        {
                            "date": play.date.isoformat() if play.date else None,
                            "play_count": play.play_count
                        }
                        for play in plays_by_date
                    ]
                }
                
                db.close()
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
                db = db_session_factory()
                
                # Get our current prices
                our_plans = db.query(SubscriptionPlan).all()
                
                # Get competitor prices for comparison
                competitor_prices = db.query(
                    CompetitorSubscriptionPlan.billing_period,
                    func.avg(CompetitorSubscriptionPriceSnapshot.price).label('avg_price')
                ).join(
                    CompetitorSubscriptionPriceSnapshot,
                    CompetitorSubscriptionPriceSnapshot.competitor_plan_id == CompetitorSubscriptionPlan.competitor_plan_id
                ).filter(
                    CompetitorSubscriptionPlan.is_student == False,
                    CompetitorSubscriptionPlan.is_family == False
                ).group_by(
                    CompetitorSubscriptionPlan.billing_period
                ).all()
                
                # Simple ML logic: recommend prices based on competitor average
                competitor_avg_by_period = {cp.billing_period: float(cp.avg_price) for cp in competitor_prices}
                
                recommendations = []
                for plan in our_plans:
                    # Determine billing period from plan name (simple heuristic)
                    period = "monthly"  # default
                    if "year" in plan.name.lower() or "annual" in plan.name.lower():
                        period = "yearly"
                    
                    competitor_avg = competitor_avg_by_period.get(period, None)
                    current_price = float(plan.price_usd)
                    
                    if competitor_avg:
                        # Recommend pricing slightly below competitor average
                        recommended_price = round(competitor_avg * 0.95, 2)
                        price_diff = recommended_price - current_price
                        
                        recommendation = "maintain" if abs(price_diff) < 1 else ("increase" if price_diff > 0 else "decrease")
                    else:
                        recommended_price = current_price
                        recommendation = "maintain"
                        price_diff = 0
                    
                    recommendations.append({
                        "plan_name": plan.name,
                        "current_price": current_price,
                        "recommended_price": recommended_price,
                        "price_diff": round(price_diff, 2),
                        "recommendation": recommendation,
                        "competitor_avg": competitor_avg
                    })
                
                db.close()
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
                
                if new_price < 0:
                    return jsonify({"error": "Price must be non-negative"}), 400
                
                db = db_session_factory()
                
                plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.plan_id == plan_id).first()
                if not plan:
                    db.close()
                    return jsonify({"error": "Plan not found"}), 404
                
                # Get user_id from JWT payload
                email = request.current_user.get('email')
                user = db.query(User).filter(User.email == email).first()
                user_id = user.user_id if user else None
                
                # Create price history entry
                price_history = SubscriptionPlanPrice(
                    plan_id=plan_id,
                    price=Decimal(str(new_price)),
                    currency_code="USD",
                    effective_from=datetime.utcnow(),
                    changed_by_user_id=user_id
                )
                
                # Update plan price
                plan.price_usd = Decimal(str(new_price))
                
                db.add(price_history)
                db.commit()
                db.close()
                
                return jsonify({
                    "message": "Price updated successfully",
                    "plan_id": plan_id,
                    "new_price": new_price
                }), 200
                
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
                
                if status not in ["active", "banned", "inactive"]:
                    return jsonify({"error": "Invalid status. Must be 'active', 'banned', or 'inactive'"}), 400
                
                db = db_session_factory()
                
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    db.close()
                    return jsonify({"error": "User not found"}), 404
                
                user.status = status
                db.commit()
                db.close()
                
                return jsonify({
                    "message": "User status updated successfully",
                    "user_id": user_id,
                    "status": status
                }), 200
                
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
                
                if role not in ["user", "admin"]:
                    return jsonify({"error": "Invalid role. Must be 'user' or 'admin'"}), 400
                
                db = db_session_factory()
                
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    db.close()
                    return jsonify({"error": "User not found"}), 404
                
                user.role = UserRole[role]
                db.commit()
                db.close()
                
                return jsonify({
                    "message": "User role updated successfully",
                    "user_id": user_id,
                    "role": role
                }), 200
                
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
                
                if page < 1 or per_page < 1 or per_page > 100:
                    return jsonify({"error": "Invalid pagination parameters"}), 400
                
                db = db_session_factory()
                
                # Get total count
                total = db.query(func.count(User.user_id)).scalar()
                
                # Get paginated users
                users = db.query(User)\
                    .order_by(User.user_id.desc())\
                    .offset((page - 1) * per_page)\
                    .limit(per_page)\
                    .all()
                
                users_data = [user.to_dict() for user in users]
                
                db.close()
                
                return jsonify({
                    "users": users_data,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total,
                        "total_pages": (total + per_page - 1) // per_page
                    }
                }), 200
                
            except Exception as e:
                print(f"[Admin] Error fetching users: {e}")
                return jsonify({"error": "Failed to fetch users"}), 500

        return admin_bp
