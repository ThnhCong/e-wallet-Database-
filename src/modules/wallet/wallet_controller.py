class WalletController:

    def __init__(self, wallet_service):
        self.wallet_service = wallet_service

    def create_wallet(self, user_id, currency):
        return self.wallet_service.create_wallet(user_id, currency)

    def deposit(self, user_id, amount):
        return self.wallet_service.deposit(user_id, amount)

    def withdraw(self, user_id, amount):
        return self.wallet_service.withdraw(user_id, amount)

    def transfer(self, sender_user_id, receiver_user_id, amount):
        return self.wallet_service.transfer(sender_user_id, receiver_user_id, amount)

    def get_wallet_by_id(self, wallet_id):
        return self.wallet_service.get_wallet_by_id(wallet_id)