# src/modules/user/user_repository.py
from src.common.db import BaseRepository


class UserRepository(BaseRepository):

    def create_user(self, user_name, password_hash, email, phone):
        with self.cursor() as cur:
            cur.execute("INSERT INTO users (user_name, password_hash, email, phone) VALUES (%s,%s,%s,%s)",
                        (user_name, password_hash, email, phone))
            return cur.lastrowid

    def get_user_by_phone(self, phone):
        with self.cursor() as cur:
            cur.execute("SELECT user_id, user_name, password_hash, email, phone FROM users WHERE phone=%s LIMIT 1",
                        (phone,))
            return cur.fetchone()

    def get_user_with_hash(self, user_id):
        with self.cursor() as cur:
            cur.execute("SELECT user_id, user_name, password_hash, email, phone FROM users WHERE user_id=%s",
                        (user_id,))
            return cur.fetchone()

    def view_user_by_id(self, user_id):
        with self.cursor() as cur:
            cur.execute("SELECT user_id, user_name, email, phone FROM users WHERE user_id=%s LIMIT 1", (user_id,))
            return cur.fetchone()

    def update_profile(self, user_id, user_name, email, phone):
        with self.cursor() as cur:
            cur.execute("UPDATE users SET user_name=%s, email=%s, phone=%s WHERE user_id=%s",
                        (user_name, email, phone, user_id))

    def update_password_hash(self, user_id, password_hash):
        with self.cursor() as cur:
            cur.execute("UPDATE users SET password_hash=%s WHERE user_id=%s", (password_hash, user_id))