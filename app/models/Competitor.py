from __future__ import annotations
from datetime import datetime
from typing import Optional, List

from sqlalchemy import BigInteger, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.sqlalchemy_engine import Base


class Competitor(Base):
    __tablename__ = "competitor"
    __table_args__ = {"schema": "public"}

    competitor_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    website: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    ad_products: Mapped[List["CompetitorAdProduct"]] = relationship(
        "CompetitorAdProduct",
        back_populates="competitor",
        cascade="all, delete-orphan",
    )

    subscription_plans: Mapped[List["CompetitorSubscriptionPlan"]] = relationship(
        "CompetitorSubscriptionPlan",
        back_populates="competitor",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<Competitor(competitor_id={self.competitor_id}, name='{self.name}')>"