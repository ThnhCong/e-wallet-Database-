# src/modules/bank/bank_repository.py
from src.common.db import BaseRepository


class BankRepository(BaseRepository):
    """banks (partner banks, read-only for the application) and bank_accounts (wallet <-> bank links)."""

    def list_banks(self):
        return self.call("sp_bank_list")

    def get_bank(self, bank_id):
        rows = self.call("sp_bank_get", (bank_id,))
        return rows[0] if rows else None

    def create_partner_bank(self, name):
        rows = self.call("sp_admin_bank_create", (name,))
        return rows[0] if rows else None

    def delete_partner_bank(self, bank_id):
        rows = self.call("sp_admin_bank_delete", (bank_id,))
        return rows[0] if rows else {"bank_id": bank_id}

    def link(self, wallet_id, bank_id):
        rows = self.call("sp_bank_account_link", (wallet_id, bank_id))
        return rows[0]["bank_account_id"]

    def list_links_by_user(self, user_id):
        return self.call("sp_bank_account_list_by_user", (user_id,))

    def list_all_links(self, limit=50):
        return self.call("sp_bank_account_list_all", (limit,))
