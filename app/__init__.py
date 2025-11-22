from flask import Flask, jsonify
from .config import settings

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['ENV'] = settings.ENV

    # register our blueprints
    # these are classes that group routes together
    # important for modularity and organization
    # from .api.spotify_routes import spotify_bp
    from .api.stripe_routes import payment_bp
    from .api.user_routes import user_bp
    
    # app.register_blueprint(spotify_bp, url_prefix='/api/spotify')
    app.register_blueprint(payment_bp, url_prefix='/api/stripe')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    
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