from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from GUI.pages.common import make_button, FormNavigation
from GUI.widgets.toast import notify


class LoginPage(QWidget):
    def __init__(self, api, on_login, on_register, parent=None):
        super().__init__(parent)
        self.api = api
        self.on_login = on_login
        root = QHBoxLayout(self)
        root.setContentsMargins(44, 36, 44, 36)
        root.setSpacing(26)
        hero = QFrame(); hero.setObjectName("AuthHero")
        hero_layout = QVBoxLayout(hero); hero_layout.setContentsMargins(42, 42, 42, 42); hero_layout.setSpacing(14)
        mark = QLabel("AURELIA"); mark.setObjectName("AuthBrand")
        eyebrow = QLabel("A MORE THOUGHTFUL WAY TO BANK"); eyebrow.setObjectName("AuthEyebrow")
        headline = QLabel("Your everyday\nmoney, made\nsimpler."); headline.setObjectName("AuthHeroTitle")
        description = QLabel("One elegant space to manage wallets, move money and understand your financial activity.")
        description.setObjectName("AuthHeroText"); description.setWordWrap(True)
        hero_layout.addWidget(mark); hero_layout.addSpacing(55); hero_layout.addWidget(eyebrow); hero_layout.addWidget(headline)
        hero_layout.addWidget(description); hero_layout.addStretch()
        trust = QLabel("●  Secure session     ●  Clear activity     ●  Multiple wallets"); trust.setObjectName("AuthHeroText")
        hero_layout.addWidget(trust)
        root.addWidget(hero, 1)

        card = QFrame(); card.setObjectName("AuthCard"); card.setMaximumWidth(440)
        form = QVBoxLayout(card); form.setContentsMargins(36, 40, 36, 36); form.setSpacing(13)
        title = QLabel("Welcome back"); title.setObjectName("AuthTitle")
        subtitle = QLabel("Sign in to continue to your wallet."); subtitle.setObjectName("MutedLabel")
        self.phone = QLineEdit(); self.phone.setPlaceholderText("Phone number"); self.phone.setMinimumHeight(48)
        self.password = QLineEdit(); self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password); self.password.setMinimumHeight(48)
        sign_in = make_button("Sign in securely  →", self.submit)
        register = QPushButton("New to Aurelia?  Create an account")
        register.setObjectName("TextButton"); register.clicked.connect(on_register)
        form.addStretch(); form.addWidget(title); form.addWidget(subtitle); form.addSpacing(20)
        form.addWidget(QLabel("PHONE NUMBER")); form.addWidget(self.phone)
        form.addWidget(QLabel("PASSWORD")); form.addWidget(self.password)
        form.addSpacing(8); form.addWidget(sign_in); form.addWidget(register); form.addStretch()
        root.addStretch(0); root.addWidget(card, 0, Qt.AlignmentFlag.AlignVCenter)
        self.form_navigation = FormNavigation(self, [self.phone, self.password], self.submit)

    def submit(self):
        try:
            user = self.api.login(self.phone.text().strip(), self.password.text())
            self.on_login(user)
        except Exception as error:
            notify(self, "Sign in failed", error, True)
