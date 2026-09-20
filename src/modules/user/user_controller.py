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

    def login(self, phone_input, password_input):
        """
        Nhận thông tin từ UI/main, gọi Service xử lý đăng nhập tài khoản.
        """

        return self.user_service.login(phone_input, password_input)

    def get_user_by_id(self, user_id):
        return self.user_service.view_user_by_id(user_id)