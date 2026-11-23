from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QScrollArea, QWidget


class Sidebar(QFrame):
    navigated = Signal(str)
    logout_requested = Signal()

    def __init__(self, is_admin=False, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(252)
        self.buttons = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 24, 18, 20)
        layout.setSpacing(6)

        brand_row = QHBoxLayout()
        mark = QLabel("A"); mark.setObjectName("BrandMark")
        brand = QLabel("AURELIA"); brand.setObjectName("Brand")
        brand_row.addWidget(mark); brand_row.addWidget(brand); brand_row.addStretch()
        layout.addLayout(brand_row)
        tagline = QLabel("DIGITAL WALLET"); tagline.setObjectName("BrandCaption")
        layout.addWidget(tagline)
        layout.addSpacing(22)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        menu = QWidget(); menu_layout = QVBoxLayout(menu); menu_layout.setContentsMargins(0, 0, 4, 0); menu_layout.setSpacing(5)
        self._section(menu_layout, "PERSONAL SPACE")
        items = [
            ("◈", "Overview", "dashboard"), ("▣", "My wallets", "wallets"),
            ("＋", "Add money", "deposit"), ("↗", "Withdraw", "withdraw"),
            ("⇄", "Transfer", "transfer"), ("▤", "Transactions", "history"),
            ("⌂", "Bank connections", "banks"), ("◷", "My insights", "statistics"),
            ("◎", "Account activity", "activity"),
        ]
        for icon, label, route in items: self._add_item(menu_layout, icon, label, route)
        self._section(menu_layout, "MY ACCOUNT")
        for icon, label, route in [("♙", "Account profile", "profile"), ("✧", "Personal details", "personal_details"), ("⚙", "Security settings", "settings")]:
            self._add_item(menu_layout, icon, label, route)
        if is_admin:
            self._section(menu_layout, "ADMINISTRATION")
            admin_items = [
                ("▦", "System overview", "admin_overview"), ("♧", "Customers", "admin_users"),
                ("⌕", "Customer profile", "admin_user_profile"), ("▣", "Wallet operations", "admin_wallets"),
                ("⇄", "All transactions", "admin_transactions"), ("▤", "Audit trail", "admin_audit"),
                ("⌂", "Bank connections", "admin_bank_accounts"),
                ("＋", "Partner banks", "admin_partner_banks"),
                ("◷", "Bank analytics", "admin_bank_statistics"),
            ]
            for icon, label, route in admin_items: self._add_item(menu_layout, icon, label, route)
        menu_layout.addStretch(1)
        scroll.setWidget(menu)
        layout.addWidget(scroll, 1)
        layout.addStretch(1)
        footer = QLabel("SECURE · PRIVATE · SIMPLE"); footer.setObjectName("SidebarFooter")
        layout.addWidget(footer)
        logout = QPushButton("↪     Sign out")
        logout.setObjectName("LogoutButton")
        logout.setMinimumHeight(44)
        logout.clicked.connect(self.logout_requested.emit)
        layout.addWidget(logout)

    def _section(self, layout, text):
        label = QLabel(text); label.setObjectName("NavSection")
        layout.addSpacing(12); layout.addWidget(label)

    def _add_item(self, layout, icon, label, route):
        button = QPushButton(f"{icon}     {label}")
        button.setObjectName("NavButton")
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumHeight(40)
        button.clicked.connect(lambda checked=False, key=route: self.navigated.emit(key))
        layout.addWidget(button)
        self.buttons[route] = button

    def set_active(self, route):
        for key, button in self.buttons.items():
            button.setChecked(key == route)
