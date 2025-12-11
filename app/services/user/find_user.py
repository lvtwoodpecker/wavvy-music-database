from typing import Optional, Callable
from sqlalchemy.orm import Session

from app.models.User import User          # ORM models, not table-constants
from app.models.Listener import Listener
from app.models.Advertiser import Advertiser

# Type alias for "give me a Session when I call you"
SessionFactory = Callable[[], Session]


class FindUserService:
    """Service for retrieving user information using SQLAlchemy ORM."""

    def __init__(self, db_session_factory: SessionFactory) -> None:
        self._db_session_factory = db_session_factory

    def _get_session(self) -> Session:
        return self._db_session_factory()

    # ---------- User lookups ----------

    def get_user_by_email(self, email: str) -> Optional[User]:
        db = self._get_session()
        try:
            return db.query(User).filter(User.email == email).one_or_none()
        except Exception as e:
            print(f"[User Service] Error fetching user by email {email}: {e}")
            raise RuntimeError("Failed to fetch user by email")
        finally:
            db.close()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        db = self._get_session()
        try:
            return db.query(User).filter(User.user_id == user_id).one_or_none()
        except Exception as e:
            print(f"[User Service] Error fetching user by ID {user_id}: {e}")
            raise RuntimeError("Failed to fetch user by ID")
        finally:
            db.close()

    def get_user_by_username(self, username: str) -> Optional[User]:
        db = self._get_session()
        try:
            return db.query(User).filter(User.username == username).one_or_none()
        except Exception as e:
            print(f"[User Service] Error fetching user by username {username}: {e}")
            raise RuntimeError("Failed to fetch user by username")
        finally:
            db.close()

    def get_user_role_by_id(self, user_id: int) -> Optional[str]:
        """
        Returns the user's role as a string, or None.
        Assumes User.role is either a string column or an Enum (UserRole).
        """
        db = self._get_session()
        try:
            user = db.query(User).filter(User.user_id == user_id).one_or_none()
        except Exception as e:
            print(f"[User Service] Error fetching user role by ID {user_id}: {e}")
            raise RuntimeError("Failed to fetch user role by ID")
        finally:
            db.close()

        if user is None:
            return None

        # If role is an Enum, return its value; if it's a string column, just return it
        try:
            return user.role.value  # Enum case
        except AttributeError:
            return user.role        # String case

    # ---------- Listener / Advertiser lookups ----------

    def get_listener_by_user_id(self, user_id: int) -> Optional[Listener]:
        db = self._get_session()
        try:
            return (
                db.query(Listener)
                .filter(Listener.user_id == user_id)
                .one_or_none()
            )
        except Exception as e:
            print(f"[User Service] Error fetching listener by user ID {user_id}: {e}")
            raise RuntimeError("Failed to fetch listener by user ID")
        finally:
            db.close()

    def get_advertiser_by_user_id(self, user_id: int) -> Optional[Advertiser]:
        db = self._get_session()
        try:
            return (
                db.query(Advertiser)
                .filter(Advertiser.user_id == user_id)
                .one_or_none()
            )
        except Exception as e:
            print(f"[User Service] Error fetching advertiser by user ID {user_id}: {e}")
            raise RuntimeError("Failed to fetch advertiser by user ID")
        finally:
            db.close()
