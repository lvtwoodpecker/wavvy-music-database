from multiprocessing.dummy.connection import Client
from flask import Flask, jsonify
from app.WavvyAPI import WavvyAPI

class WavvyAPIWrapper(WavvyAPI):
    def __init__(self, import_name, **kwargs):
        super().__init__(import_name, **kwargs)
        
    def create_dev_app(self) -> Flask:
        app = WavvyAPI(__name__)
        
        @app.get('/')
        def index():
            return jsonify({
                "message": "Wavvy backend is running",
                "routes": {
                    "health": "/health",
                    "stripe_checkout": "/api/stripe/create-checkout-session",
                    "spotify_login": "/api/spotify/login",
                    "create_listener": "/api/users/create-listener",
                    "create_advertiser": "/api/users/create-advertiser",
                },
            })
        
        @app.get('/health')
        def health():
            return {
                "status": "ok",
                "message": "Wavvy Music Database API is running!"
            }
        
        return app
    
