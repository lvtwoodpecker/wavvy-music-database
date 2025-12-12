from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.sqlalchemy_engine import Base

# It inherits from the SQLAlchemy Base class.

class StripeAccount(Base):
    """  
    Model for the StripeAccount table.
    Represents a Stripe account linked to a user.
    
    Attributes:
    - id: Primary key for the StripeAccount.
    - stripe_id: Auto-generated Stripe account ID.
    - user_id: Foreign key linking to the User table.
    - stripe_customer_id: Stripe Customer ID.
    - is_default: Boolean indicating if this is the default account.
    - created_at: Timestamp of account creation.
    
    Relationships:
    - user: One-to-one relationship back to the User model.
    
    """
    __tablename__ = "StripeAccount" 

    id = Column(Integer, primary_key=True, autoincrement=True)
    stripe_id = Column(String, unique=True, nullable=True) # auto-generated Stripe account ID
    user_id = Column(Integer, ForeignKey("User.user_id"), unique=True, nullable=False)
    stripe_customer_id = Column(String, unique=True, nullable=False) # Stripe Customer ID
    is_default = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship back to User
    user = relationship("User", back_populates="stripe_account")

    def __repr__(self):
        return f"<StripeAccount(user_id={self.user_id}, stripe_customer_id='{self.stripe_customer_id}')>"
