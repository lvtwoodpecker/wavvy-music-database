from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.sqlalchemy_engine import Base

class Advertiser(Base):
    __tablename__ = "Advertiser"  # or "advertiser"

    advertiser_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.user_id"), unique=True, nullable=False)

    # Relationship back to User
    user = relationship("User", back_populates="advertiser_profile")

    def __repr__(self):
        return f"<Advertiser(id={self.advertiser_id}, user_id={self.user_id})>"
