from GUI.pages.common import Page, add_form, make_button, make_combo
from GUI.widgets.amount_input import AmountInput
from GUI.widgets.toast import notify


class WithdrawPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("Withdraw", "The amount must not exceed the wallet balance. Link an active partner bank first.", parent)
        self.api, self.state = api, state
        self.wallet = make_combo([])
        self.amount = AmountInput()
        add_form(self, [("Source wallet", self.wallet), ("Amount", self.amount)])
        self.layout.addWidget(make_button("Confirm withdrawal", self.submit))
        self.layout.addStretch()

    def refresh(self):
        self.run_api(self.api.wallets, self.state.user_id, on_success=self._set_wallets)

    def _set_wallets(self, wallets):
        self.wallet.clear()
        for w in wallets:
            self.wallet.addItem(f"#{w['wallet_id']} · {w['currency']} · {w['status']}", w["wallet_id"])
    def submit(self):
        wallet_id = self.wallet.currentData()
        amount = self.amount.value()
        if amount <= 0:
            self.show_error("The amount must be greater than 0.")
            return
        if wallet_id is None:
            self.show_error("Create or select a wallet first.")
            return
        self.run_api(self.api.withdraw, self.state.user_id, wallet_id, amount,
                     write=True, on_success=self._withdraw_complete)

    def _withdraw_complete(self, result):
        notify(self, "Withdrawal complete", f"Transaction #{result['transaction_id']} succeeded. Balance: {result['balance']}.")
        self.amount.setValue(0)
        self.refresh()
