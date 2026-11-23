# src/modules/statistics/statistics_repository.py
from src.common.db import BaseRepository


class StatisticsRepository(BaseRepository):
    def user_statistics(self, user_id, date_from, date_to):
        return self.call("sp_user_statistics", (user_id, date_from, date_to))

    def bank_statistics(self):
        return self.call("sp_bank_statistics")

    def system_statistics(self):
        rows = self.call("sp_admin_system_statistics")
        return rows[0] if rows else {}
