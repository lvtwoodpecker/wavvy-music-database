from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional, Sequence

from sqlalchemy import select, desc, and_, or_
from sqlalchemy.orm import Session

from app.models.SubscriptionPlanPrice import SubscriptionPlanPrice
from app.services.pricing.price_key import PriceKey

SessionFactory = Callable[[], Session]


class SubscriptionPricingRepo:
    def __init__(self, session: Session) -> None:
        self.session = session
    
    def get_current_price_row(self, key: PriceKey) -> Optional[SubscriptionPlanPrice]:
        """
        Returns the most recent row that is currently effective.
        """
        now = datetime.now().astimezone()

        stmt = (
            select(SubscriptionPlanPrice)
            .where(
                SubscriptionPlanPrice.plan_id == key.plan_id,
                SubscriptionPlanPrice.currency_code == key.currency_code,
                # Treat NULL country_code as "global" pricing bucket
                (SubscriptionPlanPrice.country_code.is_(None) if key.country_code is None
                    else SubscriptionPlanPrice.country_code == key.country_code),
                SubscriptionPlanPrice.effective_from <= now,
                or_(
                    SubscriptionPlanPrice.effective_to.is_(None),
                    SubscriptionPlanPrice.effective_to > now,
                ),
            )
            .order_by(desc(SubscriptionPlanPrice.effective_from))
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_price_history(self, key: PriceKey, limit: int = 100) -> Sequence[SubscriptionPlanPrice]:
        stmt = (
            select(SubscriptionPlanPrice)
            .where(
                SubscriptionPlanPrice.plan_id == key.plan_id,
                SubscriptionPlanPrice.currency_code == key.currency_code,
                (SubscriptionPlanPrice.country_code.is_(None) if key.country_code is None
                    else SubscriptionPlanPrice.country_code == key.country_code),
            )
            .order_by(desc(SubscriptionPlanPrice.effective_from))
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()

    def insert_new_price(
        self,
        key: PriceKey,
        new_price: float,
        changed_by_user_id: Optional[int] = None,
        change_reason: Optional[str] = None,
        effective_from: Optional[datetime] = None,
    ) -> SubscriptionPlanPrice:
        """
        Inserts a new open-ended price row.

        DB trigger should close the previous open-ended row for same (plan,country,currency).
        DB exclusion constraint prevents overlapping windows.
        """
        row = SubscriptionPlanPrice(
            plan_id=key.plan_id,
            country_code=key.country_code,
            currency_code=key.currency_code,
            price=new_price,
            effective_from=effective_from or datetime.now().astimezone(),
            effective_to=None,
            changed_by_user_id=changed_by_user_id,
            change_reason=change_reason,
        )
        self.session.add(row)
        return row
