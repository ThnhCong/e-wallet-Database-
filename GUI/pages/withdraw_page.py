from GUI.pages.common import Page, add_form, make_button, make_combo
from GUI.widgets.amount_input import AmountInput
from GUI.widgets.toast import notify


class WithdrawPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("Withdraw", "The amount must not exceed the wallet balance. Weekly transfer limits do not apply.", parent)
        self.api, self.state = api, state
        self.wallet = make_combo([])
        self.amount = AmountInput()
        add_form(self, [("Source wallet", self.wallet), ("Amount", self.amount)])
        self.layout.addWidget(make_button("Confirm withdrawal", self.submit))
        self.layout.addStretch()

    def refresh(self):
        try:
            self.wallet.clear()
            for w in self.api.wallets(self.state.user_id):
                self.wallet.addItem(f"#{w['wallet_id']} · {w['currency']} · {w['status']}", w["wallet_id"])
        except Exception as error:
            self.show_error(error)

    def submit(self):
        try:
            wallet_id = self.wallet.currentData()
            if self.amount.value() <= 0:
                raise ValueError("The amount must be greater than 0.")
            if wallet_id is None:
                raise ValueError("Create or select a wallet first.")
            result = self.api.withdraw(self.state.user_id, wallet_id, self.amount.value())
            notify(self, "Withdrawal complete", f"Transaction #{result['transaction_id']} succeeded. Balance: {result['balance']}.")
            self.refresh()
            self.amount.setValue(0)
        except Exception as error:
            self.show_error(error)
