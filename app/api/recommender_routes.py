"""Content-based recommender API routes."""
from flask import Blueprint, request, jsonify
from app.services.content_based_recommender_service import ContentBasedRecommenderService

recommender_bp = Blueprint("recommender", __name__)
service = ContentBasedRecommenderService()

@recommender_bp.route('/playlist/<int:playlist_id>', methods=['GET'])
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

@recommender_bp.route('/user/<listener_id>', methods=['GET'])
def recommend_for_user(listener_id):
    limit = int(request.args.get('limit', 10))
    
    try:
        result = service.recommend_for_user(listener_id, n_recommendations=limit)
        return jsonify({
            "listener_id": listener_id,
            "recommendations": result,
            "total_recommendations": len(result)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

