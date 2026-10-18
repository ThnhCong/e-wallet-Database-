# src/modules/audit_logs/audit_service.py
"""Nghiep vu audit log: ghi log (kem kiem tra quy tac Bang 1) va xem log."""
from src.common.db import db_transaction
from src.common.errors import ServiceError
from src.common.query_params import (DEFAULT_ADMIN_LIMIT, DEFAULT_LIMIT, normalize_limit, parse_optional_id)
from src.common.validators import parse_choice
from src.modules.audit_logs.audit_actions import AUDIT_ACTIONS, AUDIT_REFERENCES


class AuditService:

    def __init__(self, audit_repository):
        self.audit_repo = audit_repository
        self.conn = audit_repository.conn

    # ---------------------------------------------------------------- ghi log
    def record(self, user_id, action, wallet_id=None, transaction_id=None):
        """Ghi 1 audit log. KHONG tu mo giao dich: phai goi ben trong db_transaction cua service
        goi no, de log nam cung giao dich voi thao tac (commit/rollback cung nhau)."""
        if user_id is None:
            raise ServiceError("AUDIT_INVALID", "An audit log needs a user.")
        if action not in AUDIT_REFERENCES:
            raise ServiceError("AUDIT_INVALID", f"Unknown audit action: {action}")

        needs_wallet, needs_transaction = AUDIT_REFERENCES[action]
        if (wallet_id is not None) != needs_wallet:
            raise ServiceError("AUDIT_INVALID", f"{action}: wallet_id must be {'set' if needs_wallet else 'empty'}.")
        if (transaction_id is not None) != needs_transaction:
            raise ServiceError("AUDIT_INVALID",
                               f"{action}: transaction_id must be {'set' if needs_transaction else 'empty'}.")

        return self.audit_repo.create_audit_log(user_id, wallet_id, transaction_id, action)

    # ---------------------------------------------------------------- xem log
    def get_user_activity(self, user_id, action=None, limit=DEFAULT_LIMIT):
        """Lich su hoat dong cua chinh nguoi dung."""
        action = parse_choice(action, AUDIT_ACTIONS, "Action")
        limit = normalize_limit(limit)
        with db_transaction(self.conn, "View activity"):
            return self.audit_repo.list_logs(user_id=user_id, action=action, limit=limit)

    def list_logs(self, user_id=None, action=None, limit=DEFAULT_ADMIN_LIMIT):
        """Quan tri: xem log cua moi nguoi dung, loc tuy chon theo user va action."""
        user_id = parse_optional_id(user_id, "User")
        action = parse_choice(action, AUDIT_ACTIONS, "Action")
        limit = normalize_limit(limit)
        with db_transaction(self.conn, "View audit logs"):
            return self.audit_repo.list_logs(user_id=user_id, action=action, limit=limit)