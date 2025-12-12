#  Configuration settings for the FastAPI services
import os 
from dotenv import load_dotenv

load_dotenv()

class Settings: 
    # Flask settings
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")
    ENV: str = os.getenv("FLASK_ENV", "development")
    
    # FRONTEND settings
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:3000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5000")
    
    # PAYMENTS / STRIPE settings
    PAYMENTS_PROVIDER: str = os.getenv("PAYMENTS_PROVIDER", "stripe")
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # SUPABASE (HTTP / REST)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "") # Supabase project URL
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "") # Public anon key
    
    # SPOTIFY
    SPOTIFY_CLIENT_ID_P: str = os.getenv("SPOTIFY_CLIENT_ID_P", "")
    SPOTIFY_CLIENT_SECRET_P: str = os.getenv("SPOTIFY_CLIENT_SECRET_P", "")
    SPOTIFY_CLIENT_ID_C: str = os.getenv("SPOTIFY_CLIENT_ID_C", "")
    SPOTIFY_CLIENT_SECRET_C: str = os.getenv("SPOTIFY_CLIENT_SECRET_C", "")
    SPOTIFY_REDIRECT_URI: str = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
    
    # DATABASE (for SQLAlchemy)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/wavvy_db"
    )
