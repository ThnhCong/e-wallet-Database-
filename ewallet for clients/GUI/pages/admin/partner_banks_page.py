from PySide6.QtWidgets import QHBoxLayout

from GUI.pages.common import Page, add_table, make_button, make_input
from GUI.widgets.confirm_dialog import confirm
from GUI.widgets.toast import notify


class AdminPartnerBanksPage(Page):
    """Admin CRUD screen for the partner-bank catalogue."""

    def __init__(self, api, state, parent=None):
        super().__init__(
            "Partner bank management",
            "Add partner banks that customers can choose when linking a bank account.",
            parent,
        )
        self.api, self.state = api, state

        form_row = QHBoxLayout()
        self.bank_name = make_input("Enter partner bank name (up to 100 characters)")
        self.bank_name.returnPressed.connect(self.create_bank)
        form_row.addWidget(self.bank_name, 1)
        form_row.addWidget(make_button("Add bank", self.create_bank))
        self.layout.addLayout(form_row)

        self.table = add_table(self, [
            ("Bank ID", "bank_id"),
            ("Partner bank", "name"),
            ("Cooperation date", "cooperated_at"),
        ])

        actions = QHBoxLayout()
        actions.addWidget(make_button("Refresh", self.refresh, "SecondaryButton"))
        actions.addStretch(1)
        actions.addWidget(make_button("Delete selected bank", self.delete_bank, "DangerButton"))
        self.layout.addLayout(actions)

    def refresh(self):
        self.run_api(self.api.admin_partner_banks, self.state.user_id,
                     on_success=lambda rows: self.table.set_rows(rows or []))
    def create_bank(self):
        name = self.bank_name.text().strip()
        if not name:
            self.show_error("Enter a partner bank name.")
            self.bank_name.setFocus()
            return
        self.run_api(self.api.admin_create_partner_bank, self.state.user_id, name,
                     write=True, on_success=lambda result: self._partner_bank_created(result, name))

    def _partner_bank_created(self, result, fallback_name):
        bank_name = (result or {}).get("name", fallback_name)
        self.bank_name.clear()
        notify(self, "Partner bank added", f"{bank_name} is now available for customer bank linking.")
        self.refresh()
    def delete_bank(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_error("Select a partner bank first.")
            return
        try:
            bank_id = int(self.table.item(row, 0).text())
            bank_name = self.table.item(row, 1).text()
        except (AttributeError, TypeError, ValueError):
            self.show_error("The selected bank row is invalid. Refresh the list and try again.")
            return
        if not confirm(self, "Delete partner bank",
                       f"Are you sure you want to delete {bank_name} (ID: {bank_id})?\n\n"
                       "A bank that already has customer links cannot be deleted."):
            return
        self.run_api(self.api.admin_delete_partner_bank, self.state.user_id, bank_id,
                     write=True, on_success=lambda _result: self._partner_bank_deleted(bank_name))

    def _partner_bank_deleted(self, bank_name):
        notify(self, "Partner bank deleted", f"{bank_name} has been removed.")
        self.refresh()
