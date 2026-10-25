from PySide6.QtWidgets import QHBoxLayout, QLabel
from GUI.pages.common import Page, add_table, make_button
from GUI.core.formatter import money, short_time


class DashboardPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("Dashboard", "Your wallet overview and recent activity.", parent)
        self.api, self.state = api, state
        self.summary = QLabel("")
        self.summary.setObjectName("MutedLabel")
        self.layout.addWidget(self.summary)
        row = QHBoxLayout()
        row.addWidget(make_button("Refresh overview", self.refresh))
        row.addStretch()
        self.layout.addLayout(row)
        self.table = add_table(self, [
            ("Transaction", "transaction_id"), ("Type", "type"),
            ("Amount", lambda r: money(r.get("amount"))), ("Status", "status"),
            ("Created", lambda r: short_time(r.get("created_at"))),
        ])

    def refresh(self):
        try:
            wallets = self.api.wallets(self.state.user_id)
            txs = self.api.history(self.state.user_id, limit=8)
            total = {}
            for wallet in wallets:
                currency = wallet["currency"]
                total[currency] = total.get(currency, 0) + float(wallet["balance"])
            balances = "  ·  ".join(f"{currency}: {money(amount, currency)}" for currency, amount in total.items())
            self.summary.setText(f"{len(wallets)} wallet(s)   |   {balances or 'No wallets yet'}")
            self.table.set_rows(txs)
        except Exception as error:
            self.show_error(error)
