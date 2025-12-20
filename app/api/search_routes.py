"""
Search API routes for track search functionality.
Provides endpoints for searching tracks using FTS and trigram matching.
"""

import logging
from flask import Blueprint, jsonify, request
from app.api.base_routes import BaseRoutes
from app.utils.auth import login_required

logger = logging.getLogger(__name__)


class SearchRoutes(BaseRoutes):
    """Routes for track search API."""
    
    def create_blueprint(self, app) -> Blueprint:
        """
        Create and configure the search blueprint.
        
        Args:
            app: Flask application instance
            
        Returns:
            Configured Blueprint with search routes
        """
        bp = Blueprint('search', __name__)
        search_service = app.services.search_service
        
        @bp.route('', methods=['GET'])
        @bp.route('/', methods=['GET'])
        @login_required
        def search_tracks():
            """
            Search for tracks by query string.
            
            Uses hybrid FTS + trigram approach for best results.
            
            Query Parameters:
                q (required): Search query string
                limit (optional): Maximum results to return (default: 25, max: 100)
            
            Returns:
                JSON response with search results:
                {
                    "query": "search query",
                    "results": [...],
                    "used": {"fts": true, "trigram": false}
                }
            """
            query = request.args.get('q', '').strip()
            
            if not query:
                return jsonify({
                    "error": "Query parameter 'q' is required"
                }), 400
            
            try:
                limit = int(request.args.get('limit', 25))
                limit = max(1, min(limit, 100))  # Clamp between 1 and 100
            except ValueError:
                return jsonify({
                    "error": "Invalid limit value"
                }), 400
            
            try:
                results = search_service.search(query=query, limit=limit)
                return jsonify(results), 200
            except Exception as e:
                logger.error(f"Search error: {e}", exc_info=True)
                return jsonify({
                    "error": "An error occurred during search"
                }), 500
        
        @bp.route('/refresh', methods=['POST'])
        @login_required
        def refresh_index():
            """
            Refresh the search index from source tables.
            
            This endpoint should be called after bulk updates to tracks.
            Requires authentication.
            
            Returns:
                JSON response indicating success or failure
            """
            try:
                success = search_service.refresh_index()
                if success:
                    return jsonify({
                        "message": "Search index refreshed successfully"
                    }), 200
                else:
                    return jsonify({
                        "error": "Failed to refresh search index"
                    }), 500
            except Exception as e:
                logger.error(f"Index refresh error: {e}", exc_info=True)
                return jsonify({
                    "error": "An error occurred refreshing the index"
                }), 500
        
        @bp.route('/stats', methods=['GET'])
        @login_required
        def get_stats():
            """
            Get search index statistics.
            
            Returns:
                JSON object with index statistics
            """
            try:
                stats = search_service.get_stats()
                return jsonify(stats), 200
            except Exception as e:
                logger.error(f"Stats error: {e}", exc_info=True)
                return jsonify({
                    "error": "An error occurred retrieving stats"
                }), 500
        
        return bp
