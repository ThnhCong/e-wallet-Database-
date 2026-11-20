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
        try:
            wallets = self.api.wallets(self.state.user_id)
            self.sender.clear()
            for w in wallets:
                label = f"#{w['wallet_id']} · {w['currency']} · {w['status']}"
                self.sender.addItem(label, w["wallet_id"])
        except Exception as error:
            self.show_error(error)

    def submit(self):
        try:
            sender_id = self.sender.currentData()
            if self.amount.value() <= 0:
                raise ValueError("The amount must be greater than 0.")
            receiver_text = self.receiver.text().strip()
            if sender_id is None or not receiver_text:
                raise ValueError("Select a sender wallet and enter the receiver wallet ID.")
            try:
                receiver_id = int(receiver_text)
            except ValueError as error:
                raise ValueError("Receiver wallet ID must be a positive integer.") from error
            if receiver_id <= 0:
                raise ValueError("Receiver wallet ID must be a positive integer.")
            result = self.api.transfer(self.state.user_id, sender_id, receiver_id, self.amount.value())
            notify(self, "Transfer complete", f"Transaction #{result['transaction_id']} succeeded.")
            self.refresh()
            self.amount.setValue(0)
        except Exception as error:
            self.show_error(error)
