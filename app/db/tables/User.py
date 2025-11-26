
class User:
    TABLE_NAME = "User"
    
    USER_ID = "user_id"
    EMAIL = "email"
    USERNAME = "username"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    PASSWORD_HASH = "password_hash"
    COUNTRY = "country"
    ROLE = "role"
    STATUS = "status"
    
    ROLE_LISTENER = "listener"
    ROLE_ADVERTISER = "advertiser"
    
    @staticmethod
    def get_table_name() -> str:
        return User.TABLE_NAME
    
    @staticmethod
    def get_columns() -> list:
        return [
            User.USER_ID,
            User.EMAIL,
            User.USERNAME,
            User.FIRST_NAME,
            User.LAST_NAME,
            User.PASSWORD_HASH,
            User.COUNTRY,
            User.ROLE,
        ]
        
    @staticmethod
    def get_roles() -> list:
        return [
            User.ROLE_LISTENER,
            User.ROLE_ADVERTISER,
        ]
        
    @staticmethod
    def get_primary_key() -> str:
        return User.USER_ID
    
    @staticmethod
    def get_unique_columns() -> list:
        return [
            User.EMAIL,
            User.USERNAME,
        ]
        