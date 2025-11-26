#  User service functions for managing user data and interactions
# This module provides functions to create, retrieve, update, and delete user information
from multiprocessing.connection import Client
from typing import Optional, Dict, Any
from app.services.stripe.stripe_service import StripeService
from app.services.user.find_user import FindUserService
from app.services.user.account_status import UserStatusService
from app.db.tables.User import User
from app.db.tables.Listener import Listener
from app.db.tables.Advertiser import Advertiser
from app.db.tables.StripeAccount import StripeAccount


class UserCreationService():
    """Service for creating users in the system."""
    def __init__(
        self, 
        stripe_service: StripeService,
        find_user_service: FindUserService,
        user_status_service: UserStatusService,
    ):
        self._stripe_service = stripe_service
        self._find_user_service = find_user_service
        self._user_status_service = user_status_service
        
    def create_base_user(
        self,
        sb: Client,
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
            res = self._find_user_service.get_user_by_email(sb, email)
            if res:
                raise ValueError("User with this email already exists")
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
            "status": "active",
            "role": role,
        }
        print(f"Creating user with data: {resp}")
        user_data = (
            sb
            .table(User.TABLE_NAME)
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
            stripe_customer_id = (
                self
                ._stripe_service
                .stripe_account_service
                .create_stripe_customer(
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
           )
        except Exception as e:
            # rollback user creation
            self._user_status_service.delete_user_by_id(sb, user_id=user["user_id"])
            print(f"Error creating stripe customer: {e}")
            raise RuntimeError("Failed to create stripe customer, user creation rolled back")
        
        # step 3: create local stripe account record
        try:
            print("Creating local stripe account record...")
            stripe_record = (
                self
                ._stripe_service
                .stripe_account_service
                .create_local_stripe_account_record(
                    user_id=user["user_id"],
                    stripe_customer_id=stripe_customer_id)
                )
        except Exception as e:
            # rollback user creation and stripe customer
            self._user_status_service.delete_user_by_id(sb, user_id=user["user_id"])
            self._stripe_service.stripe_account_service.delete_stripe_account_by_user_id(sb, user_id=user["user_id"])
            print(f"Error creating local stripe account record: {e}")
            raise RuntimeError("Failed to create local stripe account record, user creation rolled back")
        
        # return the created user
        user["stripe_account"] = stripe_record
        return user
    
    
    def verify_account_email(
        self,
        sb: Client,
        email: str,
        role: str
        ) -> None:
        """Marks a user's email as verified in the database."""
        
        if role == "listener":
            func = self._find_user_service.get_listener_by_user_id
        elif role == "advertiser":
            func = self._find_user_service.get_advertiser_by_user_id 
        else:
            raise ValueError("role must be listener or advertiser")
        
        success_msg = ""
        
        # Check if user with the same email already exists in the Users table and listener table
        try:
            existing_user = self._find_user_service.get_user_by_email(sb, email)
            existing_listener = self._find_user_service.func(sb, existing_user["user_id"]) if existing_user else None
            
            if existing_user.data and existing_listener.data:
                raise ValueError("Listener with this email already exists")
            
            if existing_user.data and not existing_listener.data:
                success_msg = "User with this email already exists but is not a listener"
                
            if not existing_user.data:
                success_msg = "No existing user with this email, proceeding to create new listener"
            
        except Exception as e:
            print(f"Error checking existing user: {e}")
            raise

        return success_msg

    def create_listener(
        self,
        sb: Client,
        email: str, 
        username: str,
        first_name: str,
        last_name: str,
        password_hash: str,
        country: str) -> Dict[str, Any]:
        
        """Create a new listener user.
        This function creates a base user and then adds listener-specific details.
        """
        success_msg = self.verify_account_email(sb, email, role="listener")
        
        # First, create the base user
        user = self.create_base_user(
            email, 
            username, 
            first_name, 
            last_name, 
            password_hash, 
            country, 
            role = "listener")
        
        # Now, add listener-specific details
        listener_data = {
            "user_id": user["user_id"],
            "ad_free": 0 # default to not ad-free
        }
        
        try: 
            response = (
                sb
                .table(Listener.TABLE_NAME)
                .insert(listener_data)
                .execute()
            )
        except Exception as e:
            raise RuntimeError(f"Error creating listener: {e}")
        
        data = response.data[0] if response.data else {}
        return {**user, **data, "success": success_msg}

    def create_advertiser(
        self,
        sb: Client,
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
        
        success_msg = self.verify_account_email(sb, email, role="advertiser")
        
        # First, create the base user
        user = self.create_base_user(
            sb,
            email, 
            username, 
            first_name, 
            last_name, 
            password_hash, 
            country, 
            role="advertiser"
        )
        
        # Now, add advertiser-specific details
        advertiser_data = {
            "user_id": user["id"],
            "company_name": company_name
        }
        
        response = (
            sb
            .table(Advertiser.TABLE_NAME)
            .insert(advertiser_data)
            .execute()
        )
        
        
        return {**user, **(response.data[0] if response.data else {}), "success": success_msg}


