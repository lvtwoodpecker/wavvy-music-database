from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.sqlalchemy_engine import Base


class SubscriptionHistory(Base):
    __tablename__ = "SubscriptionHistory"
    __table_args__ = {"schema": "public"} 

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        BigInteger, 
        ForeignKey("public.User.user_id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
    )

    plan_id = Column(Integer, nullable=True)
    plan_name = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")  # active | canceled | expired

    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Prefer explicit back_populates over backref (cleaner, less magic)
    user = relationship("User", back_populates="subscription_history")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan_id": self.plan_id,
            "plan_name": self.plan_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "canceled_at": self.canceled_at.isoformat() if self.canceled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
