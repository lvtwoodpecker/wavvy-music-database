from __future__ import annotations

from typing import Optional, Dict, Any, List

from sqlalchemy import Integer, String, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.sqlalchemy_engine import Base


class SubscriptionPlan(Base):
    __tablename__ = "SubscriptionPlan"
    __table_args__ = {"schema": "public"}

    plan_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    price_usd: Mapped[float] = mapped_column(Numeric, nullable=False)
    feature_set: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    
    prices = relationship("SubscriptionPlanPrice", back_populates="plan", order_by="desc(SubscriptionPlanPrice.effective_from)")


    price_history: Mapped[List["SubscriptionPlanPrice"]] = relationship(
        "SubscriptionPlanPrice",
        back_populates="plan",
        order_by="SubscriptionPlanPrice.effective_from.desc()",
    )
