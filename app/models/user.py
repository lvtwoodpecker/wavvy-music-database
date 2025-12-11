from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from app.db.sqlalchemy_engine import Base
import enum

class UserRole(enum.Enum):
    listener = "listener"
    advertiser = "advertiser"

class User(Base):
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
