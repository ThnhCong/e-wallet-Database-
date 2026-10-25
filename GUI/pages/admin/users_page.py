from GUI.pages.common import Page, add_table, make_button


class AdminUsersPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("User administration", "Read-only overview of registered users.", parent)
        self.api, self.state = api, state
        self.layout.addWidget(make_button("Refresh users", self.refresh))
        self.table = add_table(self, [
            ("User ID", "user_id"), ("Name", "user_name"), ("Email", "email"),
            ("Phone", "phone"), ("Role", "user_role"), ("Wallets", "wallet_count"),
        ])

    def refresh(self):
        try:
            self.table.set_rows(self.api.admin_users(self.state.user_id))
        except Exception as error:
            self.show_error(error)
