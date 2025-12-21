from __future__ import annotations
from typing import Optional, Dict, Any, List

from sqlalchemy import BigInteger, Text, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.sqlalchemy_engine import Base


class CompetitorSubscriptionPlan(Base):
    __tablename__ = "competitorsubscriptionplan"
    __table_args__ = (
        CheckConstraint(
            "billing_period = ANY (ARRAY['monthly','yearly','weekly','other'])"
        ),
        Index("idx_competitor_subscription_plan", "competitor_id"),
        {"schema": "public"},
    )

    competitor_plan_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    competitor_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("public.competitor.competitor_id", ondelete="CASCADE"),
        nullable=False,
    )

    plan_name: Mapped[str] = mapped_column(Text, nullable=False)
    billing_period: Mapped[str] = mapped_column(Text, nullable=False)

    is_student: Mapped[bool] = mapped_column(server_default="false")
    is_family: Mapped[bool] = mapped_column(server_default="false")
    max_accounts: Mapped[Optional[int]]

    feature_set: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)

    competitor = relationship("Competitor", back_populates="subscription_plans")

    price_snapshots: Mapped[List["CompetitorSubscriptionPriceSnapshot"]] = relationship(
        "CompetitorSubscriptionPriceSnapshot",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<CompetitorSubscriptionPlan(competitor_plan_id={self.competitor_plan_id}, plan_name='{self.plan_name}')>"