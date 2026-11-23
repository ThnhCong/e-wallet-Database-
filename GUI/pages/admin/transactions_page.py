from GUI.pages.common import Page, add_form, add_table, make_button, make_combo
from GUI.core.formatter import money, short_time
from GUI.widgets.toast import notify


class AdminTransactionsPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("All transactions", "Administrator view across all users.", parent)
        self.api, self.state = api, state
        self.type_filter = make_combo(["DEPOSIT", "WITHDRAW", "TRANSFER"], "All types")
        self.status_filter = make_combo(["PENDING", "SUCCESS", "FAIL"], "All statuses")
        add_form(self, [("Type", self.type_filter), ("Status", self.status_filter)])
        self.layout.addWidget(make_button("Apply filters", self.refresh))
        self.table = add_table(self, [
            ("ID", "transaction_id"), ("Type", "type"), ("Amount", lambda r: money(r.get("amount"))),
            ("Sender", "sender_id"), ("Receiver", "receiver_id"), ("Status", "status"),
            ("Created", lambda r: short_time(r.get("created_at"))),
        ])
        self.table.doubleClicked.connect(self.show_detail)

    def show_detail(self):
        row = self.table.currentRow()
        if row < 0:
            return
        try:
            tx_id = int(self.table.item(row, 0).text())
        except (AttributeError, TypeError, ValueError):
            self.show_error("The selected transaction is invalid.")
            return
        self.run_api(self.api.admin_transaction_detail, self.state.user_id, tx_id,
                     on_success=lambda detail: notify(self, f"Transaction #{tx_id}", "\n".join(f"{key}: {value}" for key, value in detail.items())))
    def refresh(self):
        self.run_api(self.api.admin_transactions, self.state.user_id, self.type_filter.currentData(),
                     self.status_filter.currentData(), on_success=self.table.set_rows)