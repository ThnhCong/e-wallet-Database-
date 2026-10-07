# src/modules/user/user_service.py
from src.common.db import db_transaction
from src.common.errors import ServiceError
from src.common.security import hash_password, needs_rehash, verify_password
from src.common.validators import (parse_currency, require_text, validate_email, validate_password, validate_phone)


class UserService:

    def __init__(self, user_repository, audit_repository, wallet_repository=None):
        self.user_repo = user_repository
        self.audit_repo = audit_repository
        self.wallet_repo = wallet_repository      # chi can neu muon tao vi ngay khi dang ky
        self.conn = user_repository.conn

    def register(self, user_name, password, email, phone, currency=None):
        """Dang ky (+ vi ban dau tuy chon) + audit trong CUNG 1 giao dich DB. Tra ve user_id."""
        name = require_text(user_name, "Name", 100)
        validate_password(password)
        email = validate_email(email)
        phone = validate_phone(phone)
        currency = parse_currency(currency) if currency else None
        password_hash = hash_password(password)

        with db_transaction(self.conn, "Register"):
            user_id = self.user_repo.create_user(name, password_hash, email, phone)
            self.audit_repo.create_audit_log(user_id, None, None, "REGISTER")
            if currency and self.wallet_repo is not None:
                wallet_id = self.wallet_repo.create_wallet(user_id, currency)
                self.audit_repo.create_audit_log(user_id, wallet_id, None, "CREATE_WALLET")
        return user_id

    def login(self, phone_input, password_input):
        """Tra ve dict user (khong co password_hash). Sai thong tin -> ServiceError('AUTH_FAILED')."""
        phone = validate_phone(phone_input)
        with db_transaction(self.conn, "Login"):
            user = self.user_repo.get_user_by_phone(phone)
            if user is None or not verify_password(password_input or "", user["password_hash"]):
                raise ServiceError("AUTH_FAILED", "Your phone or your password is wrong!")
            if needs_rehash(user["password_hash"]):
                self.user_repo.update_password_hash(user["user_id"], hash_password(password_input))
            self.audit_repo.create_audit_log(user["user_id"], None, None, "LOGIN")
        return {k: user[k] for k in ("user_id", "user_name", "email", "phone")}

    def logout(self, user_id):
        with db_transaction(self.conn, "Logout"):
            self.audit_repo.create_audit_log(user_id, None, None, "LOGOUT")

    def view_user_by_id(self, user_id):
        with db_transaction(self.conn, "View user"):
            return self.user_repo.view_user_by_id(user_id)

    def update_profile(self, user_id, user_name=None, email=None, phone=None):
        """Truong bo trong = giu nguyen."""
        with db_transaction(self.conn, "Update profile"):
            cur = self.user_repo.view_user_by_id(user_id)
            if cur is None:
                raise ServiceError("USER_NOT_FOUND", "The user does not exist.")
            name = require_text(user_name, "Name", 100) if user_name else cur["user_name"]
            mail = validate_email(email) if email else cur["email"]
            tel = validate_phone(phone) if phone else cur["phone"]
            self.user_repo.update_profile(user_id, name, mail, tel)
            self.audit_repo.create_audit_log(user_id, None, None, "UPDATE_PROFILE")
            return self.user_repo.view_user_by_id(user_id)

    def change_password(self, user_id, old_password, new_password):
        validate_password(new_password)
        if old_password == new_password:
            raise ServiceError("PASSWORD_SAME", "The new password must be different from the old one.")
        with db_transaction(self.conn, "Change password"):
            user = self.user_repo.get_user_with_hash(user_id)
            if user is None or not verify_password(old_password or "", user["password_hash"]):
                raise ServiceError("AUTH_FAILED", "The current password is incorrect.")
            self.user_repo.update_password_hash(user_id, hash_password(new_password))
            self.audit_repo.create_audit_log(user_id, None, None, "CHANGE_PASSWORD")

    def get_activity(self, user_id, limit=20):
        with db_transaction(self.conn, "View activity"):
            return self.audit_repo.list_by_user(user_id, limit)