from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from app.db.sqlalchemy_engine import Base
import enum

# It inherits from the SQLAlchemy Base class.

class UserRole(enum.Enum):
    listener = "listener"
    advertiser = "advertiser"

class User(Base):
    """
    Model for the User table.
    Represents a user in the system.
    
    Attributes:
    - user_id: Primary key for the User.
    - email: Unique email address of the user.
    - username: Unique username of the user.
    - first_name: First name of the user.
    - last_name: Last name of the user.
    - password_hash: Hashed password for authentication.
    - country: Country of the user.
    - role: Role of the user (listener or advertiser).
    - status: Account status (e.g., active, inactive).
    
    Relationships:
    - listener_profile: One-to-one relationship to Listener profile.
    - advertiser_profile: One-to-one relationship to Advertiser profile.
    - stripe_account: One-to-one relationship to StripeAccount.
    - playlists: One-to-many relationship to Playlists owned by the user.
    
    """
    __tablename__ = "User"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    country = Column(String, nullable=True)
    role = Column(Enum(UserRole), nullable=False)
    status = Column(String, default="active")

    # one-to-one relationship from User --> Listener
    listener_profile = relationship(
        "Listener",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # one-to-one relationship from User --> Advertiser
    advertiser_profile = relationship(
        "Advertiser",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    # one-to-one relationship from User --> StripeAccount
    stripe_account = relationship(
        "StripeAccount",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
        
    # one-to-many relationship from User --> Playlist
    playlists = relationship("Playlist", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}', role='{self.role.value}')>"
