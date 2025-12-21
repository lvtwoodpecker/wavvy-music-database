from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Callable
from sqlalchemy.orm import Session

from app.services.pricing.subscription_pricing_repo import SubscriptionPricingRepo, PriceKey
from app.services.pricing.price_change_request import PriceChangeRequest

SessionFactory = Callable[[], Session]

class SubscriptionPricingService:
    def __init__(self, db_session_factory: SessionFactory) -> None:
        self._db_session_factory = db_session_factory
        self.session = self._get_session()
        self.repo = SubscriptionPricingRepo(self.session)
        
    def _get_session(self) -> Session:
        return self._db_session_factory()   

    def get_current_price(self, plan_id: int, country_code: Optional[str], currency_code: str = "USD") -> Optional[float]:
        row = self.repo.get_current_price_row(PriceKey(plan_id, country_code, currency_code))
        return float(row.price) if row else None

    def change_price(self, req: PriceChangeRequest, admin_user_id: Optional[int]) -> int:
        """
        Creates a new price row; commit applies trigger + exclusion constraint.
        Returns plan_price_id of the newly inserted row.
        """
        key = PriceKey(req.plan_id, req.country_code, req.currency_code)

        self.repo.insert_new_price(
            key=key,
            new_price=req.new_price,
            changed_by_user_id=admin_user_id,
            change_reason=req.change_reason,
        )

        # Flush so we catch exclusion constraint/trigger errors before returning
        self.session.flush()

        # Commit outside if you use unit-of-work pattern; otherwise commit here:
        self.session.commit()

        # Return latest inserted row id (simple approach)
        row = self.repo.get_current_price_row(key)
        return row.plan_price_id if row else -1
