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
            
            Query Parameters:
                q (required): Search query string
                mode (optional): Search mode - "fts", "fuzzy", or "hybrid" (default: "hybrid")
                limit (optional): Maximum results to return (default: 50, max: 100)
                offset (optional): Number of results to skip for pagination (default: 0)
            
            Returns:
                JSON response with search results:
                {
                    "results": [...],
                    "query": "search query",
                    "count": 10,
                    "limit": 50,
                    "offset": 0
                }
            """
            query = request.args.get('q', '').strip()
            
            if not query:
                return jsonify({
                    "error": "Query parameter 'q' is required"
                }), 400
            
            mode = request.args.get('mode', 'hybrid')
            if mode not in ['fts', 'fuzzy', 'hybrid']:
                return jsonify({
                    "error": "Invalid mode. Must be 'fts', 'fuzzy', or 'hybrid'"
                }), 400
            
            try:
                limit = int(request.args.get('limit', 50))
                offset = int(request.args.get('offset', 0))
            except ValueError:
                return jsonify({
                    "error": "Invalid limit or offset value"
                }), 400
            
            try:
                results = search_service.search(
                    query=query,
                    mode=mode,
                    limit=limit,
                    offset=offset
                )
                return jsonify(results), 200
            except Exception as e:
                logger.error(f"Search error: {e}", exc_info=True)
                return jsonify({
                    "error": "An error occurred during search"
                }), 500
        
        @bp.route('/by-title', methods=['GET'])
        @login_required
        def search_by_title():
            """
            Search tracks specifically by title.
            
            Query Parameters:
                title (required): Track title to search for
                limit (optional): Maximum results (default: 20)
            
            Returns:
                JSON array of matching tracks
            """
            title = request.args.get('title', '').strip()
            
            if not title:
                return jsonify({
                    "error": "Query parameter 'title' is required"
                }), 400
            
            try:
                limit = int(request.args.get('limit', 20))
            except ValueError:
                return jsonify({
                    "error": "Invalid limit value"
                }), 400
            
            try:
                results = search_service.search_by_title(title, limit)
                return jsonify(results), 200
            except Exception as e:
                logger.error(f"Title search error: {e}", exc_info=True)
                return jsonify({
                    "error": "An error occurred during search"
                }), 500
        
        @bp.route('/by-artist', methods=['GET'])
        @login_required
        def search_by_artist():
            """
            Search tracks by artist name.
            
            Query Parameters:
                artist (required): Artist name to search for
                limit (optional): Maximum results (default: 20)
            
            Returns:
                JSON array of matching tracks
            """
            artist = request.args.get('artist', '').strip()
            
            if not artist:
                return jsonify({
                    "error": "Query parameter 'artist' is required"
                }), 400
            
            try:
                limit = int(request.args.get('limit', 20))
            except ValueError:
                return jsonify({
                    "error": "Invalid limit value"
                }), 400
            
            try:
                results = search_service.search_by_artist(artist, limit)
                return jsonify(results), 200
            except Exception as e:
                logger.error(f"Artist search error: {e}", exc_info=True)
                return jsonify({
                    "error": "An error occurred during search"
                }), 500
        
        @bp.route('/track/<int:track_id>', methods=['GET'])
        @login_required
        def get_track(track_id):
            """
            Get a single track by ID from search index.
            
            Path Parameters:
                track_id: Track ID
            
            Returns:
                JSON object with track details or 404 if not found
            """
            try:
                track = search_service.get_track(track_id)
                if track:
                    return jsonify(track), 200
                else:
                    return jsonify({
                        "error": "Track not found"
                    }), 404
            except Exception as e:
                logger.error(f"Get track error: {e}", exc_info=True)
                return jsonify({
                    "error": "An error occurred retrieving the track"
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
