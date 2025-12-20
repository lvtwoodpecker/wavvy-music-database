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
            user_id = request.current_user["user_id"]
            from app.db.sqlalchemy_engine import SessionLocal
            from sqlalchemy import select
            from app.models.Listener import Listener
            
            with SessionLocal() as db:
                listener_stmt = select(Listener.listener_id).where(Listener.user_id == user_id)
                listener_id = db.scalars(listener_stmt).first()
                if not listener_id:
                    return jsonify([])
            
            pls = service.list_playlists(listener_id)
            return jsonify([p.to_dict() for p in pls])

        @bp.route('', methods=['POST'])
        @login_required
        def create_playlist():
            user_id = request.current_user["user_id"]
            data = request.get_json(force=True) or {}
            name = data.get('name')
            if not name:
                return jsonify({"error": "name is required"}), 400
            description = data.get('description')
            
            from app.db.sqlalchemy_engine import SessionLocal
            from sqlalchemy import select
            from app.models.Listener import Listener
            
            with SessionLocal() as db:
                listener_stmt = select(Listener.listener_id).where(Listener.user_id == user_id)
                listener_id = db.scalars(listener_stmt).first()
                if not listener_id:
                    return jsonify({"error": "listener not found"}), 404
            
            pl = service.create_playlist(listener_id, name, description)
            return jsonify(pl.to_dict()), 201

        @bp.route('/<int:playlist_id>', methods=['GET'])
        @login_required
        def get_playlist(playlist_id: int):
            user_id = request.current_user["user_id"]
            from app.db.sqlalchemy_engine import SessionLocal
            from sqlalchemy import select, text
            
            with SessionLocal() as db:
                from app.models.Listener import Listener
                from app.models.Playlist import Playlist
                
                # Get listener_id for this user
                listener_stmt = select(Listener.listener_id).where(Listener.user_id == user_id)
                listener_id = db.scalars(listener_stmt).first()
                if not listener_id:
                    return jsonify({"error": "listener not found"}), 404
                
                # Query playlist - allow access if user owns it OR it's public
                stmt = select(Playlist).where(Playlist.id == playlist_id)
                pl = db.scalars(stmt).first()
                if not pl:
                    return jsonify({"error": "not found"}), 404
                
                # Check permissions: user must own it or it must be public
                if pl.owner_id != listener_id and not pl.is_public:
                    return jsonify({"error": "not found"}), 404
                
                # Get tracks with track metadata
                result = db.execute(text(
                    'SELECT t.track_id, t.title, COALESCE(a.name, \'Unknown\') as artist, t.audio_file_url, t.duration_ms '
                    'FROM "PlaylistTrack" pt '
                    'JOIN "Track" t ON pt.track_id = t.track_id '
                    'LEFT JOIN "TrackArtist" ta ON t.track_id = ta.track_id '
                    'LEFT JOIN "Artist" a ON ta.artist_id = a.artist_id '
                    'WHERE pt.playlist_id = :playlist_id '
                    'ORDER BY pt.date_added'
                ), {"playlist_id": playlist_id})
                
                tracks = []
                for row in result:
                    track_id, title, artist, audio_url, duration = row
                    tracks.append({
                        "id": track_id,
                        "track_id": track_id,
                        "title": title or "Untitled",
                        "artist": artist or "Unknown artist",
                        "audio_url": audio_url,
                        "duration_ms": duration or 0,
                    })
                
                data = {
                    "id": pl.id,
                    "name": pl.name,
                    "owner_id": pl.owner_id,
                    "created_at": pl.created_at.isoformat() if pl.created_at else None,
                    "is_public": pl.is_public,
                    "is_collaborative": pl.is_collaborative,
                    "tracks": tracks
                }
                return jsonify(data)

        @bp.route('/<int:playlist_id>', methods=['DELETE'])
        @login_required
        def delete_playlist(playlist_id: int):
            user_id = request.current_user["user_id"]
            
            from app.db.sqlalchemy_engine import SessionLocal
            from sqlalchemy import select
            from app.models.Listener import Listener
            from app.models.Playlist import Playlist
            
            with SessionLocal() as db:
                listener_stmt = select(Listener.listener_id).where(Listener.user_id == user_id)
                listener_id = db.scalars(listener_stmt).first()
                if not listener_id:
                    return jsonify({"error": "listener not found"}), 404
                
                # Get playlist to check if it's public
                pl_stmt = select(Playlist).where(Playlist.id == playlist_id, Playlist.owner_id == listener_id)
                pl = db.scalars(pl_stmt).first()
                if not pl:
                    return jsonify({"error": "not found"}), 404
                
                # Don't allow deletion of public/system playlists
                if pl.is_public:
                    return jsonify({"error": "cannot delete public playlists"}), 403
            
            ok = service.delete_playlist(playlist_id, listener_id)
            return ("", 204) if ok else (jsonify({"error": "not found"}), 404)

        @bp.route('/<int:playlist_id>/tracks', methods=['POST'])
        @login_required
        def add_track(playlist_id: int):
            user_id = request.current_user["user_id"]
            data = request.get_json(force=True) or {}
            required = ["track_id"]
            if any(not data.get(k) for k in required):
                return jsonify({"error": "track_id is required"}), 400
            
            from app.db.sqlalchemy_engine import SessionLocal
            from sqlalchemy import select
            from app.models.Listener import Listener
            
            with SessionLocal() as db:
                listener_stmt = select(Listener.listener_id).where(Listener.user_id == user_id)
                listener_id = db.scalars(listener_stmt).first()
                if not listener_id:
                    return jsonify({"error": "listener not found"}), 404
            
            tr = service.add_track(playlist_id, listener_id, data)
            if not tr:
                return jsonify({"error": "playlist not found"}), 404
            return jsonify(tr.to_dict()), 201

        @bp.route('/<int:playlist_id>/tracks/<int:track_id>', methods=['DELETE'])
        @login_required
        def remove_track(playlist_id: int, track_id: int):
            user_id = request.current_user["user_id"]
            
            from app.db.sqlalchemy_engine import SessionLocal
            from sqlalchemy import select
            from app.models.Listener import Listener
            
            with SessionLocal() as db:
                listener_stmt = select(Listener.listener_id).where(Listener.user_id == user_id)
                listener_id = db.scalars(listener_stmt).first()
                if not listener_id:
                    return jsonify({"error": "listener not found"}), 404
            
            ok = service.remove_track(playlist_id, track_id, listener_id)
            return ("", 204) if ok else (jsonify({"error": "not found"}), 404)

        @bp.route('/<int:playlist_id>/reorder', methods=['PUT'])
        @login_required
        def reorder_tracks(playlist_id: int):
            user_id = request.current_user["user_id"]
            data = request.get_json(force=True) or {}
            order = data.get('order')  # list of track ids
            if not isinstance(order, list) or not order:
                return jsonify({"error": "order must be a non-empty list of track ids"}), 400
            
            from app.db.sqlalchemy_engine import SessionLocal
            from sqlalchemy import select
            from app.models.Listener import Listener
            
            with SessionLocal() as db:
                listener_stmt = select(Listener.listener_id).where(Listener.user_id == user_id)
                listener_id = db.scalars(listener_stmt).first()
                if not listener_id:
                    return jsonify({"error": "listener not found"}), 404
            
            ok = service.reorder_tracks(playlist_id, order, listener_id)
            if not ok:
                return jsonify({"error": "invalid order or playlist not found"}), 400
            return jsonify({"status": "ok"})

        return bp
