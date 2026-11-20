from GUI.pages.common import Page, add_form, add_table, make_button, make_combo, make_input
from GUI.core.formatter import money, short_time
from GUI.widgets.toast import notify


class HistoryPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("Transaction history", "Review your deposits, withdrawals and transfers.", parent)
        self.api, self.state = api, state
        self.type_filter = make_combo(["DEPOSIT", "WITHDRAW", "TRANSFER"], "All types")
        self.status_filter = make_combo(["PENDING", "SUCCESS", "FAIL"], "All statuses")
        self.limit = make_input("100")
        add_form(self, [("Type", self.type_filter), ("Status", self.status_filter), ("Maximum rows", self.limit)])
        self.layout.addWidget(make_button("Apply filters", self.refresh))
        self.table = add_table(self, [
            ("ID", "transaction_id"), ("Type", "type"), ("Amount", lambda r: money(r.get("amount"))),
            ("Sender", "sender_id"), ("Receiver", "receiver_id"), ("Status", "status"),
            ("Created", lambda r: short_time(r.get("created_at"))),
        ])
        self.table.doubleClicked.connect(self.show_detail)

    def refresh(self):
        try:
            limit = int(self.limit.text() or "100")
            rows = self.api.history(self.state.user_id, self.type_filter.currentData(),
                                    self.status_filter.currentData(), limit)
            self.table.set_rows(rows)
        except Exception as error:
            self.show_error(error)

    def show_detail(self):
        row = self.table.currentRow()
        if row < 0:
            return
        try:
            detail = self.api.transaction_detail(self.state.user_id, int(self.table.item(row, 0).text()))
            text = "\n".join(f"{key}: {value}" for key, value in detail.items())
            notify(self, "Transaction details", text)
        except Exception as error:
            self.show_error(error)
