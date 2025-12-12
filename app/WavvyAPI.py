from flask import Flask
from flask_cors import CORS
from supabase import Client
from app.config import Settings
from app.db.supabase_client import SupabaseClient
from app.db.sqlalchemy_engine import SessionLocal, Base, engine # ORM base and engine
from app.api import WavvyAPIBlueprints
from app.services.register_services import APIServices


class WavvyAPI(Flask):
    """
    Main Flask application class for Wavvy API.
    
    Initializes settings, Supabase client, database, services, and blueprints.
    Provides properties to access settings, Supabase client, database session factory, 
    and services.
    
    Attributes:
        _settings (Settings): Application settings instance.
        _supabase (Client | None): Supabase client instance.
        _services (APIServices | None): Registered application services.
        
    Methods:
        init_config(): Initializes Flask app configuration.
        init_supabase(): Initializes Supabase client.
        init_database(): Initializes database and creates tables in development.
        init_services(): Initializes application services.
        register_blueprints(): Registers API blueprints with the Flask app.
    """
    
    def __init__(self, import_name, **kwargs):
        """Initialize WavvyAPI application."""
        
        super().__init__(import_name, **kwargs)
        self._settings = Settings()
        self._supabase: Client | None = None
        self._services: APIServices | None = None

        self.init_config()
        self.init_cors()
        self.init_supabase()
        self.init_database()
        self.init_services()
        self.register_blueprints()

    # settings
    @property
    def settings(self) -> Settings:
        return self._settings

    # supabase
    @property
    def supabase(self) -> Client:
        if self._supabase is None:
            raise RuntimeError("Supabase client accessed before initialization.")
        return self._supabase

    def init_supabase(self) -> None:
        """Initialize Supabase client."""
        self._supabase = SupabaseClient.init_supabase()
        if self._supabase is None:
            raise RuntimeError("Failed to initialize Supabase client.")

    # ORM / DB
    @property
    def db_session_factory(self):
        """Get the SQLAlchemy SessionLocal factory."""
        return SessionLocal

    def init_database(self) -> None:
        """Initialize database and create tables in development environment."""
        # Optional: only auto-create tables in dev
        if self.settings.ENV == "development":
            Base.metadata.create_all(bind=engine)

    # services
    @property
    def services(self) -> APIServices:
        if self._services is None:
            raise RuntimeError("Services accessed before initialization.")
        return self._services

    def init_services(self) -> None:
        self._services = APIServices(self)

    # config
    def init_config(self) -> None:
        self.config["SECRET_KEY"] = self._settings.SECRET_KEY
        self.config["ENV"] = self._settings.ENV

    # CORS
    def init_cors(self) -> None:
        """Initialize CORS with frontend URL."""
        CORS(self, resources={
            r"/api/*": {
                "origins": [self._settings.FRONTEND_URL],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        })

    # blueprints
    def register_blueprints(self) -> None:
        WavvyAPIBlueprints.register_blueprints(self)
