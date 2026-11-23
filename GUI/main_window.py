from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget, QVBoxLayout, QFrame, QLabel, QStackedWidget
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
from GUI.pages.bank_page import BankPage
from GUI.pages.personal_details_page import PersonalDetailsPage
from GUI.pages.statistics_page import StatisticsPage
from GUI.pages.activity_page import ActivityPage
from GUI.pages.admin.users_page import AdminUsersPage
from GUI.pages.admin.transactions_page import AdminTransactionsPage
from GUI.pages.admin.wallets_page import AdminWalletsPage
from GUI.pages.admin.audit_logs_page import AdminAuditLogsPage
from GUI.pages.admin.system_overview_page import AdminOverviewPage
from GUI.pages.admin.bank_accounts_page import AdminBankAccountsPage
from GUI.pages.admin.bank_statistics_page import AdminBankStatisticsPage
from GUI.pages.admin.partner_banks_page import AdminPartnerBanksPage
from GUI.pages.admin.user_profile_page import AdminUserProfilePage
from GUI.widgets.sidebar import Sidebar
from GUI.widgets.toast import notify


PAGE_TITLES = {
    "dashboard": "Overview", "wallets": "My wallets", "deposit": "Add money",
    "withdraw": "Withdraw", "transfer": "Transfer", "history": "Transactions",
    "profile": "Account profile", "personal_details": "Personal details", "banks": "Bank connections",
    "statistics": "My insights", "activity": "Account activity", "settings": "Security settings",
    "admin_overview": "System overview", "admin_users": "Customer management",
    "admin_user_profile": "Customer profiles", "admin_wallets": "Wallet operations",
    "admin_transactions": "All transactions", "admin_audit": "Audit trail",
    "admin_bank_accounts": "Bank connections", "admin_partner_banks": "Partner bank management",
    "admin_bank_statistics": "Partner bank analytics",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurelia · E-Wallet")
        self.resize(1440, 900)
        self.setMinimumSize(1080, 700)
        self.api = Api()
        self.state = AppState()
        self.root_stack = QWidget()
        self.setCentralWidget(self.root_stack)
        root = QVBoxLayout(self.root_stack)
        root.setContentsMargins(0, 0, 0, 0)
        self.root_pages = QStackedWidget()
        root.addWidget(self.root_pages)

        self.login_page = LoginPage(self.api, self.open_workspace, self.open_register)
        self.register_page = RegisterPage(self.api, self.open_login, self.open_login)
        self.root_pages.addWidget(self.login_page)
        self.root_pages.addWidget(self.register_page)
        self.root_pages.setCurrentWidget(self.login_page)
        self.workspace = None
        self._api_version_warning_shown = False

    def open_login(self):
        self.root_pages.setCurrentWidget(self.login_page)

    def open_register(self):
        self.root_pages.setCurrentWidget(self.register_page)

    def open_workspace(self, user):
        # Detect the common client/server mismatch before the user opens a page
        # whose endpoint may not exist on an older, still-running API process.
        if not self._api_version_warning_shown:
            try:
                server_info = self.api.health()
                if server_info.get("api_version") != "1.3.0":
                    notify(
                        self,
                        "API server needs updating",
                        "The desktop app is newer than the REST API server. "
                        "Some pages (including Personal details and the new Admin pages) "
                        "may report 'Unknown API operation'. Update the SERVER source from "
                        "this same ZIP, stop the old server, and restart it with:\n\n"
                        "python -m uvicorn src.api:app --host 0.0.0.0 --port 8000",
                        True,
                    )
                self._api_version_warning_shown = True
            except Exception:
                # Login already succeeded; leave the normal page-level error handling
                # to report a transient health-check failure if an API call is made.
                pass
        if self.workspace is not None:
            self.root_pages.removeWidget(self.workspace)
            self.workspace.deleteLater()
        self.state.user = user
        self.workspace = QWidget()
        layout = QHBoxLayout(self.workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.sidebar = Sidebar(self.state.is_admin)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 28, 24)
        content_layout.setSpacing(16)
        self.header = QFrame(); self.header.setObjectName("AppHeader")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 14, 20, 14)
        self.header_title = QLabel("Overview"); self.header_title.setObjectName("HeaderTitle")
        self.header_subtitle = QLabel("Your money, clearly organized."); self.header_subtitle.setObjectName("MutedLabel")
        title_box = QVBoxLayout(); title_box.setSpacing(2); title_box.addWidget(self.header_title); title_box.addWidget(self.header_subtitle)
        header_layout.addLayout(title_box); header_layout.addStretch()
        self.user_badge = QLabel(); self.user_badge.setObjectName("UserBadge")
        header_layout.addWidget(self.user_badge)
        content_layout.addWidget(self.header)
        self.router = Router()
        content_layout.addWidget(self.router, 1)
        layout.addWidget(self.sidebar)
        layout.addWidget(content, 1)

        self.pages = {
            "dashboard": DashboardPage(self.api, self.state),
            "wallets": WalletPage(self.api, self.state),
            "deposit": DepositPage(self.api, self.state),
            "withdraw": WithdrawPage(self.api, self.state),
            "transfer": TransferPage(self.api, self.state),
            "history": HistoryPage(self.api, self.state),
            "profile": ProfilePage(self.api, self.state),
            "personal_details": PersonalDetailsPage(self.api, self.state),
            "banks": BankPage(self.api, self.state),
            "statistics": StatisticsPage(self.api, self.state),
            "activity": ActivityPage(self.api, self.state),
            "settings": SettingsPage(self.api, self.state),
        }
        if self.state.is_admin:
            self.pages.update({
                "admin_overview": AdminOverviewPage(self.api, self.state),
                "admin_users": AdminUsersPage(self.api, self.state),
                "admin_user_profile": AdminUserProfilePage(self.api, self.state),
                "admin_wallets": AdminWalletsPage(self.api, self.state),
                "admin_transactions": AdminTransactionsPage(self.api, self.state),
                "admin_audit": AdminAuditLogsPage(self.api, self.state),
                "admin_bank_accounts": AdminBankAccountsPage(self.api, self.state),
                "admin_partner_banks": AdminPartnerBanksPage(self.api, self.state),
                "admin_bank_statistics": AdminBankStatisticsPage(self.api, self.state),
            })
        for key, page in self.pages.items():
            self.router.register(key, page)
        self.sidebar.navigated.connect(self.navigate)
        self.sidebar.logout_requested.connect(self.logout)
        if self.state.is_admin:
            self.pages["admin_users"].profile_requested.connect(self.open_admin_user_profile)
        self.root_pages.addWidget(self.workspace)
        self.root_pages.setCurrentWidget(self.workspace)
        self.user_badge.setText(f"●  {user.get('user_name', 'Member')}   ·   {'ADMIN' if self.state.is_admin else 'PERSONAL'}")
        self.navigate("admin_overview" if self.state.is_admin else "dashboard")

    def open_admin_user_profile(self, user_id):
        page = self.pages.get("admin_user_profile")
        if page:
            page.load_user(user_id)
        self.navigate("admin_user_profile")

    def navigate(self, name):
        self.router.go(name)
        self.sidebar.set_active(name)
        self.header_title.setText(PAGE_TITLES.get(name, "E-Wallet"))
        self.header_subtitle.setText("Administrator workspace" if name.startswith("admin_") else "Your money, clearly organized.")
        page = self.pages.get(name)
        if page and hasattr(page, "refresh"):
            page.refresh()

    def logout(self):
        try:
            self.api.logout(self.state.user_id)
        except Exception as error:
            notify(self, "Sign out warning", error, True)
        self.state.clear()
        self.root_pages.setCurrentWidget(self.login_page)
