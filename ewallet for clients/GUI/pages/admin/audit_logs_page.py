from GUI.pages.common import Page, add_form, add_table, make_button, make_combo, make_input
from GUI.core.formatter import short_time


ACTIONS = ["REGISTER", "LOGIN", "LOGOUT", "CHANGE_PASSWORD", "UPDATE_PROFILE",
           "CREATE_WALLET", "LOCK_WALLET", "UNLOCK_WALLET", "DEPOSIT", "WITHDRAW",
           "TRANSFER", "TRANSFER_RECEIVED"]


class AdminAuditLogsPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("Audit logs", "Immutable record of important system activities.", parent)
        self.api, self.state = api, state
        self.action = make_combo(ACTIONS, "All actions")
        add_form(self, [("Action", self.action)])
        self.layout.addWidget(make_button("Refresh logs", self.refresh))
        self.table = add_table(self, [
            ("Log ID", "audit_log_id"), ("User", "user_id"), ("Wallet", "wallet_id"),
            ("Transaction", "transaction_id"), ("Action", "action"),
            ("Created", lambda r: short_time(r.get("created_at"))),
        ])

    def refresh(self):
        try:
            self.table.set_rows(self.api.admin_audit_logs(self.state.user_id, self.action.currentData()))
        except Exception as error:
            self.show_error(error)
