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
                "stripe_account_id": account.id,
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
