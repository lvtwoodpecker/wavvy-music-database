from __future__ import annotations

from typing import Optional, List, Dict, Any
from sqlalchemy import Integer, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.sqlalchemy_engine import Base


class SubscriptionPlan(Base):
    __tablename__ = "SubscriptionPlan"
    __table_args__ = {"schema": "public"}

    plan_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    price_usd: Mapped[float] = mapped_column(Numeric, nullable=False)  # legacy/current simple field
    feature_set: Mapped[Optional[Dict[str, Any]]] = mapped_column(nullable=True)

    # Relationship: all price history rows for this plan
    price_history: Mapped[List["subscriptionplanprice"]] = relationship(
        "subscriptionplanprice",
        back_populates="plan",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="subscriptionplanprice.effective_from.desc()",
    )
