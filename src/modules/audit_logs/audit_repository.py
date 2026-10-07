# src/common/audit_repository.py
from src.common.db import BaseRepository


class AuditRepository(BaseRepository):
    """audit_logs: chi INSERT / SELECT (bang bat bien, trigger chan UPDATE/DELETE).
    12 action hop le: REGISTER LOGIN LOGOUT CHANGE_PASSWORD UPDATE_PROFILE CREATE_WALLET LOCK_WALLET
    UNLOCK_WALLET DEPOSIT WITHDRAW TRANSFER TRANSFER_RECEIVED  (khong co DEBIT / CREDIT)."""

    def create_audit_log(self, user_id, wallet_id, transaction_id, action):
        with self.cursor() as cur:
            cur.execute("INSERT INTO audit_logs (user_id, wallet_id, transaction_id, action) VALUES (%s,%s,%s,%s)",
                        (user_id, wallet_id, transaction_id, action))
            return cur.lastrowid

    def list_by_user(self, user_id, limit=20):
        with self.cursor() as cur:
            cur.execute("SELECT audit_log_id, action, wallet_id, transaction_id, created_at FROM audit_logs "
                        "WHERE user_id=%s ORDER BY audit_log_id DESC LIMIT %s", (user_id, limit))
            return cur.fetchall()