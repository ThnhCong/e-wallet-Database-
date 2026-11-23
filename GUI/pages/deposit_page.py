from GUI.pages.common import Page, add_form, make_button, make_combo
from GUI.widgets.amount_input import AmountInput
from GUI.widgets.toast import notify


class DepositPage(Page):
    tx_type = "deposit"

    def __init__(self, api, state, parent=None):
        super().__init__("Deposit", "Deposits are simulated and have no weekly limit.", parent)
        self.api, self.state = api, state
        self.wallet = make_combo([])
        self.amount = AmountInput()
        add_form(self, [("Destination wallet", self.wallet), ("Amount", self.amount)])
        self.layout.addWidget(make_button("Confirm deposit", self.submit))
        self.layout.addStretch()

    def refresh(self):
        self.run_api(self.api.wallets, self.state.user_id, on_success=self._set_wallets)

    def _set_wallets(self, wallets):
        self.wallet.clear()
        for wallet in wallets:
            self.wallet.addItem(f"#{wallet['wallet_id']} · {wallet['currency']} · {wallet['status']}", wallet["wallet_id"])
    def submit(self):
        wallet_id = self.wallet.currentData()
        amount = self.amount.value()
        if amount <= 0:
            self.show_error("The amount must be greater than 0.")
            return
        if wallet_id is None:
            self.show_error("Create or select a wallet first.")
            return
        currency = self.wallet.currentText().split('·')[1].strip()
        self.run_api(self.api.deposit, self.state.user_id, wallet_id, amount,
                     write=True, on_success=lambda result: self._deposit_complete(result, currency))

    def _deposit_complete(self, result, currency):
        notify(self, "Deposit complete", f"Transaction #{result['transaction_id']} succeeded. New balance: {result['balance']} {currency}.")
        self.amount.setValue(0)
        self.refresh()
