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

    def deposit(self, user_id, wallet_id, amount):
        return self.wallet_service.deposit(user_id, wallet_id, amount)

    def withdraw(self, user_id, wallet_id, amount):
        return self.wallet_service.withdraw(user_id, wallet_id, amount)

    def transfer(self, user_id, sender_wallet_id, receiver_wallet_id, amount):
        return self.wallet_service.transfer(user_id, sender_wallet_id, receiver_wallet_id, amount)

    def history(self, user_id, tx_type=None, status=None, limit=20):
        return self.wallet_service.history(user_id, tx_type, status, limit)

    def transaction_detail(self, user_id, transaction_id):
        return self.wallet_service.transaction_detail(user_id, transaction_id)