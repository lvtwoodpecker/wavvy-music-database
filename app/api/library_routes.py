from flask import Blueprint, jsonify
import app.api.base_routes as base_routes
from app.utils.auth import login_required


class LibraryRoutes(base_routes.BaseRoutes):
    def create_blueprint(self, app) -> Blueprint:
        bp = Blueprint('library', __name__)
        library_service = app.services.library_service

        @bp.route('/tracks', methods=['GET'])
        @login_required
        def list_tracks():
            data = library_service.list_tracks(limit=100)
            return jsonify(data), 200

        return bp
