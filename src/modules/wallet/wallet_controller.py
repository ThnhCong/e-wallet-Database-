# src/modules/wallet/wallet_controller.py
class WalletController:

    def __init__(self, wallet_service):
        self.wallet_service = wallet_service

    def create_wallet(self, user_id, currency):
        return self.wallet_service.create_wallet(user_id, currency)

    def list_wallets(self, user_id):
        return self.wallet_service.list_wallets(user_id)

    def get_wallet_by_id(self, user_id, wallet_id):
        return self.wallet_service.get_wallet_by_id(user_id, wallet_id)

    def lock_wallet(self, user_id, wallet_id):
        return self.wallet_service.set_locked(user_id, wallet_id, True)

    def unlock_wallet(self, user_id, wallet_id):
        return self.wallet_service.set_locked(user_id, wallet_id, False)

    def list_all_wallets(self, user_id=None, limit=50):
        return self.wallet_service.list_all_wallets(user_id, limit)