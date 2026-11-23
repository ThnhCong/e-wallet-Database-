# src/modules/statistics/statistics_controller.py
class StatisticsController:
    def __init__(self, statistics_service):
        self.statistics_service = statistics_service

    def my_statistics(self, user_id, date_from=None, date_to=None):
        return self.statistics_service.my_statistics(user_id, date_from, date_to)
