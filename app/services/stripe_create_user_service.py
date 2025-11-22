#  User service functions for managing user data and interactions
# This module provides functions to create, retrieve, update, and delete user information

from typing import Optional, Dict, Any
from app.db.supabase_client import supabase

from app.services.stripe_account_service import (
    create_stripe_customer,
    create_local_stripe_account_record,
    delete_stripe_account_by_user_id
)

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
    role: str
    ) -> Dict[str, Any]:
    
    """Helper function to create a base user entry.
    This function inserts a new user into the Users table with the provided details.
    """
    
    if role not in ("listener", "advertiser"):
        raise ValueError("role must be listener or advertiser")
    
    # Step 0: Check if user with the same email already exists in the Users table
    try: 
        existing_user = supabase.table(USERS_TABLE).select("*").eq("email", email).execute()
        if existing_user.data:
            # pass user_id to caller to handle
            return existing_user.data[0]
    except Exception as e:
        print(f"Error checking existing user: {e}")
        raise
    
    # Step 1: Create the base user
    resp = {
        "email": email,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "password_hash": password_hash,
        "country": country,
        "role": role,
    }
    print(f"Creating user with data: {resp}")
    user_data = (
        supabase
        .table(USERS_TABLE)
        .insert(resp)
        .execute()
    )
    
    if "error" in user_data and user_data.error:
        print(f"Error creating user: {user_data.error.message}")
        raise RuntimeError("Failed to create user")
    
    user = user_data.data[0]
    
    # step 2: create stripe customer
    try:
        print("Creating stripe customer...")
        stripe_customer_id = create_stripe_customer(
            email=email,
            first_name=first_name,
            last_name=last_name
        )
    except Exception as e:
        # rollback user creation
        _delete_user_by_id(user_id=user["user_id"])
        print(f"Error creating stripe customer: {e}")
        raise RuntimeError("Failed to create stripe customer, user creation rolled back")
    
    # step 3: create local stripe account record
    try:
        print("Creating local stripe account record...")
        stripe_record = create_local_stripe_account_record(
            user_id=user["user_id"],
            stripe_customer_id=stripe_customer_id
        )
    except Exception as e:
        # rollback user creation and stripe customer
        _delete_user_by_id(user_id=user["user_id"])
        delete_stripe_account_by_user_id(user_id=user["user_id"])
        print(f"Error creating local stripe account record: {e}")
        raise RuntimeError("Failed to create local stripe account record, user creation rolled back")
    
    # return the created user
    user["stripe_account"] = stripe_record
    return user
    

def _delete_user_by_id(user_id: int) -> None:
    """Helper function to delete a user by their ID."""
    print(f"Deleting user with ID: {user_id}")
    try:
        response = (
            supabase
            .table(USERS_TABLE)
            .delete()
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as e:
        print(f"Error deleting user with ID {user_id}: {e}")
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


