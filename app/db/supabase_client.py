from supabase import Client, create_client
import os
from app.config import Settings

settings = Settings()
class SupabaseClient:
    @staticmethod
    def init_supabase() -> Client | None:
        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.SUPABASE_SERVICE_KEY

        if supabase_url and supabase_key:
            supabase_client = create_client(supabase_url, supabase_key)
            return supabase_client

        print("[Supabase] Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in env")
        return None
