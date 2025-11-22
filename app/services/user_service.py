#  User service functions for managing user data and interactions
# This module provides functions to create, retrieve, update, and delete user information

from typing import Optional, Dict, Any
from app.db.supabase_client import supabase

if supabase is None:
    raise RuntimeError("Supabase client is not configured")

USERS_TABLE = "User"
LISTENER_TABLE = "Listener"
ADVERTISER_TABLE = "Advertiser"

def _create_base_user(
    email: str, 
    username: str,
    first_name: str,
    last_name: str,
    password_hash: str,
    country: str,
    role: str) -> Dict[str, Any]:
    
    """Helper function to create a base user entry.
    This function inserts a new user into the Users table with the provided details.
    """
    
    if role not in ("listener", "advertiser"):
        raise ValueError("role must be listener or advertiser")
    
    
    resp = {
        "email": email,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "password_hash": password_hash,
        "country": country,
        "role": role,
    }
    
    try: 
        existing_user = supabase.table(USERS_TABLE).select("*").eq("email", email).execute()
        if existing_user.data:
            # pass user_id to caller to handle
            return existing_user.data[0]
    except Exception as e:
        print(f"Error checking existing user: {e}")
        raise
    
    response = (
        supabase
        .table(USERS_TABLE)
        .insert(resp)
        .execute()
    )
    
    if "error" in response and response.error:
        print(f"Error creating user: {response.error.message}")
        raise RuntimeError("Failed to create user")
    
    return response.data[0] if response.data else {}

def _delete_user_by_id(user_id: int) -> None:
    """Helper function to delete a user by their ID."""
    try:
        response = (
            supabase
            .table(USERS_TABLE)
            .delete()
            .eq("id", user_id)
            .execute()
        )
    except Exception as e:
        print(f"Error deleting user with ID {user_id}: {response.error.message}")
        raise RuntimeError("Failed to delete user")

def create_listener(
    email: str, 
    username: str,
    first_name: str,
    last_name: str,
    password_hash: str,
    country: str) -> Dict[str, Any]:
    
    """Create a new listener user.
    This function creates a base user and then adds listener-specific details.
    """
    
    # Check if user with the same email already exists in the Users table and listener table
    try:
        existing_user = supabase.table(USERS_TABLE).select("*").eq("email", email).execute()
        existing_listener = supabase.table(LISTENER_TABLE).select("*").eq("user_id", existing_user.data[0]['user_id'] if existing_user.data else -1).execute()
        
        if existing_user.data and existing_listener.data:
            raise ValueError("Listener with this email already exists")
        
    except Exception as e:
        print(f"Error checking existing user: {e}")
        raise
    
    # First, create the base user
    user = _create_base_user(email, username, first_name, last_name, password_hash, country, role="listener")
    
    # Now, add listener-specific details
    listener_data = {
        "user_id": user["user_id"],
        "ad_free": 0 # default to not ad-free
    }
    
    try: 
        response = (
            supabase
            .table(LISTENER_TABLE)
            .insert(listener_data)
            .execute()
        )
        
    except Exception as e:
        raise RuntimeError(f"Error creating listener: {e}")
    
    return {**user, **(response.data[0] if response.data else {})}

def create_advertiser(
    email: str, 
    username: str,
    first_name: str,
    last_name: str,
    password_hash: str,
    country: str,
    company_name: Optional[str] = None) -> Dict[str, Any]:
    
    """Create a new advertiser user.
    This function creates a base user and then adds advertiser-specific details.
    """
    
    # First, create the base user
    user = _create_base_user(email, username, first_name, last_name, password_hash, country, role="advertiser")
    
    # Now, add advertiser-specific details
    advertiser_data = {
        "user_id": user["id"],
        "company_name": company_name
    }
    
    response = (
        supabase
        .table(ADVERTISER_TABLE)
        .insert(advertiser_data)
        .execute()
    )
    
    
    return {**user, **(response.data[0] if response.data else {})}


