# src/modules/transaction/transaction_repository.py
"""Transaction data access. Trigger logic remains responsible for validating and settling balances."""
from src.common.db import BaseRepository


class TransactionRepository(BaseRepository):
    def create_transaction(self, sender_id, receiver_id, transaction_type, amount):
        rows = self.call("sp_transaction_create", (sender_id, receiver_id, transaction_type, amount))
        return rows[0]["transaction_id"]

    def mark_transaction_success(self, transaction_id):
        self._change_pending_status(transaction_id, "SUCCESS")

    def mark_transaction_failed(self, transaction_id):
        self._change_pending_status(transaction_id, "FAIL")

    def _change_pending_status(self, transaction_id, new_status):
        rows = self.call("sp_transaction_set_status", (transaction_id, new_status))
        if not rows or rows[0]["affected_rows"] != 1:
            raise RuntimeError("Cannot update transaction status.")

    def get_transaction(self, transaction_id):
        rows = self.call("sp_transaction_get", (transaction_id,))
        return rows[0] if rows else None

    def list_transactions(self, user_id, tx_type=None, status=None, limit=20):
        return self.call("sp_transaction_list_user", (user_id, tx_type, status, limit))

    def list_all_transactions(self, tx_type=None, status=None, limit=50):
        return self.call("sp_transaction_list_all", (tx_type, status, limit))
