class UserController:

    def __init__(self, user_service):
        self.user_service = user_service

    def register(self, user_name, password, email, phone):
        """
        Nhận thông tin từ UI/main, gọi Service xử lý đăng ký tài khoản.
        """
        return self.user_service.register(
            user_name=user_name,
            password=password,
            email=email,
            phone=phone
        )