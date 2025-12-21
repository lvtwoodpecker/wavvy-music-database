from typing import Callable, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.User import User
from app.models.Listener import Listener
from app.models.Advertiser import Advertiser

SessionFactory = Callable[[], Session]


class UserStatusService:
    """Service for managing user status and deletion using SQLAlchemy ORM."""

    def __init__(self, db_session_factory: SessionFactory) -> None:
        self._db_session_factory = db_session_factory

    def _get_session(self) -> Session:
        return self._db_session_factory()

    # ---------- Status helpers ----------

    def get_user_status_by_id(self, user_id: int) -> str:
        """Get a user's status by their ID."""
        print(f"Fetching user status for ID: {user_id}")
        db = self._get_session()
        try:
            user = db.query(User).filter(User.user_id == user_id).one_or_none()
            if not user:
                raise RuntimeError(f"User with ID {user_id} not found")
            return user.status
        except Exception as e:
            print(f"Error fetching user status with ID {user_id}: {e}")
            raise RuntimeError("Failed to fetch user status")
        finally:
            db.close()

    def update_user_status_by_id(
        self,
        user_id: int,
        new_status: str,
    ) -> Dict[str, Any]:
        """Update a user's status by their ID."""
        print(f"Updating user status for ID: {user_id} to {new_status}")
        db = self._get_session()
        try:
            user = db.query(User).filter(User.user_id == user_id).one_or_none()
            if not user:
                raise RuntimeError(f"User with ID {user_id} not found")

            user.status = new_status
            db.commit()
            db.refresh(user)
            return {
                "user_id": user.user_id,
                "status": user.status,
            }
        except Exception as e:
            db.rollback()
            print(f"Error updating user status with ID {user_id}: {e}")
            raise RuntimeError("Failed to update user status")
        finally:
            db.close()

    # convenience wrappers

    def set_user_inactive_by_id(self, user_id: int) -> Dict[str, Any]:
        return self.update_user_status_by_id(user_id, "inactive")

    def set_user_active_by_id(self, user_id: int) -> Dict[str, Any]:
        return self.update_user_status_by_id(user_id, "active")

    def set_user_banned_by_id(self, user_id: int) -> Dict[str, Any]:
        return self.update_user_status_by_id(user_id, "banned")

    def set_user_suspended_by_id(self, user_id: int) -> Dict[str, Any]:
        return self.update_user_status_by_id(user_id, "suspended")

    # ---------- Deletion ----------

    def delete_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """
        Deletes a user and their role-specific record (Listener/Advertiser).
        """
        print(f"Deleting user with ID: {user_id}")
        db = self._get_session()
        try:
            user = db.query(User).filter(User.user_id == user_id).one_or_none()
            if not user:
                raise RuntimeError(f"User with ID {user_id} not found")

            # Get role as string even if it's an Enum
            role_value = None
            if hasattr(user.role, "value"):  # Enum case
                role_value = user.role.value
            else:
                role_value = user.role

            # Delete from role-specific table first (if present)
            success_msg = ""

            if role_value == "user":
                db.query(Listener).filter(Listener.user_id == user_id).delete(
                    synchronize_session=False
                )
                success_msg = "Listener data deleted successfully."
                
                db.query(Advertiser).filter(Advertiser.user_id == user_id).delete(
                    synchronize_session=False
                )
                success_msg = "Advertiser data deleted successfully."
                
            elif role_value == "admin":
                # Admins may not have role-specific records
                success_msg = "No role-specific data to delete for admin."
            else:
                raise RuntimeError(f"Unknown role '{role_value}' for user ID {user_id}")
            
            # Then delete from User table
            db.delete(user)
            db.commit()
            success_msg += " User base data deleted successfully."

            return {"result": success_msg}

        except Exception as e:
            db.rollback()
            print(f"Error deleting user with ID {user_id}: {e}")
            raise RuntimeError("Failed to delete user")
        finally:
            db.close()
