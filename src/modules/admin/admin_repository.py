from src.common.db import BaseRepository

class AdminRepository(BaseRepository):
    def is_admin(self, user_id, admin_accounts):
        rows = self.call("sp_user_get_by_id", (user_id,))
        return bool(rows and str(rows[0].get("phone", "")) in admin_accounts)

    def list_users(self, limit=50):
        return self.call("sp_admin_list_users", (limit,))
