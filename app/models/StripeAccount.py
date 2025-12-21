from sqlalchemy import Column, BigInteger, Boolean, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship
from app.db.sqlalchemy_engine import Base

class StripeAccount(Base):
    __tablename__ = "StripeAccount"
    __table_args__ = {"schema": "public"} 

    # DB primary key is stripe_id (bigint identity)
    stripe_id = Column(BigInteger, primary_key=True)

    user_id = Column(
        BigInteger,
        ForeignKey("public.User.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    is_default = Column(Boolean, default=True, nullable=False)
    stripe_customer_id = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="stripe_account")

    def __repr__(self):
        return f"<StripeAccount(stripe_id={self.stripe_id}, user_id={self.user_id})>"
