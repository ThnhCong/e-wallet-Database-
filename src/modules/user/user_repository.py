# src/modules/user/user_repository.py
from src.common.db import BaseRepository


class UserRepository(BaseRepository):
    def create_user(self, user_name, password_hash, email, phone):
        rows = self.call("sp_user_create", (user_name, password_hash, email, phone))
        return rows[0]["user_id"]

    def get_user_by_phone(self, phone):
        rows = self.call("sp_user_get_by_phone", (phone,))
        return rows[0] if rows else None

    def get_user_with_hash(self, user_id):
        rows = self.call("sp_user_get_with_hash", (user_id,))
        return rows[0] if rows else None

    def view_user_by_id(self, user_id):
        rows = self.call("sp_user_get_by_id", (user_id,))
        return rows[0] if rows else None

    def update_profile(self, user_id, user_name, email, phone):
        self.call("sp_user_update_profile", (user_id, user_name, email, phone))

    def update_password_hash(self, user_id, password_hash):
        self.call("sp_user_update_password", (user_id, password_hash))
