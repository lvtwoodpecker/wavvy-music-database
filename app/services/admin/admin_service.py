# app/services/admin/admin_service.py

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.services import service
from app.models.SubscriptionPlan import SubscriptionPlan
from app.models.SubscriptionPlanPrice import SubscriptionPlanPrice
from app.models.User import User, UserRole
from app.models.Competitor import Competitor
from app.models.CompetitorSubscriptionPlan import CompetitorSubscriptionPlan
from app.models.CompetitorSubscriptionPriceSnapshot import CompetitorSubscriptionPriceSnapshot
from app.models.Track import Track
from app.models.PlayHistory import PlayHistory
from sqlalchemy.orm import selectinload

SessionFactory = Callable[[], Session]


class AdminService(service.Service):
    """Service for managing admin operations.
    
    This service provides admin-related functionality including:
    - Pricing trends and updates
    - Competitor data analysis
    - Music analytics
    - ML-based price recommendations
    - User management
    """

    def __init__(self, app):
        super().__init__(app)
        # Call create_service after init, following the pattern
        self.create_service()

    def create_service(self):
        print("Creating AdminService...")
        # No sub-services needed for now

    # --- Pricing Operations ---

    def get_pricing_trends(self) -> List[Dict[str, Any]]:
        db = self.db_session_factory()
        try:
            plans = (
                db.query(SubscriptionPlan)
                .options(selectinload(SubscriptionPlan.prices))
                .all()
            )

            pricing_data = []
            for plan in plans:
                history_rows = list(plan.prices or [])
                current = history_rows[0] if history_rows else None

                pricing_data.append({
                    "plan_id": plan.plan_id,
                    "plan_name": getattr(plan, "name", None),
                    "current_price": float(current.price) if current else None,
                    "history": [
                        {
                            # "price_id": h.price_id,
                            "price": float(h.price),
                            "effective_from": h.effective_from.isoformat() if h.effective_from else None,
                        }
                        for h in history_rows
                    ],
                })

            return pricing_data
        finally:
            db.close()

    def update_subscription_price(self, plan_id: int, new_price: float, user_email: str) -> Dict[str, Any]:
        """Update subscription plan price and create history entry."""
        if new_price < 0:
            raise ValueError("Price must be non-negative")
        
        db = self.db_session_factory()
        try:
            plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.plan_id == plan_id).first()
            if not plan:
                raise ValueError("Plan not found")
            
            # Get user_id from email
            user = db.query(User).filter(User.email == user_email).first()
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
            
            return {
                "plan_id": plan_id,
                "new_price": new_price,
                "updated_by": user_id
            }
        finally:
            db.close()

    # --- Competitor Operations ---

    def get_competitor_data(self) -> List[Dict[str, Any]]:
        """Get competitor pricing and plan information."""
        db = self.db_session_factory()
        try:
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
            
            return competitor_data
        finally:
            db.close()

    # --- Music Analytics ---

    def get_music_analytics(self) -> Dict[str, Any]:
        """Get music analytics data."""
        db = self.db_session_factory()
        try:
            # Total tracks
            total_tracks = db.query(func.count(Track.track_id)).scalar() or 0
            
            # Top played tracks
            top_tracks = db.query(
                Track.title,
                # Track.track_artist,
                func.count(PlayHistory.played_at).label('play_count')
            ).join(
                PlayHistory, PlayHistory.track_id == Track.track_id
            ).group_by(
                Track.track_id, Track.title
            ).order_by(
                func.count(PlayHistory.played_at).desc()
            ).limit(10).all()
            
            # Play count by date (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            plays_by_date = db.query(
                func.date(PlayHistory.played_at).label('date'),
                func.count(PlayHistory.played_at).label('play_count')
            ).filter(
                PlayHistory.played_at >= thirty_days_ago
            ).group_by(
                func.date(PlayHistory.played_at)
            ).order_by(
                func.date(PlayHistory.played_at)
            ).all()
            
            return {
                "total_tracks": total_tracks,
                "top_tracks": [
                    {
                        "title": track.title,
                        # "artist": track.track_artist,
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
        finally:
            db.close()

    # --- ML Price Analysis ---

    def get_ml_price_analysis(self) -> List[Dict[str, Any]]:
        """Get ML-based price recommendations."""
        db = self.db_session_factory()
        try:
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
            
            return recommendations
        finally:
            db.close()

    # --- User Management ---

    def get_users(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """Get paginated list of users."""
        if page < 1 or per_page < 1 or per_page > 100:
            raise ValueError("Invalid pagination parameters")
        
        db = self.db_session_factory()
        try:
            # Get total count
            total = db.query(func.count(User.user_id)).scalar()
            
            # Get paginated users
            users = db.query(User)\
                .order_by(User.user_id.desc())\
                .offset((page - 1) * per_page)\
                .limit(per_page)\
                .all()
            
            users_data = [user.to_dict() for user in users]
            
            return {
                "users": users_data,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page
                }
            }
        finally:
            db.close()

    def update_user_status(self, user_id: int, status: str) -> Dict[str, Any]:
        """Update user status."""
        if status not in ["active", "banned", "inactive"]:
            raise ValueError("Invalid status. Must be 'active', 'banned', or 'inactive'")
        
        db = self.db_session_factory()
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            user.status = status
            db.commit()
            
            return {
                "user_id": user_id,
                "status": status
            }
        finally:
            db.close()

    def update_user_role(self, user_id: int, role: str) -> Dict[str, Any]:
        """Update user role."""
        if role not in ["user", "admin"]:
            raise ValueError("Invalid role. Must be 'user' or 'admin'")
        
        db = self.db_session_factory()
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            user.role = UserRole[role]
            db.commit()
            
            return {
                "user_id": user_id,
                "role": role
            }
        finally:
            db.close()
