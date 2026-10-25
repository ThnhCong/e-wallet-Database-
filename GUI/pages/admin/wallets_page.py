from GUI.pages.common import Page, add_table, make_button
from GUI.core.formatter import money
from GUI.widgets.confirm_dialog import confirm
from GUI.widgets.toast import notify


class AdminWalletsPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("Wallet administration", "Review wallets and lock or unlock them when necessary.", parent)
        self.api, self.state = api, state
        self.layout.addWidget(make_button("Refresh wallets", self.refresh))
        self.table = add_table(self, [
            ("Wallet ID", "wallet_id"), ("Owner ID", "user_id"), ("Owner", "user_name"),
            ("Currency", "currency"), ("Balance", lambda r: money(r.get("balance"), r.get("currency", ""))),
            ("Weekly cap", lambda r: money(r.get("limit_week"), r.get("currency", ""))),
            ("Remaining", lambda r: money(r.get("remain_limit_week"), r.get("currency", ""))),
            ("Status", "status"),
        ])
        self.layout.addWidget(make_button("Lock selected wallet", lambda: self.set_locked(True), "DangerButton"))
        self.layout.addWidget(make_button("Unlock selected wallet", lambda: self.set_locked(False)))

    def refresh(self):
        try:
            self.table.set_rows(self.api.admin_wallets(self.state.user_id))
        except Exception as error:
            self.show_error(error)

    def set_locked(self, locked):
        row = self.table.currentRow()
        if row < 0:
            self.show_error("Select a wallet first.")
            return
        wallet_id = int(self.table.item(row, 0).text())
        action = "lock" if locked else "unlock"
        if not confirm(self, f"{action.title()} wallet", f"Are you sure you want to {action} wallet #{wallet_id}?"):
            return
        try:
            self.api.admin_set_wallet_locked(self.state.user_id, wallet_id, locked)
            notify(self, "Wallet updated", f"Wallet #{wallet_id} is now {'LOCKED' if locked else 'ACTIVE'}.")
            self.refresh()
        except Exception as error:
            self.show_error(error)
