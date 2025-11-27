from flask import Flask, jsonify
from .config import settings

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['ENV'] = settings.ENV

    # register our blueprints
    # these are classes that group routes together
    # important for modularity and organization
    from .api.spotify_routes import spotify_bp
    from .api.stripe_routes import payment_bp
    from .api.user_routes import user_bp
    from .api.auth_routes import auth_bp
    from .api.similarity_routes import similarity_bp
    from .api.recommender_routes import recommender_bp
    
    app.register_blueprint(spotify_bp, url_prefix='/api/spotify')
    app.register_blueprint(payment_bp, url_prefix='/api/stripe')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(similarity_bp, url_prefix="/api/similarity")
    app.register_blueprint(recommender_bp, url_prefix="/api/recommender")
    
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
                "similarity": "/api/similarity/content-based-similarity?user1=username1&user2=username2",
                "similarity_recommendations": "/api/similarity/content-based-recommendations?user1=username1&user2=username2&limit=10&max_artist_repeats=2",
                "playlist_recommendations": "/api/recommender/playlist/<playlist_id>?limit=10",
                "user_recommendations": "/api/recommender/user/<listener_id>?limit=10",
            },
        })
    
    @app.get('/health')
    def health():
        return {
            "status": "ok",
            "message": "Wavvy Music Database API is running!"
        }
    

    return app