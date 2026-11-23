from PySide6.QtWidgets import QHBoxLayout
from GUI.pages.common import Page, add_form, add_table, make_button, make_input
from GUI.widgets.balance_card import BalanceCard


class StatisticsPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("My insights", "A per-currency view of your wallet activity. Leave either date blank to include the full available period.", parent)
        self.api, self.state = api, state
        self.date_from = make_input("YYYY-MM-DD (optional)")
        self.date_to = make_input("YYYY-MM-DD (optional)")
        add_form(self, [("From date", self.date_from), ("To date", self.date_to)])
        row = QHBoxLayout(); row.addWidget(make_button("Apply period", self.refresh)); row.addStretch(); self.layout.addLayout(row)
        cards = QHBoxLayout()
        self.wallets = BalanceCard("WALLETS", "—")
        self.success = BalanceCard("SUCCESSFUL OPERATIONS", "—")
        self.failed = BalanceCard("FAILED OPERATIONS", "—")
        cards.addWidget(self.wallets); cards.addWidget(self.success); cards.addWidget(self.failed)
        self.layout.addLayout(cards)
        self.table = add_table(self, [
            ("Currency", "currency"), ("Wallets", "wallet_count"),
            ("Deposited", "total_deposit"), ("Withdrawn", "total_withdraw"),
            ("Transfer in", "total_transfer_in"), ("Transfer out", "total_transfer_out"),
            ("Success", "success_count"), ("Failed", "fail_count"),
        ])

    def refresh(self):
        start = self.date_from.text().strip() or None
        end = self.date_to.text().strip() or None
        self.run_api(self.api.statistics, self.state.user_id, start, end, on_success=self._render_statistics)

    def _render_statistics(self, rows):
        self.table.set_rows(rows)
        self.wallets.set_value(sum(int(r.get("wallet_count") or 0) for r in rows))
        self.success.set_value(sum(int(r.get("success_count") or 0) for r in rows))
        self.failed.set_value(sum(int(r.get("fail_count") or 0) for r in rows))