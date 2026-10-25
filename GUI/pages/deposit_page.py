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
        try:
            wallets = self.api.wallets(self.state.user_id)
            self.wallet.clear()
            for wallet in wallets:
                self.wallet.addItem(f"#{wallet['wallet_id']} · {wallet['currency']} · {wallet['status']}", wallet["wallet_id"])
        except Exception as error:
            self.show_error(error)

    def submit(self):
        try:
            wallet_id = self.wallet.currentData()
            if self.amount.value() <= 0:
                raise ValueError("The amount must be greater than 0.")
            if wallet_id is None:
                raise ValueError("Create or select a wallet first.")
            result = self.api.deposit(self.state.user_id, wallet_id, self.amount.value())
            notify(self, "Deposit complete", f"Transaction #{result['transaction_id']} succeeded. New balance: {result['balance']} {self.wallet.currentText().split('·')[1].strip()}.")
            self.refresh()
            self.amount.setValue(0)
        except Exception as error:
            self.show_error(error)
