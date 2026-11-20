from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from GUI.pages.common import make_button
from GUI.widgets.toast import notify


class LoginPage(QWidget):
    def __init__(self, api, on_login, on_register, parent=None):
        super().__init__(parent)
        self.api = api
        self.on_login = on_login
        layout = QVBoxLayout(self)
        layout.addStretch()
        row = QHBoxLayout()
        row.addStretch()
        card = QFrame()
        card.setObjectName("AuthCard")
        card.setFixedWidth(420)
        form = QVBoxLayout(card)
        form.setContentsMargins(34, 34, 34, 34)
        title = QLabel("Welcome back")
        title.setObjectName("AuthTitle")
        subtitle = QLabel("Sign in to your e-wallet account")
        subtitle.setObjectName("MutedLabel")
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Phone number")
        self.phone.setMinimumHeight(44)
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setMinimumHeight(44)
        self.password.returnPressed.connect(self.submit)
        sign_in = make_button("Sign in", self.submit)
        register = QPushButton("Create an account")
        register.setObjectName("TextButton")
        register.clicked.connect(on_register)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addWidget(title)
        form.addWidget(subtitle)
        form.addSpacing(16)
        form.addWidget(self.phone)
        form.addWidget(self.password)
        form.addWidget(sign_in)
        form.addWidget(register)
        row.addWidget(card)
        row.addStretch()
        layout.addLayout(row)
        layout.addStretch()

        self.phone.returnPressed.connect(self.password.setFocus)
        self.password.returnPressed.connect(self.submit)

    def submit(self):
        try:
            user = self.api.login(self.phone.text().strip(), self.password.text())
            self.on_login(user)
        except Exception as error:
            notify(self, "Sign in failed", error, True)
