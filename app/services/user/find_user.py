# app/services/user_service.py

from typing import Optional, Dict, Any
from app.db.tables.User import User
from app.db.tables.Listener import Listener
from app.db.tables.Advertiser import Advertiser
from multiprocessing.connection import Client

class FindUserService:
    """Service for retrieving user information."""

    def get_user_by_email(
        self,
        sb: Client,
        email: str) -> Optional[Dict[str, Any]]:
        try:
            resp = (
                sb.table(User.TABLE_NAME)
                .select("*")
                .eq("email", email)
                .maybe_single()
                .execute()
            )
        except Exception as e:
            print(f"[User Service] Error fetching user by email {email}: {e}")
            raise RuntimeError("Failed to fetch user by email")

        return resp.data  # dict or None
    
    def get_user_by_id(
        self,
        sb: Client,
        user_id: int) -> Optional[Dict[str, Any]]:
        try:
            resp = (
                sb.table(User.TABLE_NAME)
                .select("*")
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
        except Exception as e:
            print(f"[User Service] Error fetching user by ID {user_id}: {e}")
            raise RuntimeError("Failed to fetch user by ID")

        return resp.data  # dict or None
    
    def get_user_role_by_id(
        self,
        sb: Client,
        user_id: int) -> Optional[str]:
        try:
            resp = (
                sb.table(User.TABLE_NAME)
                .select("role")
                .eq(User.USER_ID, user_id)
                .maybe_single()
                .execute()
            )
        except Exception as e:
            print(f"[User Service] Error fetching user role by ID {user_id}: {e}")
            raise RuntimeError("Failed to fetch user role by ID")

        if resp.data:
            return resp.data.get("role")
        return None
    
    def get_listener_by_user_id(
        self,
        sb: Client,
        user_id: int) -> Optional[Dict[str, Any]]:
        try:
            resp = (
                sb.table(Listener.TABLE_NAME)
                .select("*")
                .eq(Listener.USER_ID, user_id)
                .maybe_single()
                .execute()
            )
        except Exception as e:
            print(f"[User Service] Error fetching listener by user ID {user_id}: {e}")
            raise RuntimeError("Failed to fetch listener by user ID")

        return resp.data  # dict or None
    
    def get_advertiser_by_user_id(
        self,
        sb: Client,
        user_id: int) -> Optional[Dict[str, Any]]:
        try:
            resp = (
                sb.table(Advertiser.TABLE_NAME)
                .select("*")
                .eq(Advertiser.USER_ID, user_id)
                .maybe_single()
                .execute()
            )
        except Exception as e:
            print(f"[User Service] Error fetching advertiser by user ID {user_id}: {e}")
            raise RuntimeError("Failed to fetch advertiser by user ID")

        return resp.data  # dict or None
    
    def get_user_by_username(
        self,
        sb: Client,
        username: str) -> Optional[Dict[str, Any]]:
        try:
            resp = (
                sb.table(User.TABLE_NAME)
                .select("*")
                .eq(User.USERNAME, username)
                .maybe_single()
                .execute()
            )
        except Exception as e:
            print(f"[User Service] Error fetching user by username {username}: {e}")
            raise RuntimeError("Failed to fetch user by username")

        return resp.data  # dict or None
    
    
