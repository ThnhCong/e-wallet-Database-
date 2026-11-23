from GUI.pages.common import Page, add_form, make_button, make_combo, make_input
from GUI.widgets.amount_input import AmountInput
from GUI.widgets.toast import notify


class TransferPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("Transfer money", "Both wallets must be active and use the same currency. The sender's weekly limit applies.", parent)
        self.api, self.state = api, state
        self.sender = make_combo([])
        self.receiver = make_input("Receiver wallet ID")
        self.amount = AmountInput()
        add_form(self, [("From wallet", self.sender), ("Receiver wallet ID", self.receiver), ("Amount", self.amount)])
        self.layout.addWidget(make_button("Confirm transfer", self.submit))
        self.layout.addStretch()

    def refresh(self):
        self.run_api(self.api.wallets, self.state.user_id, on_success=self._set_wallets)

    def _set_wallets(self, wallets):
        self.sender.clear()
        for w in wallets:
            label = f"#{w['wallet_id']} · {w['currency']} · {w['status']}"
            self.sender.addItem(label, w["wallet_id"])
    def submit(self):
        sender_id = self.sender.currentData()
        amount = self.amount.value()
        receiver_text = self.receiver.text().strip()
        if amount <= 0:
            self.show_error("The amount must be greater than 0.")
            return
        if sender_id is None or not receiver_text:
            self.show_error("Select a sender wallet and enter the receiver wallet ID.")
            return
        try:
            receiver_id = int(receiver_text)
        except ValueError:
            self.show_error("Receiver wallet ID must be a positive integer.")
            return
        if receiver_id <= 0:
            self.show_error("Receiver wallet ID must be a positive integer.")
            return
        self.run_api(self.api.transfer, self.state.user_id, sender_id, receiver_id, amount,
                     write=True, on_success=self._transfer_complete)

    def _transfer_complete(self, result):
        notify(self, "Transfer complete", f"Transaction #{result['transaction_id']} succeeded.")
        self.amount.setValue(0)
        self.refresh()
