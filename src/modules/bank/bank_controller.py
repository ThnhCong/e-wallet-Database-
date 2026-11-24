# src/modules/bank/bank_controller.py
class BankController:
    def __init__(self, bank_service):
        self.bank_service = bank_service

    def list_banks(self):
        return self.bank_service.list_banks()

    def list_my_links(self, user_id):
        return self.bank_service.list_my_links(user_id)

    def link_wallet(self, user_id, wallet_id, bank_id, account_number):
        return self.bank_service.link_wallet(user_id, wallet_id, bank_id, account_number)

    def unlink_wallet(self, user_id, bank_account_id):
        return self.bank_service.unlink_wallet(user_id, bank_account_id)
