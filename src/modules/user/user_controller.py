# src/modules/user/user_controller.py
class UserController:

    def __init__(self, user_service):
        self.user_service = user_service

    def register(self, user_name, password, email, phone, currency=None):
        return self.user_service.register(user_name, password, email, phone, currency)

    def login(self, phone_input, password_input):
        return self.user_service.login(phone_input, password_input)

    def logout(self, user_id):
        return self.user_service.logout(user_id)

    def get_user_by_id(self, user_id):
        return self.user_service.view_user_by_id(user_id)

    def update_profile(self, user_id, user_name=None, email=None, phone=None):
        return self.user_service.update_profile(user_id, user_name, email, phone)

    def change_password(self, user_id, old_password, new_password):
        return self.user_service.change_password(user_id, old_password, new_password)

    def get_activity(self, user_id, limit=20):
        return self.user_service.get_activity(user_id, limit)