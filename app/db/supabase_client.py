from supabase import create_client, Client
from app.config import settings

supabase: Client | None = None

if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
    # Initialize Supabase client
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
else:
    print("[Supabase] Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in env")
