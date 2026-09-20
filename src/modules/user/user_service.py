# src/modules/user/user_service.py
import hashlib
import re


class UserService:

    def __init__(self, user_repository):
        self.user_repo = user_repository

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(
            password.encode("utf-8")
        ).hexdigest()

    def register(self, user_name, password, email, phone):

        if not password or len(password) < 6:
            raise ValueError(
                "Mật khẩu phải có tối thiểu 6 ký tự."
            )

        password_hash = self._hash_password(password)

        """Check email format, email must have a format like ...@....com"""
        if not re.match(r"^[^@\s]+@[^@\s]+\.com$", email):
            raise ValueError("Email must be like: sth@sth.com")

        return self.user_repo.register(
            user_name,
            password_hash,
            email,
            phone
        )

    def login(self, phone_input, password_input):
        password_hash = self._hash_password(password_input)

        if self.user_repo.login(phone_input, password_hash):
            print("Login successfully")
            return True

        else:
            print("Your phone or your password is wrong!")
            return False

    def view_user_by_id(self, user_id):
        return self.user_repo.view_user_by_id(user_id)