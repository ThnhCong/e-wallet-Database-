# src/modules/admin/admin_repository.py
"""Chi chua SQL RIENG cua quan tri. Cac truy van ve vi / giao dich / audit log dung lai repository san co
(WalletRepository, TransactionRepository, AuditRepository), khong viet lai SQL.
Khong bao gio tra password_hash."""
from src.common.db import BaseRepository


class AdminRepository(BaseRepository):

    def get_role(self, user_id):
        """Vai tro cua user ('user' / 'admin'); None neu user khong ton tai."""
        with self.cursor() as cur:
            cur.execute("SELECT role FROM users WHERE user_id=%s", (user_id,))
            row = cur.fetchone()
            return row["role"] if row else None

    def list_users(self, limit=50):
        """Moi user kem vai tro va so vi dang so huu."""
        with self.cursor() as cur:
            cur.execute("SELECT u.user_id, u.user_name, u.email, u.phone, u.role, COUNT(w.wallet_id) AS wallet_count "
                        "FROM users u LEFT JOIN wallets w ON w.user_id = u.user_id "
                        "GROUP BY u.user_id, u.user_name, u.email, u.phone, u.role "
                        "ORDER BY u.user_id LIMIT %s", (limit,))
            return cur.fetchall()
