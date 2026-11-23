# src/modules/statistics/statistics_service.py
"""Business statistics produced by stored procedures (user report, bank report, system overview)."""
from src.common.db import db_transaction
from src.common.errors import ServiceError
from src.common.validators import parse_optional_date


class StatisticsService:
    def __init__(self, statistics_repository):
        self.repo = statistics_repository
        self.conn = statistics_repository.conn

    def my_statistics(self, user_id, date_from=None, date_to=None):
        date_from = parse_optional_date(date_from, "From date")
        date_to = parse_optional_date(date_to, "To date")
        if date_from and date_to and date_from > date_to:
            raise ServiceError("DATE_RANGE", "The 'from' date must not be after the 'to' date.")
        with db_transaction(self.conn, "View statistics"):
            return self.repo.user_statistics(user_id, date_from, date_to)
