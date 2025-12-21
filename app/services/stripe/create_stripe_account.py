from uuid import uuid4
from typing import Callable, Optional, Dict, Any
from sqlalchemy.orm import Session

import stripe
from supabase import Client
from app.models.User import User
from app.models.StripeAccount import StripeAccount


SessionFactory = Callable[[], Session]

class StripeAccountService:
    def __init__(self, stripe_api_key: str, db_session_factory: SessionFactory):
        stripe.api_key = stripe_api_key
        self._db_session_factory = db_session_factory

    def _get_session(self) -> Session:
        return self._db_session_factory()

    def create_local_stripe_account_record(self, user_id, stripe_customer_id, is_default=True):
        db = self._get_session()
        try:
            account = StripeAccount(
                user_id=user_id,
                stripe_customer_id=stripe_customer_id,
                is_default=is_default,
            )
            db.add(account)
            db.commit()
            db.refresh(account)

            return {
                "stripe_account_id": account.stripe_id,
                "user_id": account.user_id,
                "stripe_customer_id": account.stripe_customer_id,
                "is_default": account.is_default,
                "created_at": account.created_at.isoformat(),
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get_stripe_account_by_user_id(self, user_id: int) -> Optional[StripeAccount]:
        """Get the Stripe account for a user, if it exists."""
        db = self._get_session()
        try:
            return db.query(StripeAccount).filter(StripeAccount.user_id == user_id).first()
        except Exception as e:
            print(f"[Stripe Account Service] Error fetching stripe account for user {user_id}: {e}")
            raise
        finally:
            db.close()

    def create_or_get_stripe_customer(self, user_id: int, email: str, name: str) -> Dict[str, Any]:
        """
        Create a Stripe Customer or retrieve existing one for a user.
        
        Args:
            user_id: User's ID
            email: User's email
            name: User's full name
            
        Returns:
            Dictionary with stripe_customer_id and status
        """
        # Check if user already has a Stripe account
        existing_account = self.get_stripe_account_by_user_id(user_id)
        
        if existing_account:
            return {
                "stripe_customer_id": existing_account.stripe_customer_id,
                "status": "existing",
                "created_at": existing_account.created_at.isoformat()
            }
        
        # Create new Stripe Customer
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "user_id": str(user_id)
                }
            )
            
            # Save to database
            account_data = self.create_local_stripe_account_record(
                user_id=user_id,
                stripe_customer_id=customer.id,
                is_default=True
            )
            
            return {
                "stripe_customer_id": customer.id,
                "status": "created",
                "created_at": account_data["created_at"]
            }
        except stripe.error.StripeError as e:
            print(f"[Stripe Account Service] Stripe API error: {e}")
            raise ValueError(f"Failed to create Stripe customer: {str(e)}")
        except Exception as e:
            print(f"[Stripe Account Service] Error creating Stripe customer: {e}")
            raise
