# src/modules/transaction/transaction_repository.py
"""Chi chua SQL cua bang transactions. KHONG sua balance / remain_limit_week:
viec do la cua trigger khi giao dich chuyen PENDING -> SUCCESS."""
from src.common.db import BaseRepository

_LIST_COLUMNS = "t.transaction_id, t.type, t.amount, t.status, t.sender_id, t.receiver_id, t.created_at"
_WALLET_JOINS = ("FROM transactions t "
                 "LEFT JOIN wallets s ON s.wallet_id = t.sender_id "
                 "LEFT JOIN wallets r ON r.wallet_id = t.receiver_id")


class TransactionRepository(BaseRepository):

    def create_transaction(self, sender_id, receiver_id, transaction_type, amount):
        """INSERT luon la PENDING (DEFAULT); trigger BEFORE INSERT kiem tra toan bo luat."""
        with self.cursor() as cur:
            cur.execute("INSERT INTO transactions (sender_id, receiver_id, type, amount) VALUES (%s,%s,%s,%s)",
                        (sender_id, receiver_id, transaction_type, amount))
            return cur.lastrowid

    def mark_transaction_success(self, transaction_id):
        """PENDING -> SUCCESS: trigger AFTER UPDATE kiem tra lai va cap nhat balance + remain_limit_week."""
        self._change_pending_status(transaction_id, "SUCCESS")

    def mark_transaction_failed(self, transaction_id):
        """PENDING -> FAIL: giao dich da luu nhung khong hoan tat duoc; khong thay doi so du."""
        self._change_pending_status(transaction_id, "FAIL")

    def _change_pending_status(self, transaction_id, new_status):
        with self.cursor() as cur:
            cur.execute("UPDATE transactions SET status=%s WHERE transaction_id=%s AND status='PENDING'",
                        (new_status, transaction_id))
            if cur.rowcount != 1:
                raise RuntimeError("Cannot update transaction status.")

    def get_transaction(self, transaction_id):
        with self.cursor() as cur:
            cur.execute(f"SELECT {_LIST_COLUMNS}, s.user_id AS sender_user_id, r.user_id AS receiver_user_id "
                        f"{_WALLET_JOINS} WHERE t.transaction_id=%s", (transaction_id,))
            return cur.fetchone()

    def list_transactions(self, user_id, tx_type=None, status=None, limit=20):
        """Giao dich ma user la nguoi gui HOAC nguoi nhan."""
        return self._list(["(s.user_id=%s OR r.user_id=%s)"], [user_id, user_id], tx_type, status, limit)

    def list_all_transactions(self, tx_type=None, status=None, limit=50):
        """Quan tri: giao dich cua moi nguoi dung."""
        return self._list([], [], tx_type, status, limit)

    def _list(self, conditions, params, tx_type, status, limit):
        conditions, params = list(conditions), list(params)
        if tx_type:
            conditions.append("t.type=%s")
            params.append(tx_type)
        if status:
            conditions.append("t.status=%s")
            params.append(status)

        sql = f"SELECT {_LIST_COLUMNS} {_WALLET_JOINS}"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY t.created_at DESC, t.transaction_id DESC LIMIT %s"
        params.append(limit)

        with self.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()