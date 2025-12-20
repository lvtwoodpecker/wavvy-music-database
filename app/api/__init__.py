# app/api/__init__.py
from app.api.stripe_routes import StripeRoutes
from app.api.auth_routes import AuthRoutes
from app.api.playlist_routes import PlaylistRoutes
from app.api.library_routes import LibraryRoutes
from app.api.recommender_routes import recommender_bp
from app.api.play_history_routes import PlayHistoryRoutes
from app.api.search_routes import SearchRoutes

class WavvyAPIBlueprints():
    @staticmethod
    def register_blueprints(app) -> None:
        """Register all blueprints for the app."""
        registers_routes = {
            'stripe': StripeRoutes(app),
            'auth': AuthRoutes(app),
            'playlist': PlaylistRoutes(app),
            'library': LibraryRoutes(app),
            'play-history': PlayHistoryRoutes(app),
            'search': SearchRoutes(app),
        }
        
        for route_name, route_class in registers_routes.items():
            bp = route_class.create_blueprint(app)
            app.register_blueprint(bp, url_prefix=f'/api/{route_name}')
        
        # Register direct blueprint for recommender
        app.register_blueprint(recommender_bp, url_prefix='/api/recommend')
            
    @staticmethod
    def register_all(app) -> None:
        WavvyAPIBlueprints.register_blueprints(app)
        
    @staticmethod
    def register_auth(app) -> None:
        auth_routes = AuthRoutes(app)
        bp = auth_routes.create_blueprint(app)
        app.register_blueprint(bp, url_prefix='/api/auth')
        
    # @staticmethod
    # def register_users(app) -> None:
    #     user_routes = AuthRoutes(app)
    #     bp = user_routes.create_blueprint(app)
    #     app.register_blueprint(bp, url_prefix='/api/users')
        
    @staticmethod
    def register_stripe(app) -> None:
        stripe_routes = StripeRoutes(app)
        bp = stripe_routes.create_blueprint(app)
        app.register_blueprint(bp, url_prefix='/api/stripe')