# src/modules/user/user_service.py
import hashlib


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

        return self.user_repo.register(
            user_name,
            password_hash,
            email,
            phone
        )
