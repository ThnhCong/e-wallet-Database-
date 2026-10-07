# src/modules/wallet/wallet_repository.py
"""Chi chua SQL. KHONG co cau lenh nao sua balance / remain_limit_week / limit_week:
viec do la cua trigger khi giao dich chuyen PENDING -> SUCCESS."""
from src.common.db import BaseRepository


class WalletRepository(BaseRepository):

    # ---------------- wallets
    def create_wallet(self, user_id, currency):
        with self.cursor() as cur:
            # chi truyen (user_id, currency): balance=0, status=ACTIVE la DEFAULT; limit_week / remain_limit_week
            # do trigger trg_wallets_before_insert dat theo currency
            cur.execute("INSERT INTO wallets (user_id, currency) VALUES (%s,%s)", (user_id, currency))
            return cur.lastrowid

    def get_wallet_by_id(self, wallet_id):
        with self.cursor() as cur:
            cur.execute("SELECT w.wallet_id, w.user_id, u.user_name, w.balance, w.currency, w.limit_week, "
                        "w.remain_limit_week, w.status, w.created_at "
                        "FROM wallets w INNER JOIN users u ON u.user_id = w.user_id WHERE w.wallet_id=%s",
                        (wallet_id,))
            return cur.fetchone()

    def list_wallets_by_user(self, user_id):
        with self.cursor() as cur:
            cur.execute("SELECT wallet_id, balance, currency, limit_week, remain_limit_week, status, created_at "
                        "FROM wallets WHERE user_id=%s ORDER BY wallet_id", (user_id,))
            return cur.fetchall()

    def lock_wallets(self, *wallet_ids):
        """SELECT ... FOR UPDATE theo thu tu wallet_id TANG DAN (chong deadlock). Tra ve {wallet_id: row}."""
        ids = sorted({i for i in wallet_ids if i is not None})
        placeholders = ",".join(["%s"] * len(ids))
        with self.cursor() as cur:
            cur.execute(f"SELECT wallet_id, user_id, status, currency FROM wallets "
                        f"WHERE wallet_id IN ({placeholders}) ORDER BY wallet_id FOR UPDATE", ids)
            return {r["wallet_id"]: r for r in cur.fetchall()}

    def set_wallet_status(self, wallet_id, status):
        with self.cursor() as cur:
            cur.execute("UPDATE wallets SET status=%s WHERE wallet_id=%s", (status, wallet_id))

    # ---------------- transactions
    def create_transaction(self, sender_id, receiver_id, transaction_type, amount):
        """INSERT luon la PENDING (DEFAULT); trigger BEFORE INSERT kiem tra toan bo luat."""
        with self.cursor() as cur:
            cur.execute("INSERT INTO transactions (sender_id, receiver_id, type, amount) VALUES (%s,%s,%s,%s)",
                        (sender_id, receiver_id, transaction_type, amount))
            return cur.lastrowid

    def mark_transaction_success(self, transaction_id):
        """PENDING -> SUCCESS: trigger AFTER UPDATE kiem tra lai va cap nhat balance + remain_limit_week."""
        with self.cursor() as cur:
            cur.execute("UPDATE transactions SET status='SUCCESS' WHERE transaction_id=%s AND status='PENDING'",
                        (transaction_id,))
            if cur.rowcount != 1:
                raise RuntimeError("Cannot update transaction status.")

    def list_transactions(self, user_id, tx_type=None, status=None, limit=20):
        sql = ("SELECT t.transaction_id, t.type, t.amount, t.status, t.sender_id, t.receiver_id, t.created_at "
               "FROM transactions t "
               "LEFT JOIN wallets s ON s.wallet_id = t.sender_id "
               "LEFT JOIN wallets r ON r.wallet_id = t.receiver_id "
               "WHERE (s.user_id=%s OR r.user_id=%s)")
        params = [user_id, user_id]
        if tx_type:
            sql += " AND t.type=%s"
            params.append(tx_type)
        if status:
            sql += " AND t.status=%s"
            params.append(status)
        sql += " ORDER BY t.created_at DESC, t.transaction_id DESC LIMIT %s"
        params.append(limit)
        with self.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def get_transaction(self, transaction_id):
        with self.cursor() as cur:
            cur.execute("SELECT t.transaction_id, t.type, t.amount, t.status, t.sender_id, t.receiver_id, "
                        "t.created_at, s.user_id AS sender_user_id, r.user_id AS receiver_user_id "
                        "FROM transactions t "
                        "LEFT JOIN wallets s ON s.wallet_id = t.sender_id "
                        "LEFT JOIN wallets r ON r.wallet_id = t.receiver_id "
                        "WHERE t.transaction_id=%s", (transaction_id,))
            return cur.fetchone()