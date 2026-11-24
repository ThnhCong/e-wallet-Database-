# src/modules/admin/admin_controller.py
class AdminController:
    """Moi ham nhan admin_id lam tham so DAU TIEN; quyen duoc kiem tra lai trong AdminService."""

    def __init__(self, admin_service):
        self.admin_service = admin_service

    def list_users(self, admin_id, limit=50):
        return self.admin_service.list_users(admin_id, limit)

    def list_wallets(self, admin_id, user_id=None, limit=50):
        return self.admin_service.list_wallets(admin_id, user_id, limit)

    def list_transactions(self, admin_id, tx_type=None, status=None, limit=50):
        return self.admin_service.list_transactions(admin_id, tx_type, status, limit)

    def get_transaction(self, admin_id, transaction_id):
        return self.admin_service.get_transaction(admin_id, transaction_id)

    def list_audit_logs(self, admin_id, user_id=None, action=None, limit=50):
        return self.admin_service.list_audit_logs(admin_id, user_id, action, limit)

    def lock_wallet(self, admin_id, wallet_id):
        return self.admin_service.set_wallet_locked(admin_id, wallet_id, True)

    def unlock_wallet(self, admin_id, wallet_id):
        return self.admin_service.set_wallet_locked(admin_id, wallet_id, False)

    def get_user_profile(self, admin_id, user_id):
        return self.admin_service.get_user_profile(admin_id, user_id)

    def list_user_profiles(self, admin_id, page=1, page_size=20, search=None, sex=None, country=None,
                           sort_by="created_at", sort_order="DESC"):
        return self.admin_service.list_user_profiles(admin_id, page, page_size, search, sex, country,
                                                     sort_by, sort_order)

    def list_bank_accounts(self, admin_id, limit=50):
        return self.admin_service.list_bank_accounts(admin_id, limit)

    def list_partner_banks(self, admin_id):
        return self.admin_service.list_partner_banks(admin_id)

    def create_partner_bank(self, admin_id, name):
        return self.admin_service.create_partner_bank(admin_id, name)

    def set_partner_bank_valid(self, admin_id, bank_id, is_valid):
        return self.admin_service.set_partner_bank_valid(admin_id, bank_id, is_valid)

    def bank_statistics(self, admin_id):
        return self.admin_service.bank_statistics(admin_id)

    def system_statistics(self, admin_id):
        return self.admin_service.system_statistics(admin_id)
