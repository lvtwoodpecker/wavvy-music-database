from supabase import Client, create_client

class SupabaseClient:
    @staticmethod
    def init_supabase(supabase_url: str, supabase_key: str) -> Client | None:
        if supabase_url and supabase_key:
            # Initialize Supabase client
            # Attach to app for global access
            # This allows accessing supabase client via app.supabase
            supabase_client = create_client(supabase_url, supabase_key)
            return supabase_client
        else:
            print("[Supabase] Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in env")
            return None
