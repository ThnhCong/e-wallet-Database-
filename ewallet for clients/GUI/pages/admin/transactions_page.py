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
        if row < 0: return
        try:
            tx_id = int(self.table.item(row, 0).text())
            detail = self.api.admin_transaction_detail(self.state.user_id, tx_id)
            notify(self, f"Transaction #{tx_id}", "\n".join(f"{key}: {value}" for key, value in detail.items()))
        except Exception as error:
            self.show_error(error)

    def refresh(self):
        try:
            self.table.set_rows(self.api.admin_transactions(self.state.user_id,
                                                           self.type_filter.currentData(),
                                                           self.status_filter.currentData()))
        except Exception as error:
            self.show_error(error)
