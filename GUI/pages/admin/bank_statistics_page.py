from GUI.pages.common import Page, add_table, make_button
from GUI.core.formatter import short_time


class AdminBankStatisticsPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("Partner bank analytics", "Compare how many customer wallets and users are connected to each partner bank.", parent)
        self.api, self.state = api, state
        self.layout.addWidget(make_button("Refresh bank analytics", self.refresh))
        self.table = add_table(self, [
            ("Bank ID", "bank_id"), ("Partner bank", "bank_name"),
            ("Linked wallets", "linked_wallets"), ("Unique users", "linked_users"),
            ("Partner since", lambda r: short_time(r.get("cooperated_at"))),
        ])

    def refresh(self):
        try: self.table.set_rows(self.api.admin_bank_statistics(self.state.user_id))
        except Exception as error: self.show_error(error)
