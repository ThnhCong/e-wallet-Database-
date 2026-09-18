# src/modules/users/user_service.py
import bcrypt

class UserService:
    def __init__(self, user_repository):
        self.user_repo = user_repository

    def register_user(self, user_name, plain_password, email, phone):
        """
        Xử lý mã hóa mật khẩu và gọi Repository để lưu dữ liệu
        """
        # 1. Mã hóa mật khẩu thô
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')

        # 2. Gọi UserRepository để insert vào MySQL
        user_id = self.user_repo.register(
            user_name=user_name,
            password_hash=password_hash,
            email=email,
            phone=phone
        )
        return user_id