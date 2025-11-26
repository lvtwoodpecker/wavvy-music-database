
class Listener:
    TABLE_NAME = "listener"
    USER_ID = "user_id"
    LISTENER_ID = "listener_id"

    @staticmethod
    def get_table_name() -> str:
        return Listener.TABLE_NAME