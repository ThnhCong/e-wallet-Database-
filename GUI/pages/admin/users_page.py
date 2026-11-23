from PySide6.QtCore import Signal
from GUI.pages.common import Page, add_table, make_button


class AdminUsersPage(Page):
    profile_requested = Signal(int)
    def __init__(self, api, state, parent=None):
        super().__init__("User administration", "Read-only overview of registered users.", parent)
        self.api, self.state = api, state
        self.layout.addWidget(make_button("Refresh users", self.refresh))
        self.table = add_table(self, [
            ("User ID", "user_id"), ("Name", "user_name"), ("Email", "email"),
            ("Phone", "phone"), ("Wallets", "wallet_count"),
        ])
        self.layout.addWidget(make_button("View selected customer profile", self.view_profile, "SecondaryButton"))

    def view_profile(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_error("Select a customer first.")
            return
        try:
            self.profile_requested.emit(int(self.table.item(row, 0).text()))
        except Exception as error:
            self.show_error(error)

    def refresh(self):
        try:
            self.table.set_rows(self.api.admin_users(self.state.user_id))
        except Exception as error:
            self.show_error(error)
