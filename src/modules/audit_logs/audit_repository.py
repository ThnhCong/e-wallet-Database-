# src/modules/audit_logs/audit_repository.py
"""Audit logs are immutable; writes and reads are exposed through Stored Procedures."""
from src.common.db import BaseRepository


class AuditRepository(BaseRepository):
    def create_audit_log(self, user_id, wallet_id, transaction_id, action):
        rows = self.call("sp_audit_create", (user_id, wallet_id, transaction_id, action))
        return rows[0]["audit_log_id"]

    def list_logs(self, user_id=None, action=None, limit=20):
        return self.call("sp_audit_list", (user_id, action, limit))
