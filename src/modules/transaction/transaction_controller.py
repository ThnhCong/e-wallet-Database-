# src/modules/transaction/transaction_controller.py
class TransactionController:

    def __init__(self, transaction_service):
        self.transaction_service = transaction_service

    def deposit(self, user_id, wallet_id, amount):
        return self.transaction_service.deposit(user_id, wallet_id, amount)

    def withdraw(self, user_id, wallet_id, amount):
        return self.transaction_service.withdraw(user_id, wallet_id, amount)

    def transfer(self, user_id, sender_wallet_id, receiver_wallet_id, amount):
        return self.transaction_service.transfer(user_id, sender_wallet_id, receiver_wallet_id, amount)

    def history(self, user_id, tx_type=None, status=None, limit=20):
        return self.transaction_service.history(user_id, tx_type, status, limit)

    def transaction_detail(self, user_id, transaction_id):
        return self.transaction_service.transaction_detail(user_id, transaction_id)

    def list_all_transactions(self, tx_type=None, status=None, limit=50):
        return self.transaction_service.list_all_transactions(tx_type, status, limit)

    def get_transaction_by_id(self, transaction_id):
        return self.transaction_service.get_transaction_by_id(transaction_id)