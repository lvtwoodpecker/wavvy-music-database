from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Text,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.sqlalchemy_engine import Base


class CompetitorSubscriptionPriceSnapshot(Base):
    __tablename__ = "competitorsubscriptionpricesnapshot"
    __table_args__ = (
        CheckConstraint("price >= 0"),
        CheckConstraint("promo_price IS NULL OR promo_price >= 0"),
        Index("idx_competitor_price_snapshot", "competitor_plan_id", "observed_at"),
        {"schema": "public"},
    )

    snapshot_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    competitor_plan_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "public.competitorsubscriptionplan.competitor_plan_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    country_code: Mapped[Optional[str]] = mapped_column(Text)
    currency_code: Mapped[str] = mapped_column(Text, server_default="USD")

    price: Mapped[float]

    promo_label: Mapped[Optional[str]] = mapped_column(Text)
    promo_price: Mapped[Optional[float]]
    promo_ends_at: Mapped[Optional[datetime]]

    source: Mapped[Optional[str]] = mapped_column(Text)
    source_url: Mapped[Optional[str]] = mapped_column(Text)

    plan = relationship("CompetitorSubscriptionPlan", back_populates="price_snapshots")
