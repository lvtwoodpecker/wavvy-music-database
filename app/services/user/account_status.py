
from multiprocessing.connection import Client
from app.db.tables import User
from app.db.tables.Listener import Listener
from app.db.tables.Advertiser import Advertiser

class UserStatusService:
    
    def get_user_status_by_id(
        self,
        sb: Client,
        user_id: int) -> str:
        """Helper function to get a user's status by their ID."""
        print(f"Fetching user status for ID: {user_id}")
        try:
            response = (
                sb
                .table(User.TABLE_NAME)
                .select(User.STATUS)
                .eq(User.USER_ID, user_id)
                .execute()
            )
            if response.data:
                return response.data[0].get(User.STATUS)
            else:
                raise RuntimeError(f"User with ID {user_id} not found")
        except Exception as e:
            print(f"Error fetching user status with ID {user_id}: {e}")
            raise RuntimeError("Failed to fetch user status")

    def update_user_status_by_id(
        self,
        sb: Client,
        user_id: int,
        new_status: str) -> None:
        """Helper function to update a user's status by their ID."""
        print(f"Updating user status for ID: {user_id} to {new_status}")
        try:
            response = (
                sb
                .table(User.TABLE_NAME)
                .update({User.STATUS: new_status})
                .eq(User.USER_ID, user_id)
                .execute()
            )
            
            return {"result": response}
        except Exception as e:
            print(f"Error updating user status with ID {user_id}: {e}")
            raise RuntimeError("Failed to update user status")
        
        
    def set_user_inactive_by_id(
        self,
        sb: Client,
        user_id: int) -> None:
        """Sets a user's status to inactive by their ID."""
        
        return self.update_user_status_by_id(sb, user_id, "inactive")
    
    def set_user_active_by_id(
        self,
        sb: Client,
        user_id: int) -> None:
        """Sets a user's status to active by their ID."""
        
        return self.update_user_status_by_id(sb, user_id, "active")
    
    def set_user_banned_by_id(
        self,
        sb: Client,
        user_id: int) -> None:
        """Sets a user's status to banned by their ID."""
        
        return self.update_user_status_by_id(sb, user_id, "banned")
    
    def set_user_suspended_by_id(
        self,
        sb: Client,
        user_id: int) -> None:
        """Sets a user's status to suspended by their ID."""
        
        return self.update_user_status_by_id(sb, user_id, "suspended")
    
    def delete_user_by_id(
        self,
        sb: Client,
        user_id: int) -> None:
        """Deletes a user from the database by their ID."""
        print(f"Deleting user with ID: {user_id}")
        role = (
            sb
            .table(User.TABLE_NAME)
            .select(User.ROLE)
            .eq(User.USER_ID, user_id)
            .execute()
        ).data[0].get(User.ROLE)
        
        # First delete from role-specific table
        if role == "listener":
            role_table = Listener.TABLE_NAME
        elif role == "advertiser":
            role_table = Advertiser.TABLE_NAME
        else:
            raise RuntimeError(f"Unknown role '{role}' for user ID {user_id}")
        
        # Delete from role-specific table first
        sucess_msg = ""
        try:
            response = (
                sb
                .table(role_table)
                .delete()
                .eq(User.USER_ID, user_id)
                .execute()
            )
            sucess_msg = "Role-specific user data deleted successfully."
        except Exception as e:
            print(f"Error deleting user with ID {user_id}: {e}")
            raise RuntimeError("Failed to delete user")
        
        # Then delete from User table
        try:
            response = (
                sb
                .table(User.TABLE_NAME)
                .delete()
                .eq(User.USER_ID, user_id)
                .execute()
            )
            sucess_msg += " User base data deleted successfully."
        except Exception as e:
            print(f"Error deleting user with ID {user_id}: {e}")
            raise RuntimeError("Failed to delete user")
        
        # Return some indication of success
        return {"result": sucess_msg}