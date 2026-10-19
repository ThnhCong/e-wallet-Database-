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
