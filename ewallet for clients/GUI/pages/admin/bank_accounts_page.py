from GUI.pages.common import Page, add_table, make_button
from GUI.core.formatter import short_time


class AdminBankAccountsPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("Bank connections", "Review simulated links between customer wallets and partner banks.", parent)
        self.api, self.state = api, state
        self.layout.addWidget(make_button("Refresh connections", self.refresh))
        self.table = add_table(self, [
            ("Link ID", "bank_account_id"), ("Wallet", "wallet_id"), ("User ID", "user_id"),
            ("Customer", "user_name"), ("Bank", "bank_name"), ("Bank ID", "bank_id"),
            ("Status", "status"), ("Connected", lambda r: short_time(r.get("linked_at"))),
        ])

    def refresh(self):
        try: self.table.set_rows(self.api.admin_bank_accounts(self.state.user_id))
        except Exception as error: self.show_error(error)
