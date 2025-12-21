from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import BigInteger
from app.db.sqlalchemy_engine import Base


class PasswordResetToken(Base):
    __tablename__ = "PasswordResetToken"
    __table_args__ = {"schema": "public"}  # ✅

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        BigInteger,  # ✅ match public.User.user_id
        ForeignKey("public.User.user_id", ondelete="CASCADE"),  # ✅ schema-qualified
        nullable=False,
        index=True,
    )

    token = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=False), nullable=True)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())

    user = relationship("User", back_populates="password_reset_tokens")
