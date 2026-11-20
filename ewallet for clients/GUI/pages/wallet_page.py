from PySide6.QtWidgets import QHBoxLayout, QPushButton
from GUI.pages.common import Page, add_form, add_table, make_button, make_combo
from GUI.widgets.confirm_dialog import confirm
from GUI.widgets.toast import notify
from GUI.core.formatter import money, short_time


class WalletPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("My wallets", "Create and review wallets. Transfer limits are set by the database.", parent)
        self.api, self.state = api, state
        self.currency = make_combo(["VND", "USD"])
        add_form(self, [("New wallet currency", self.currency)])
        self.layout.addWidget(make_button("Create wallet", self.create_wallet))
        self.table = add_table(self, [
            ("Wallet ID", "wallet_id"), ("Currency", "currency"),
            ("Balance", lambda r: money(r.get("balance"), r.get("currency", ""))),
            ("Weekly cap", lambda r: money(r.get("limit_week"), r.get("currency", ""))),
            ("Remaining", lambda r: money(r.get("remain_limit_week"), r.get("currency", ""))),
            ("Status", "status"), ("Created", lambda r: short_time(r.get("created_at"))),
        ])
        actions = QHBoxLayout()
        actions.addWidget(make_button("Lock selected", lambda: self.set_locked(True), "DangerButton"))
        actions.addWidget(make_button("Unlock selected", lambda: self.set_locked(False)))
        actions.addWidget(make_button("Refresh", self.refresh, "SecondaryButton"))
        actions.addStretch()
        self.layout.addLayout(actions)

    def refresh(self):
        try:
            self.table.set_rows(self.api.wallets(self.state.user_id))
        except Exception as error:
            self.show_error(error)

    def selected_wallet(self):
        row = self.table.currentRow()
        if row < 0:
            raise ValueError("Select a wallet first.")
        return int(self.table.item(row, 0).text())

    def create_wallet(self):
        try:
            wallet = self.api.create_wallet(self.state.user_id, self.currency.currentText())
            notify(self, "Wallet created", f"Wallet #{wallet['wallet_id']} created successfully.")
            self.refresh()
        except Exception as error:
            self.show_error(error)

    def set_locked(self, locked):
        try:
            wallet_id = self.selected_wallet()
            action = "lock" if locked else "unlock"
            if not confirm(self, f"{action.title()} wallet", f"Are you sure you want to {action} wallet #{wallet_id}?"):
                return
            self.api.set_wallet_locked(self.state.user_id, wallet_id, locked)
            self.refresh()
        except Exception as error:
            self.show_error(error)
