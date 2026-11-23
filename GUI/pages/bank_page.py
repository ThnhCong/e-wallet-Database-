from PySide6.QtWidgets import QHBoxLayout, QLabel
from GUI.pages.common import Page, add_form, add_table, make_button, make_combo
from GUI.core.formatter import short_time
from GUI.widgets.toast import notify


class BankPage(Page):
    """User bank directory and simulated wallet-to-bank linking."""
    def __init__(self, api, state, parent=None):
        super().__init__("Bank connections", "Connect an active wallet to one of the partner banks. This is a simulated link; it does not contact a real bank.", parent)
        self.api, self.state = api, state
        self.wallet = make_combo([])
        self.bank = make_combo([])
        add_form(self, [("Wallet to connect", self.wallet), ("Partner bank", self.bank)])
        actions = QHBoxLayout()
        actions.addWidget(make_button("Connect bank", self.link_bank))
        actions.addWidget(make_button("Refresh", self.refresh, "SecondaryButton"))
        actions.addStretch()
        self.layout.addLayout(actions)
        self.layout.addWidget(self.section_label("My connected banks"))
        self.table = add_table(self, [
            ("Link ID", "bank_account_id"), ("Wallet", "wallet_id"),
            ("Currency", "currency"), ("Bank", "bank_name"),
            ("Status", "status"), ("Connected", lambda r: short_time(r.get("linked_at"))),
        ])

    def refresh(self):
        try:
            wallets = self.api.wallets(self.state.user_id)
            banks = self.api.banks()
            self.wallet.clear()
            for w in wallets:
                self.wallet.addItem(f"Wallet #{w['wallet_id']} · {w['currency']} · {w['status']}", w['wallet_id'])
            self.bank.clear()
            for b in banks:
                self.bank.addItem(b['name'], b['bank_id'])
            self.table.set_rows(self.api.bank_accounts(self.state.user_id))
        except Exception as error:
            self.show_error(error)

    def link_bank(self):
        try:
            wallet_id, bank_id = self.wallet.currentData(), self.bank.currentData()
            if wallet_id is None or bank_id is None:
                raise ValueError("Choose a wallet and a partner bank first.")
            result = self.api.link_bank(self.state.user_id, wallet_id, bank_id)
            notify(self, "Bank connected", f"{result.get('bank_name', 'Partner bank')} connected to wallet #{wallet_id}. Reference: {result.get('bank_account_id', '—')}")
            self.refresh()
        except Exception as error:
            self.show_error(error)
