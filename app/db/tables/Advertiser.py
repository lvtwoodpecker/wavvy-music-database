
class Advertiser:
    TABLE_NAME = "advertiser"
    USER_ID = "user_id"
    ADVERTISER_ID = "advertiser_id"

    @staticmethod
    def get_table_name() -> str:
        return Advertiser.TABLE_NAME