from flask import Blueprint, request, jsonify
import app.api.base_routes as base_routes
from app.utils.auth import login_required


class PlaylistRoutes(base_routes.BaseRoutes):
    def create_blueprint(self, app) -> Blueprint:
        bp = Blueprint('playlist', __name__)
        service = app.services.playlist_service

        @bp.route('', methods=['GET'])
        @login_required
        def list_playlists():
            owner_id = request.current_user["user_id"]
            pls = service.list_playlists(owner_id)
            return jsonify([p.to_dict() for p in pls])

        @bp.route('', methods=['POST'])
        @login_required
        def create_playlist():
            owner_id = request.current_user["user_id"]
            data = request.get_json(force=True) or {}
            name = data.get('name')
            if not name:
                return jsonify({"error": "name is required"}), 400
            description = data.get('description')
            pl = service.create_playlist(owner_id, name, description)
            return jsonify(pl.to_dict()), 201

        @bp.route('/<int:playlist_id>', methods=['GET'])
        @login_required
        def get_playlist(playlist_id: int):
            owner_id = request.current_user["user_id"]
            pl = service.get_playlist(playlist_id, owner_id)
            if not pl:
                return jsonify({"error": "not found"}), 404
            return jsonify(pl.to_dict(include_tracks=True))

        @bp.route('/<int:playlist_id>', methods=['DELETE'])
        @login_required
        def delete_playlist(playlist_id: int):
            owner_id = request.current_user["user_id"]
            ok = service.delete_playlist(playlist_id, owner_id)
            return ("", 204) if ok else (jsonify({"error": "not found"}), 404)

        @bp.route('/<int:playlist_id>/tracks', methods=['POST'])
        @login_required
        def add_track(playlist_id: int):
            owner_id = request.current_user["user_id"]
            data = request.get_json(force=True) or {}
            required = ["title", "audio_url"]
            if any(not data.get(k) for k in required):
                return jsonify({"error": "title and audio_url are required"}), 400
            tr = service.add_track(playlist_id, owner_id, data)
            if not tr:
                return jsonify({"error": "playlist not found"}), 404
            return jsonify(tr.to_dict()), 201

        @bp.route('/<int:playlist_id>/tracks/<int:track_id>', methods=['DELETE'])
        @login_required
        def remove_track(playlist_id: int, track_id: int):
            owner_id = request.current_user["user_id"]
            ok = service.remove_track(playlist_id, track_id, owner_id)
            return ("", 204) if ok else (jsonify({"error": "not found"}), 404)

        @bp.route('/<int:playlist_id>/reorder', methods=['PUT'])
        @login_required
        def reorder_tracks(playlist_id: int):
            owner_id = request.current_user["user_id"]
            data = request.get_json(force=True) or {}
            order = data.get('order')  # list of track ids
            if not isinstance(order, list) or not order:
                return jsonify({"error": "order must be a non-empty list of track ids"}), 400
            ok = service.reorder_tracks(playlist_id, order, owner_id)
            if not ok:
                return jsonify({"error": "invalid order or playlist not found"}), 400
            return jsonify({"status": "ok"})

        return bp
