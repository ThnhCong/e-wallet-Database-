# src/modules/bank/bank_repository.py
from src.common.db import BaseRepository


class BankRepository(BaseRepository):
    """banks (partner banks, read-only for the application) and bank_accounts (wallet <-> bank links)."""

    def list_banks(self):
        return self.call("sp_bank_list")

    def list_all_banks(self): return self.call("sp_admin_bank_list")
    def set_bank_valid(self, bank_id, is_valid):
        rows=self.call("sp_admin_bank_set_valid", (bank_id, bool(is_valid))); return rows[0] if rows else None
    def has_active_link(self, wallet_id):
        rows=self.call("sp_bank_account_has_active_link", (wallet_id,)); return bool(rows and rows[0].get("has_active_link"))

    def get_bank(self, bank_id):
        rows = self.call("sp_bank_get", (bank_id,))
        return rows[0] if rows else None

    def create_partner_bank(self, name):
        rows = self.call("sp_admin_bank_create", (name,))
        return rows[0] if rows else None

    def link(self, wallet_id, bank_id, account_number):
        rows = self.call("sp_bank_account_link", (wallet_id, bank_id, account_number))
        return rows[0] if rows else {}

    def unlink(self, user_id, bank_account_id):
        rows=self.call("sp_bank_account_unlink", (user_id, bank_account_id)); return rows[0] if rows and rows[0].get("affected_rows") else None

    def list_links_by_user(self, user_id):
        return self.call("sp_bank_account_list_by_user", (user_id,))

    def list_all_links(self, limit=50):
        return self.call("sp_bank_account_list_all", (limit,))
