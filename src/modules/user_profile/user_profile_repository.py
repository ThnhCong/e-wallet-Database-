# src/modules/user_profile/user_profile_repository.py
from src.common.db import BaseRepository


class UserProfileRepository(BaseRepository):
    def get_profile(self, user_id):
        rows = self.call("sp_user_profile_get", (user_id,))
        return rows[0] if rows else None

    def save_profile(self, user_id, date_of_birth, age, sex, address, job, country):
        """Create the profile the first time, update it afterwards. Returns (profile_id, created)."""
        rows = self.call("sp_user_profile_save", (user_id, date_of_birth, age, sex, address, job, country))
        return rows[0]["user_profile_id"], bool(rows[0]["created"])

    def list_profiles_for_admin(self, search, sex, country, sort_by, sort_order, limit, offset):
        """Return the requested page and its filtered total.

        The procedure deliberately returns one sentinel row when the page is
        empty; the service removes that row while retaining total_count.
        """
        return self.call(
            "sp_admin_list_user_profiles",
            (search, sex, country, sort_by, sort_order, limit, offset),
        )
