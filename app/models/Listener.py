from sqlalchemy import Boolean, Column, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.sqlalchemy_engine import Base

class Listener(Base):
    __tablename__ = "Listener"
    __table_args__ = {"schema": "public"}

    listener_id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(
        BigInteger,
        ForeignKey("public.User.user_id", ondelete="CASCADE"), 
        unique=True,
        nullable=False,
    )
    ad_free = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="listener_profile")

    def __repr__(self):
        return f"<Listener(id={self.listener_id}, user_id={self.user_id})>"
