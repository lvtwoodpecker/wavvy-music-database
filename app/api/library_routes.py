from flask import Blueprint, jsonify, request
import app.api.base_routes as base_routes
from app.utils.auth import login_required


class LibraryRoutes(base_routes.BaseRoutes):
    def create_blueprint(self, app) -> Blueprint:
        bp = Blueprint('library', __name__)
        library_service = app.services.library_service
        search_service = app.services.search_service

        @bp.route('/tracks', methods=['GET'])
        @login_required
        def list_tracks():
            """
            List tracks from library.
            
            Query Parameters:
                q (optional): Search query to filter tracks
                limit (optional): Maximum results (default: 100)
            
            If 'q' parameter is provided, uses search service for filtering.
            Otherwise, returns all tracks from library service.
            """
            query = request.args.get('q', '').strip()
            
            # If search query provided, use search service
            if query:
                try:
                    limit = int(request.args.get('limit', 100))
                except ValueError:
                    limit = 100
                
                search_result = search_service.search(query, limit=limit)
                return jsonify(search_result["results"]), 200
            
            # Otherwise, use standard library listing
            try:
                limit = int(request.args.get('limit', 100))
            except ValueError:
                limit = 100
            
            data = library_service.list_tracks(limit=limit)
            return jsonify(data), 200

        return bp
