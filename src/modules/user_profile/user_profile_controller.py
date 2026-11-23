# src/modules/user_profile/user_profile_controller.py
class UserProfileController:
    def __init__(self, profile_service):
        self.profile_service = profile_service

    def get_profile(self, user_id):
        return self.profile_service.get_profile(user_id)

    def save_profile(self, user_id, age, sex, address, job, country):
        return self.profile_service.save_profile(user_id, age, sex, address, job, country)
