from PySide6.QtWidgets import QGridLayout, QLabel
from GUI.pages.common import Page, make_button
from GUI.widgets.balance_card import BalanceCard


class AdminOverviewPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("System overview", "Live operational snapshot returned by the administration statistics service.", parent)
        self.api, self.state = api, state
        grid = QGridLayout(); grid.setSpacing(14)
        self.cards = {}
        definitions = [
            ("users", "REGISTERED USERS"), ("profiles", "COMPLETED PROFILES"),
            ("wallets", "TOTAL WALLETS"), ("locked_wallets", "LOCKED WALLETS"),
            ("banks", "PARTNER BANKS"), ("bank_accounts", "BANK CONNECTIONS"),
            ("tx_success", "SUCCESSFUL TX"), ("tx_fail", "FAILED TX"),
            ("tx_pending", "PENDING TX"),
        ]
        for i, (key, title) in enumerate(definitions):
            card = BalanceCard(title, "—"); self.cards[key] = card
            grid.addWidget(card, i // 3, i % 3)
        self.layout.addLayout(grid)
        self.vnd = QLabel("VND deposit volume: —"); self.vnd.setObjectName("InsightBanner")
        self.usd = QLabel("USD deposit volume: —"); self.usd.setObjectName("InsightBanner")
        self.layout.addWidget(self.vnd); self.layout.addWidget(self.usd)
        self.layout.addWidget(make_button("Refresh system metrics", self.refresh))
        self.layout.addStretch()

    def refresh(self):
        self.run_api(self.api.admin_system_statistics, self.state.user_id, on_success=self._render_statistics)

    def _render_statistics(self, data):
        for key, card in self.cards.items():
            card.set_value(data.get(key, 0))
        self.vnd.setText(f"VND · Successful deposit volume     {float(data.get('deposit_volume_vnd') or 0):,.2f} VND")
        self.usd.setText(f"USD · Successful deposit volume     {float(data.get('deposit_volume_usd') or 0):,.2f} USD")