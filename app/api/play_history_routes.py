from flask import Blueprint, request, jsonify
import app.api.base_routes as base_routes
from app.utils.auth import login_required


class PlayHistoryRoutes(base_routes.BaseRoutes):
    def create_blueprint(self, app) -> Blueprint:
        bp = Blueprint('play_history', __name__)

        @bp.route('', methods=['POST'])
        @login_required
        def track_play():
            """Track when a user plays a song for at least 10 seconds."""
            user_id = request.current_user["user_id"]
            data = request.get_json(force=True) or {}
            track_id = data.get('track_id')
            
            if not track_id:
                return jsonify({"error": "track_id is required"}), 400
            
            from app.db.sqlalchemy_engine import SessionLocal
            from sqlalchemy import select
            from app.models.Listener import Listener
            from app.models.PlayHistory import PlayHistory
            
            with SessionLocal() as db:
                # Get listener_id for this user
                listener_stmt = select(Listener.listener_id).where(Listener.user_id == user_id)
                listener_id = db.scalars(listener_stmt).first()
                if not listener_id:
                    return jsonify({"error": "listener not found"}), 404
                
                # Create play history entry
                play_history = PlayHistory(
                    listener_id=listener_id,
                    track_id=track_id,
                    is_skip=False
                )
                db.add(play_history)
                db.commit()
                db.refresh(play_history)
                
                return jsonify(play_history.to_dict()), 201

        return bp
