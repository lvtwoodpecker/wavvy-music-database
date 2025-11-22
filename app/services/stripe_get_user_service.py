# app/services/user_service.py

from typing import Optional, Dict, Any
from app.db.supabase_client import supabase

USERS_TABLE = "User"

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    try:
        resp = (
            supabase.table(USERS_TABLE)
            .select("*")
            .eq("email", email)
            .maybe_single()
            .execute()
        )
    except Exception as e:
        print(f"[User Service] Error fetching user by email {email}: {e}")
        raise RuntimeError("Failed to fetch user by email")

    return resp.data  # dict or None
