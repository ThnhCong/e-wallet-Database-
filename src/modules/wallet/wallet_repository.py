# src/modules/wallet/wallet_repository.py
"""Chi chua SQL cua bang wallets. KHONG co cau lenh nao sua balance / remain_limit_week / limit_week:
viec do la cua trigger khi giao dich chuyen PENDING -> SUCCESS (xem module transaction)."""
from src.common.db import BaseRepository

_WALLET_WITH_OWNER = ("SELECT w.wallet_id, w.user_id, u.user_name, w.balance, w.currency, w.limit_week, "
                      "w.remain_limit_week, w.status, w.created_at "
                      "FROM wallets w INNER JOIN users u ON u.user_id = w.user_id")


class WalletRepository(BaseRepository):

    def create_wallet(self, user_id, currency):
        with self.cursor() as cur:
            # chi truyen (user_id, currency): balance=0, status=ACTIVE la DEFAULT; limit_week / remain_limit_week
            # do trigger trg_wallets_before_insert dat theo currency
            cur.execute("INSERT INTO wallets (user_id, currency) VALUES (%s,%s)", (user_id, currency))
            return cur.lastrowid

    def get_wallet_by_id(self, wallet_id):
        with self.cursor() as cur:
            cur.execute(f"{_WALLET_WITH_OWNER} WHERE w.wallet_id=%s", (wallet_id,))
            return cur.fetchone()

    def list_wallets_by_user(self, user_id):
        with self.cursor() as cur:
            cur.execute("SELECT wallet_id, balance, currency, limit_week, remain_limit_week, status, created_at "
                        "FROM wallets WHERE user_id=%s ORDER BY wallet_id", (user_id,))
            return cur.fetchall()

    def list_all_wallets(self, user_id=None, limit=50):
        """Quan tri: vi cua moi nguoi dung kem ten chu vi; user_id tuy chon de loc."""
        sql, params = _WALLET_WITH_OWNER, []
        if user_id is not None:
            sql += " WHERE w.user_id=%s"
            params.append(user_id)
        sql += " ORDER BY w.wallet_id LIMIT %s"
        params.append(limit)
        with self.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def lock_wallets(self, *wallet_ids):
        """SELECT ... FOR UPDATE theo thu tu wallet_id TANG DAN (chong deadlock). Tra ve {wallet_id: row}."""
        ids = sorted({i for i in wallet_ids if i is not None})
        if not ids:
            return {}
        placeholders = ",".join(["%s"] * len(ids))
        with self.cursor() as cur:
            cur.execute(f"SELECT wallet_id, user_id, status, currency FROM wallets "
                        f"WHERE wallet_id IN ({placeholders}) ORDER BY wallet_id FOR UPDATE", ids)
            return {r["wallet_id"]: r for r in cur.fetchall()}

    def set_wallet_status(self, wallet_id, status):
        with self.cursor() as cur:
            cur.execute("UPDATE wallets SET status=%s WHERE wallet_id=%s", (status, wallet_id))