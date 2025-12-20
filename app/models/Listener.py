from sqlalchemy import Boolean, Column, Integer, ForeignKey, UUID
from sqlalchemy.orm import relationship
from app.db.sqlalchemy_engine import Base

# It inherits from the SQLAlchemy Base class.

class Listener(Base):
    """
    Model for the Listener table.
    Represents a listener profile linked to a user.
    
    Attributes:
    - listener_id: Primary key for the Listener (UUID).
    - user_id: Foreign key linking to the User table (bigint).
    
    Relationships:
    - user: One-to-one relationship back to the User model.
    """
    __tablename__ = "Listener"  # or "listener"

    listener_id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(Integer, ForeignKey("User.user_id"), unique=True, nullable=False)
    ad_free = Column(Boolean, default=False)  # false by default
    
    # Relationship back to User
    user = relationship("User", back_populates="listener_profile")

    def __repr__(self):
        return f"<Listener(id={self.listener_id}, user_id={self.user_id})>"
