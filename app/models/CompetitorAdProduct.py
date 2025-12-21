from __future__ import annotations
from typing import Optional, List

from sqlalchemy import BigInteger, Text, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.sqlalchemy_engine import Base


class CompetitorAdProduct(Base):
    __tablename__ = "competitoradproduct"
    __table_args__ = (
        CheckConstraint(
            "creative_type = ANY (ARRAY['audio','video','display','other'])"
        ),
        CheckConstraint(
            "buying_model = ANY (ARRAY['CPM','CPC','CPV','FLAT','OTHER'])"
        ),
        Index("idx_competitoradproduct_competitor", "competitor_id"),
        {"schema": "public"},
    )

    competitor_ad_product_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    competitor_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("public.competitor.competitor_id", ondelete="CASCADE"),
        nullable=False,
    )

    product_name: Mapped[str] = mapped_column(Text, nullable=False)
    creative_type: Mapped[Optional[str]] = mapped_column(Text)
    buying_model: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    competitor = relationship("Competitor", back_populates="ad_products")

    rate_snapshots: Mapped[List["CompetitorAdRateSnapshot"]] = relationship(
        "CompetitorAdRateSnapshot",
        back_populates="ad_product",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<CompetitorAdProduct(competitor_ad_product_id={self.competitor_ad_product_id}, product_name='{self.product_name}')>"