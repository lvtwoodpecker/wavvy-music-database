"""User similarity API routes."""
from flask import Blueprint, request, jsonify
from app.services.content_based_similarity_service import ContentBasedSimilarityService

similarity_bp = Blueprint("similarity", __name__)
service = ContentBasedSimilarityService()

@similarity_bp.route('/content-based-similarity', methods=['GET'])
def get_content_based_similarity():
    user1 = request.args.get('user1')
    user2 = request.args.get('user2')
    
    if not user1 or not user2:
        return jsonify({"error": "user1 and user2 required"}), 400
    
    try:
        result = service.calculate_content_based_similarity(user1, user2)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@similarity_bp.route('/content-based-recommendations', methods=['GET'])
def get_content_based_recommendations():
    user1 = request.args.get('user1')
    user2 = request.args.get('user2')
    limit = int(request.args.get('limit', 10))
    max_artist_repeats = int(request.args.get('max_artist_repeats', 2))
    
    if not user1 or not user2:
        return jsonify({"error": "user1 and user2 required"}), 400
    
    try:
        result = service.get_recommendations_for_both_users(
            user1, user2, n_recommendations=limit, max_artist_repeats=max_artist_repeats
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

