from PySide6.QtWidgets import QLineEdit
from GUI.pages.common import Page, add_form, make_button, make_input
from GUI.widgets.toast import notify


class SettingsPage(Page):
    def __init__(self, api, state, parent=None):
        super().__init__("Settings", "Change your account password.", parent)
        self.api, self.state = api, state
        self.current = make_input("Current password")
        self.current.setEchoMode(QLineEdit.EchoMode.Password)
        self.new = make_input("New password (at least 6 characters)")
        self.new.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm = make_input("Confirm new password")
        self.confirm.setEchoMode(QLineEdit.EchoMode.Password)
        add_form(self, [("Current password", self.current), ("New password", self.new),
                        ("Confirm password", self.confirm)])
        self.layout.addWidget(make_button("Update password", self.save))
        self.layout.addStretch()

    def save(self):
        if self.new.text() != self.confirm.text():
            self.show_error("The new passwords do not match.")
            return
        try:
            self.api.change_password(self.state.user_id, self.current.text(), self.new.text())
            self.current.clear()
            self.new.clear()
            self.confirm.clear()
            notify(self, "Password updated", "Your password has been changed.")
        except Exception as error:
            self.show_error(error)
