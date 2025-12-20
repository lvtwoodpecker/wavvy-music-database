"""Content-based recommender API routes."""
from flask import Blueprint, request, jsonify
from app.services.content_based_recommender_service import ContentBasedRecommenderService
from app.utils.auth import login_required

recommender_bp = Blueprint("recommender", __name__)
service = ContentBasedRecommenderService()

@recommender_bp.route('/playlist/<int:playlist_id>', methods=['GET'])
@login_required
def recommend_for_playlist(playlist_id):
    limit = int(request.args.get('limit', 10))
    
    try:
        result = service.recommend_for_playlist(playlist_id, n_recommendations=limit)
        return jsonify({
            "playlist_id": playlist_id,
            "recommendations": result,
            "total_recommendations": len(result)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@recommender_bp.route('/user', methods=['GET'])
@login_required
def recommend_for_user():
    from flask import request
    from app.db.sqlalchemy_engine import SessionLocal
    from sqlalchemy import select
    from app.models.Listener import Listener
    
    user_id = request.current_user["user_id"]
    limit = int(request.args.get('limit', 10))
    
    # Get listener_id for this user
    with SessionLocal() as db:
        listener_stmt = select(Listener.listener_id).where(Listener.user_id == user_id)
        listener_id = db.scalars(listener_stmt).first()
        if not listener_id:
            return jsonify({"error": "listener not found"}), 404
    
    try:
        result = service.recommend_for_user(str(listener_id), n_recommendations=limit)
        return jsonify({
            "listener_id": str(listener_id),
            "recommendations": result,
            "total_recommendations": len(result)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

