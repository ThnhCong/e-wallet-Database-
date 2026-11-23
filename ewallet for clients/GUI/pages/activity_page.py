from GUI.pages.common import Page, add_form, add_table, make_button, make_combo
from GUI.core.formatter import short_time

ACTIONS = ["REGISTER", "LOGIN", "LOGOUT", "CHANGE_PASSWORD", "UPDATE_PROFILE", "CREATE_WALLET",
           "LOCK_WALLET", "UNLOCK_WALLET", "DEPOSIT", "WITHDRAW", "TRANSFER", "TRANSFER_RECEIVED",
           "LINK_BANK"]


class ActivityPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("Account activity", "A timeline of security and wallet events recorded for your account.", parent)
        self.api, self.state = api, state
        self.action = make_combo(ACTIONS, "All activity")
        add_form(self, [("Activity type", self.action)])
        self.layout.addWidget(make_button("Refresh activity", self.refresh))
        self.table = add_table(self, [
            ("Log ID", "audit_log_id"), ("Action", "action"), ("Wallet", "wallet_id"),
            ("Transaction", "transaction_id"), ("Recorded at", lambda r: short_time(r.get("created_at"))),
        ])

    def refresh(self):
        self.run_api(self.api.activity, self.state.user_id, self.action.currentData(), 200,
                     on_success=self.table.set_rows)