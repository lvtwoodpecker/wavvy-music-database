from __future__ import annotations

from typing import Optional
from sqlalchemy import (
    BigInteger,
    Numeric,
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    Computed,
)
from sqlalchemy.dialects.postgresql import TSTZRANGE
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.base import Base


class SubscriptionPlanPrice(Base):
    """
    Price history for SubscriptionPlan.

    Design:
    - Insert a new row with effective_to = NULL to set a new "current" price.
    - Trigger closes the previous open-ended row (effective_to) automatically.
    - Exclusion constraint prevents overlapping ranges (DB-enforced correctness).
    """
    __tablename__ = "subscriptionplanprice"
    __table_args__ = (
        CheckConstraint("price >= 0", name="subscriptionplanprice_price_nonnegative"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="subscriptionplanprice_effective_window_valid",
        ),
        # Helpful indexes for "current price" lookups and history browsing
        Index(
            "idx_plan_price_lookup_current",
            "plan_id", "country_code", "currency_code", "effective_from",
            postgresql_using="btree",
        ),
        Index(
            "idx_plan_price_effective",
            "plan_id", "effective_from",
            postgresql_using="btree",
        ),
        {"schema": "public"},
    )

    plan_price_id: Mapped[int] = mapped_column(primary_key=True)  # bigserial in DB
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("public.SubscriptionPlan.plan_id", ondelete="CASCADE"),
        nullable=False,
    )

    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)

    price: Mapped[float] = mapped_column(Numeric, nullable=False)

    effective_from: Mapped["datetime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    effective_to: Mapped[Optional["datetime"]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    changed_by_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("public.User.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    change_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Computed range column (matches your DDL)
    price_range: Mapped[object] = mapped_column(
        TSTZRANGE,
        Computed("tstzrange(effective_from, COALESCE(effective_to, 'infinity'))", persisted=True),
        nullable=False,
    )

    # Relationships
    plan = relationship("SubscriptionPlan", back_populates="price_history")
    changed_by_user = relationship("User", foreign_keys=[changed_by_user_id])
