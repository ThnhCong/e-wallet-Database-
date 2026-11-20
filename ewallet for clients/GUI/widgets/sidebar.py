from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout


class Sidebar(QFrame):
    navigated = Signal(str)
    logout_requested = Signal()

    def __init__(self, is_admin=False, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 24, 16, 20)
        layout.setSpacing(8)

        brand = QLabel("E-WALLET")
        brand.setObjectName("Brand")
        layout.addWidget(brand)
        layout.addSpacing(20)

        items = [
            ("Dashboard", "dashboard"),
            ("My wallets", "wallets"),
            ("Deposit", "deposit"),
            ("Withdraw", "withdraw"),
            ("Transfer", "transfer"),
            ("Transaction history", "history"),
            ("Profile", "profile"),
            ("Settings", "settings"),
        ]
        if is_admin:
            items.extend([
                ("Admin · Users", "admin_users"),
                ("Admin · Wallets", "admin_wallets"),
                ("Admin · Transactions", "admin_transactions"),
                ("Admin · Audit logs", "admin_audit"),
            ])
        for label, route in items:
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.clicked.connect(lambda checked=False, key=route: self.navigated.emit(key))
            layout.addWidget(button)
        layout.addStretch()
        logout = QPushButton("Sign out")
        logout.setObjectName("DangerButton")
        logout.clicked.connect(self.logout_requested.emit)
        layout.addWidget(logout)
