# src/modules/audit_logs/audit_repository.py
"""Chi chua SQL cua bang audit_logs. Bang nay bat bien (trigger chan UPDATE/DELETE)
nen repository chi co INSERT va SELECT."""
from src.common.db import BaseRepository

_COLUMNS = "audit_log_id, user_id, wallet_id, transaction_id, action, created_at"


class AuditRepository(BaseRepository):

    def create_audit_log(self, user_id, wallet_id, transaction_id, action):
        with self.cursor() as cur:
            cur.execute("INSERT INTO audit_logs (user_id, wallet_id, transaction_id, action) "
                        "VALUES (%s,%s,%s,%s)", (user_id, wallet_id, transaction_id, action))
            return cur.lastrowid

    def list_logs(self, user_id=None, action=None, limit=20):
        """Moi nhat truoc. user_id / action la bo loc tuy chon (None = khong loc)."""
        conditions, params = [], []
        if user_id is not None:
            conditions.append("user_id=%s")
            params.append(user_id)
        if action:
            conditions.append("action=%s")
            params.append(action)

        sql = f"SELECT {_COLUMNS} FROM audit_logs"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at DESC, audit_log_id DESC LIMIT %s"
        params.append(limit)

        with self.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()