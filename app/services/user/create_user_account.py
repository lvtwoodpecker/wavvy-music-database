from typing import Optional, Dict, Any, Callable
from sqlalchemy.orm import Session

from app.services.stripe.stripe_service import StripeService
from app.services.user.find_user import FindUserService
from app.services.user.account_status import UserStatusService

from app.models.User import User
from app.models.Listener import Listener
from app.models.Advertiser import Advertiser
from app.models.StripeAccount import StripeAccount

SessionFactory = Callable[[], Session]


class UserCreationService:
    """Service for creating users in the system using ORM."""

    def __init__(
        self,
        db_session_factory: SessionFactory,
        stripe_service: StripeService,
        find_user_service: FindUserService,
        user_status_service: UserStatusService,
    ):
        self._db_session_factory = db_session_factory
        self._stripe_service = stripe_service
        self._find_user_service = find_user_service
        self._user_status_service = user_status_service

    # ---------- Internal helpers ----------

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self._db_session_factory()

    @staticmethod
    def _serialize_user(user: User) -> Dict[str, Any]:
        """Turn a User ORM object into a dict suitable for API responses."""
        return {
            "user_id": user.user_id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "country": user.country,
            "status": user.status,
            "role": user.role.value if hasattr(user.role, "value") else user.role,
        }

    @staticmethod
    def _serialize_stripe_account(account: StripeAccount) -> Dict[str, Any]:
        """Turn a StripeAccount ORM object into a dict suitable for API responses."""
        return {
            "stripe_account_id": getattr(account, "id", None),
            "user_id": account.user_id,
            "stripe_customer_id": account.stripe_customer_id,
            "is_default": account.is_default,
            "created_at": account.created_at.isoformat() if account.created_at else None,
        }

    # ---------- Core logic ----------

    def create_base_user(
        self,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        password_hash: str,
        country: str,
        role: str,
    ) -> Dict[str, Any]:
        """
        Helper function to create a base user entry + local Stripe account record
        in a single transaction.

        Returns a dict representing the user + embedded stripe_account dict.
        
        STEPS: 
        0. Check if user with same email exists
        1. Create base User row (ORM)
        2. Create Stripe customer via Stripe API
        3. Create local StripeAccount row (ORM)
        4. Commit transaction
        """

        if role not in ("listener", "advertiser"):
            raise ValueError("role must be 'listener' or 'advertiser'")

        db = self._get_session()
        try:
            # Step 0: Check if user with the same email already exists
            existing_user = self._find_user_service.get_user_by_email(email)
            if existing_user:
                raise ValueError("User with this email already exists")

            # Step 1: Create the base user (but don't commit yet)
            user = User(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password_hash=password_hash,
                country=country,
                status="active",
                role=role,
            )
            db.add(user)
            db.flush()  # assign user.user_id without committing

            # Step 2: Create Stripe customer via Stripe API
            try:
                print("Creating Stripe customer...")
                stripe_customer_id = (
                    self
                    ._stripe_service
                    .stripe_account_service
                    .create_stripe_customer(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                    )
                )
            except Exception as e:
                print(f"Error creating Stripe customer: {e}")
                db.rollback()
                raise RuntimeError(
                    "Failed to create Stripe customer, user creation rolled back"
                )

            # Step 3: Create local Stripe account record (ORM)
            try:
                print("Creating local Stripe account record...")
                stripe_account = StripeAccount(
                    user_id=user.user_id,
                    stripe_customer_id=stripe_customer_id,
                    is_default=True,
                )
                db.add(stripe_account)
                db.flush()
            except Exception as e:
                print(f"Error creating local Stripe account record: {e}")
                db.rollback()
                raise RuntimeError(
                    "Failed to create local Stripe account record, user creation rolled back"
                )

            # Step 4: Commit everything
            db.commit()
            db.refresh(user)
            db.refresh(stripe_account)

            user_dict = self._serialize_user(user)
            user_dict["stripe_account"] = self._serialize_stripe_account(stripe_account)
            return user_dict

        except Exception:
            # We already rolled back in the specific error branches
            # If something else bubbles up, make sure we rollback too
            db.rollback()
            raise
        finally:
            db.close()

    def verify_account_email(
        self,
        email: str,
        role: str,
    ) -> str:
        """
        Check if a user with this email already exists and whether they already
        have a listener/advertiser profile.

        Returns a human-readable message about the situation.
        """

        if role not in ("listener", "advertiser"):
            raise ValueError("role must be 'listener' or 'advertiser'")

        existing_user = self._find_user_service.get_user_by_email(email)

        if role == "listener":
            if existing_user:
                listener = self._find_user_service.get_listener_by_user_id(
                    existing_user.user_id
                )
            else:
                listener = None

            if existing_user and listener:
                raise ValueError("Listener with this email already exists")

            if existing_user and not listener:
                return "User with this email already exists but is not a listener"
            if not existing_user:
                return "No existing user with this email, proceeding to create new listener"

        elif role == "advertiser":
            if existing_user:
                advertiser = self._find_user_service.get_advertiser_by_user_id(
                    existing_user.user_id
                )
            else:
                advertiser = None

            if existing_user and advertiser:
                raise ValueError("Advertiser with this email already exists")

            if existing_user and not advertiser:
                return "User with this email already exists but is not an advertiser"
            if not existing_user:
                return "No existing user with this email, proceeding to create new advertiser"

        return ""

    # ---------- Public APIs: create listener / advertiser ----------

    def create_listener(
        self,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        password_hash: str,
        country: str,
    ) -> Dict[str, Any]:
        """
        Create a new listener user:
        - Verify email usage
        - Create base user + Stripe account
        - Create Listener profile row
        """

        success_msg = self.verify_account_email(email, role="listener")

        # 1. Create base user + stripe account
        user_dict = self.create_base_user(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash,
            country=country,
            role="listener",
        )

        db = self._get_session()
        try:
            # 2. Create listener row
            listener = Listener(
                user_id=user_dict["user_id"],
                ad_free=False,  # default to not ad-free
            )
            db.add(listener)
            db.commit()
            db.refresh(listener)

            # Combine both for API response
            listener_data = {
                "listener_id": listener.listener_id,
                "user_id": listener.user_id,
                "ad_free": listener.ad_free,
            }

            return {
                **user_dict,
                "listener": listener_data,
                "success": success_msg,
            }

        except Exception as e:
            db.rollback()
            print(f"Error creating listener: {e}")
            # Optionally: you might want to deactivate/delete user here
            raise RuntimeError("Error creating listener")
        finally:
            db.close()

    def create_advertiser(
        self,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        password_hash: str,
        country: str,
        company_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new advertiser user:
        - Verify email usage
        - Create base user + Stripe account
        - Create Advertiser profile row
        """

        success_msg = self.verify_account_email(email, role="advertiser")

        # 1. Create base user + stripe account
        user_dict = self.create_base_user(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash,
            country=country,
            role="advertiser",
        )

        db = self._get_session()
        try:
            # 2. Create advertiser row
            advertiser = Advertiser(
                user_id=user_dict["user_id"],
                company_name=company_name,
            )
            db.add(advertiser)
            db.commit()
            db.refresh(advertiser)

            advertiser_data = {
                "advertiser_id": advertiser.advertiser_id,
                "user_id": advertiser.user_id,
                "company_name": advertiser.company_name,
            }

            return {
                **user_dict,
                "advertiser": advertiser_data,
                "success": success_msg,
            }

        except Exception as e:
            db.rollback()
            print(f"Error creating advertiser: {e}")
            # Optionally: deactivate/delete user here
            raise RuntimeError("Error creating advertiser")
        finally:
            db.close()
