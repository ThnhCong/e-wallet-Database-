from PySide6.QtWidgets import QComboBox, QLineEdit, QPushButton, QVBoxLayout, QLabel
from GUI.pages.common import Page, add_form, make_button, make_input, make_combo
from GUI.widgets.toast import notify


class RegisterPage(Page):
    def __init__(self, api, on_registered, on_back, parent=None):
        super().__init__("Create account", "Register with your name, email address and phone number.", parent)
        self.api = api
        self.on_registered = on_registered
        self.name = make_input("Full name")
        self.email = make_input("name@example.com")
        self.phone = make_input("Phone number")
        self.password = make_input("At least 6 characters")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.currency = make_combo(["VND", "USD"])
        add_form(self, [("Name", self.name), ("Email", self.email), ("Phone", self.phone),
                        ("Password", self.password), ("Initial wallet", self.currency)])
        self.layout.addWidget(make_button("Create account", self.submit))
        back = QPushButton("Back to sign in")
        back.setObjectName("TextButton")
        back.clicked.connect(on_back)
        self.layout.addWidget(back)
        self.layout.addStretch()

    def submit(self):
        self.setEnabled(False)
        def registration_succeeded(user_id):
            self.setEnabled(True)
            self._registration_complete(user_id)
        def registration_failed(message):
            self.setEnabled(True)
            notify(self, "Registration failed", message, True)
        self.api.run_async(
            self.api.register, self.name.text(), self.password.text(), self.email.text(),
            self.phone.text(), self.currency.currentText(),
            on_success=registration_succeeded, on_error=registration_failed,
        )

    def _registration_complete(self, user_id):
        notify(self, "Account created", f"Your account ID is {user_id}. You can now sign in.")
        self.on_registered()
