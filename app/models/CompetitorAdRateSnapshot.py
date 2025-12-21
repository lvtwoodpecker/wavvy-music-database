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


class CompetitorAdRateSnapshot(Base):
    __tablename__ = "competitoradratesnapshot"
    __table_args__ = (
        CheckConstraint("rate >= 0"),
        CheckConstraint("min_spend IS NULL OR min_spend >= 0"),
        Index("idx_ad_rate_snapshot", "competitor_ad_product_id", "observed_at"),
        {"schema": "public"},
    )

    ad_rate_snapshot_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    competitor_ad_product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "public.competitoradproduct.competitor_ad_product_id",
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

    rate: Mapped[float]
    min_spend: Mapped[Optional[float]]

    targeting_notes: Mapped[Optional[str]] = mapped_column(Text)
    inventory_notes: Mapped[Optional[str]] = mapped_column(Text)

    source: Mapped[Optional[str]] = mapped_column(Text)
    source_url: Mapped[Optional[str]] = mapped_column(Text)

    ad_product = relationship("CompetitorAdProduct", back_populates="rate_snapshots")
