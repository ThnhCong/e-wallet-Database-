# src/modules/user/user_service.py
"""Nghiep vu tai khoan: dang ky, dang nhap/xuat, ho so, doi mat khau.
Audit log duoc ghi qua AuditService, trong CUNG giao dich DB voi thao tac."""
from src.common.db import db_transaction
from src.common.errors import ServiceError
from src.common.query_params import DEFAULT_ADMIN_LIMIT, normalize_limit
from src.common.security import hash_password, needs_rehash, verify_password
from src.common.validators import (parse_currency, require_text, validate_email, validate_password, validate_phone)
from src.modules.audit_logs.audit_actions import AuditAction

_PUBLIC_FIELDS = ("user_id", "user_name", "email", "phone")     # khong bao gio tra password_hash


class UserService:

    def __init__(self, user_repository, audit_service, wallet_service=None):
        self.user_repo = user_repository
        self.audit = audit_service
        self.wallet_service = wallet_service      # chi can neu muon tao vi ngay khi dang ky
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
            self.audit.record(user_id, AuditAction.REGISTER)
            if currency and self.wallet_service is not None:
                self.wallet_service.create_in_open_transaction(user_id, currency)
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
            self.audit.record(user["user_id"], AuditAction.LOGIN)
        return {field: user[field] for field in _PUBLIC_FIELDS}

    def logout(self, user_id):
        with db_transaction(self.conn, "Logout"):
            self.audit.record(user_id, AuditAction.LOGOUT)

    def view_user_by_id(self, user_id):
        with db_transaction(self.conn, "View user"):
            return self.user_repo.view_user_by_id(user_id)

    def update_profile(self, user_id, user_name=None, email=None, phone=None):
        """Truong bo trong = giu nguyen."""
        with db_transaction(self.conn, "Update profile"):
            current = self.user_repo.view_user_by_id(user_id)
            if current is None:
                raise ServiceError("USER_NOT_FOUND", "The user does not exist.")
            name = require_text(user_name, "Name", 100) if user_name else current["user_name"]
            mail = validate_email(email) if email else current["email"]
            tel = validate_phone(phone) if phone else current["phone"]
            self.user_repo.update_profile(user_id, name, mail, tel)
            self.audit.record(user_id, AuditAction.UPDATE_PROFILE)
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
            self.audit.record(user_id, AuditAction.CHANGE_PASSWORD)

    # ---------------------------------------------------------------- quan tri
    def list_users(self, limit=DEFAULT_ADMIN_LIMIT):
        limit = normalize_limit(limit)
        with db_transaction(self.conn, "View users"):
            return self.user_repo.list_users(limit)