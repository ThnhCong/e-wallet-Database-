from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget, QStackedWidget
from GUI.app_state import AppState
from GUI.core.api import Api
from GUI.core.router import Router
from GUI.pages.auth.login_page import LoginPage
from GUI.pages.auth.register_page import RegisterPage
from GUI.pages.dashboard_page import DashboardPage
from GUI.pages.wallet_page import WalletPage
from GUI.pages.deposit_page import DepositPage
from GUI.pages.withdraw_page import WithdrawPage
from GUI.pages.transfer_page import TransferPage
from GUI.pages.history_page import HistoryPage
from GUI.pages.profile_page import ProfilePage
from GUI.pages.settings_page import SettingsPage
from GUI.pages.admin.users_page import AdminUsersPage
from GUI.pages.admin.transactions_page import AdminTransactionsPage
from GUI.pages.admin.wallets_page import AdminWalletsPage
from GUI.pages.admin.audit_logs_page import AdminAuditLogsPage
from GUI.widgets.sidebar import Sidebar
from GUI.widgets.toast import notify


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("E-Wallet Management System")
        self.resize(1280, 820)
        self.setMinimumSize(960, 640)
        self.api = Api()
        self.state = AppState()
        self.root_stack = QStackedWidget()
        self.setCentralWidget(self.root_stack)

        self.login_page = LoginPage(self.api, self.open_workspace, self.open_register)
        self.register_page = RegisterPage(self.api, self.open_login, self.open_login)
        self.root_stack.addWidget(self.login_page)
        self.root_stack.addWidget(self.register_page)
        self.root_stack.setCurrentWidget(self.login_page)
        self.workspace = None

    def open_login(self):
        self.root_stack.setCurrentWidget(self.login_page)

    def open_register(self):
        self.root_stack.setCurrentWidget(self.register_page)

    def open_workspace(self, user):
        if self.workspace is not None:
            self.root_stack.removeWidget(self.workspace)
            self.workspace.deleteLater()
        self.state.user = user
        self.workspace = QWidget()
        layout = QHBoxLayout(self.workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar = Sidebar(self.state.is_admin)
        self.router = Router()
        layout.addWidget(self.sidebar)
        layout.addWidget(self.router, 1)
        self.pages = {
            "dashboard": DashboardPage(self.api, self.state),
            "wallets": WalletPage(self.api, self.state),
            "deposit": DepositPage(self.api, self.state),
            "withdraw": WithdrawPage(self.api, self.state),
            "transfer": TransferPage(self.api, self.state),
            "history": HistoryPage(self.api, self.state),
            "profile": ProfilePage(self.api, self.state),
            "settings": SettingsPage(self.api, self.state),
        }
        if self.state.is_admin:
            self.pages.update({
                "admin_users": AdminUsersPage(self.api, self.state),
                "admin_wallets": AdminWalletsPage(self.api, self.state),
                "admin_transactions": AdminTransactionsPage(self.api, self.state),
                "admin_audit": AdminAuditLogsPage(self.api, self.state),
            })
        for key, page in self.pages.items():
            self.router.register(key, page)
        self.sidebar.navigated.connect(self.navigate)
        self.sidebar.logout_requested.connect(self.logout)
        old = self.root_stack.indexOf(self.workspace)
        if old >= 0:
            self.root_stack.removeWidget(self.workspace)
        self.root_stack.addWidget(self.workspace)
        self.root_stack.setCurrentWidget(self.workspace)
        self.navigate("dashboard")

    def navigate(self, name):
        self.router.go(name)
        page = self.pages.get(name)
        if page and hasattr(page, "refresh"):
            page.refresh()

    def logout(self):
        try:
            self.api.logout(self.state.user_id)
        except Exception as error:
            notify(self, "Sign out warning", error, True)
        self.state.clear()
        self.root_stack.setCurrentWidget(self.login_page)
