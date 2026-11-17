# src/modules/wallet/wallet_repository.py
"""Wallet data access. Balance and weekly-limit changes remain trigger-owned."""
from src.common.db import BaseRepository


class WalletRepository(BaseRepository):
    def create_wallet(self, user_id, currency):
        rows = self.call("sp_wallet_create", (user_id, currency))
        return rows[0]["wallet_id"]

    def get_wallet_by_id(self, wallet_id):
        rows = self.call("sp_wallet_get_by_id", (wallet_id,))
        return rows[0] if rows else None

    def list_wallets_by_user(self, user_id):
        return self.call("sp_wallet_list_by_user", (user_id,))

    def list_all_wallets(self, user_id=None, limit=50):
        return self.call("sp_wallet_list_all", (user_id, limit))

    def lock_wallets(self, *wallet_ids):
        ids = sorted({value for value in wallet_ids if value is not None})
        if not ids:
            return {}
        if len(ids) > 2:
            raise ValueError("At most two wallets can be locked by this operation.")
        rows = self.call("sp_wallet_lock_many", (ids[0], ids[1] if len(ids) == 2 else None))
        return {row["wallet_id"]: row for row in rows}

    def set_wallet_status(self, wallet_id, status):
        self.call("sp_wallet_set_status", (wallet_id, status))
