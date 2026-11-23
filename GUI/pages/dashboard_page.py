from PySide6.QtWidgets import QHBoxLayout, QLabel, QFrame, QVBoxLayout
from GUI.pages.common import Page, add_table, make_button
from GUI.widgets.balance_card import BalanceCard
from GUI.core.formatter import money, short_time


class DashboardPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("Your wallet, at a glance", "A clear view of your balances and the latest movement across your wallets.", parent)
        self.api, self.state = api, state
        hero = QFrame(); hero.setObjectName("HeroPanel")
        hero_layout = QVBoxLayout(hero); hero_layout.setContentsMargins(22, 20, 22, 20); hero_layout.setSpacing(6)
        greeting = QLabel("WELCOME BACK"); greeting.setObjectName("HeroEyebrow")
        self.hero_title = QLabel("Your money, in one place."); self.hero_title.setObjectName("HeroTitle")
        self.hero_subtitle = QLabel("Stay on top of your everyday finances."); self.hero_subtitle.setObjectName("HeroSubtitle")
        hero_layout.addWidget(greeting); hero_layout.addWidget(self.hero_title); hero_layout.addWidget(self.hero_subtitle)
        self.layout.addWidget(hero)
        cards = QHBoxLayout(); cards.setSpacing(12)
        self.wallet_count = BalanceCard("ACTIVE WALLETS", "—")
        self.balance_vnd = BalanceCard("TOTAL BALANCE · VND", "—")
        self.balance_usd = BalanceCard("TOTAL BALANCE · USD", "—")
        self.tx_count = BalanceCard("RECENT TRANSACTIONS", "—")
        for card in [self.wallet_count, self.balance_vnd, self.balance_usd, self.tx_count]: cards.addWidget(card)
        self.layout.addLayout(cards)
        row = QHBoxLayout(); row.addWidget(self.section_label("Recent transactions")); row.addStretch()
        row.addWidget(make_button("Refresh overview", self.refresh, "SecondaryButton"))
        self.layout.addLayout(row)
        self.table = add_table(self, [
            ("Transaction", "transaction_id"), ("Type", "type"),
            ("Amount", lambda r: money(r.get("amount"))), ("Status", "status"),
            ("Created", lambda r: short_time(r.get("created_at"))),
        ])

    def refresh(self):
        self.run_api(self.api.dashboard_summary, self.state.user_id, on_success=self._render_summary)

    def _render_summary(self, data):
        wallets = data.get("wallets") or []
        txs = data.get("transactions") or []
        total = {"VND": 0.0, "USD": 0.0}
        active = 0
        for wallet in wallets:
            currency = wallet["currency"]
            total[currency] = total.get(currency, 0.0) + float(wallet["balance"])
            active += int(wallet.get("status") == "ACTIVE")
        self.wallet_count.set_value(f"{active} / {len(wallets)}")
        self.balance_vnd.set_value(money(total.get("VND", 0), "VND"))
        self.balance_usd.set_value(money(total.get("USD", 0), "USD"))
        self.tx_count.set_value(len(txs))
        self.hero_title.setText(f"Welcome back, {self.state.user.get('user_name', 'there')}.")
        self.table.set_rows(txs)