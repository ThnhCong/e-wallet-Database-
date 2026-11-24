# src/container.py
"""Noi duy nhat biet cach noi 4 module (repository -> service -> controller).
Tat ca repository dung CHUNG 1 connection, nen audit log nam cung giao dich DB voi thao tac.

Phu thuoc giua cac module (mot chieu, khong vong):
    user -> wallet -> audit_logs        transaction -> wallet, audit_logs
    user_profile, bank (-> wallet), statistics: doc lap;  admin -> tat ca
"""
from dataclasses import dataclass

from src.modules.admin.admin_controller import AdminController
from src.modules.admin.admin_repository import AdminRepository
from src.modules.admin.admin_service import AdminService
from src.modules.audit_logs.audit_controller import AuditController
from src.modules.audit_logs.audit_repository import AuditRepository
from src.modules.audit_logs.audit_service import AuditService
from src.modules.bank.bank_controller import BankController
from src.modules.bank.bank_repository import BankRepository
from src.modules.bank.bank_service import BankService
from src.modules.statistics.statistics_controller import StatisticsController
from src.modules.statistics.statistics_repository import StatisticsRepository
from src.modules.statistics.statistics_service import StatisticsService
from src.modules.user_profile.user_profile_controller import UserProfileController
from src.modules.user_profile.user_profile_repository import UserProfileRepository
from src.modules.user_profile.user_profile_service import UserProfileService
from src.modules.transaction.transaction_controller import TransactionController
from src.modules.transaction.transaction_repository import TransactionRepository
from src.modules.transaction.transaction_service import TransactionService
from src.modules.user.user_controller import UserController
from src.modules.user.user_repository import UserRepository
from src.modules.user.user_service import UserService
from src.modules.wallet.wallet_controller import WalletController
from src.modules.wallet.wallet_repository import WalletRepository
from src.modules.wallet.wallet_service import WalletService


@dataclass(frozen=True)
class Controllers:
    users: UserController
    wallets: WalletController
    transactions: TransactionController
    audit: AuditController
    profiles: UserProfileController
    banks: BankController
    statistics: StatisticsController
    admin: AdminController


def build_controllers(conn):
    audit_service = AuditService(AuditRepository(conn))

    wallet_repo = WalletRepository(conn)
    wallet_service = WalletService(wallet_repo, audit_service)

    user_service = UserService(UserRepository(conn), audit_service, wallet_service)

    profile_repo = UserProfileRepository(conn)
    bank_repo = BankRepository(conn)
    transaction_service = TransactionService(TransactionRepository(conn), wallet_repo, audit_service, bank_repo)
    stats_repo = StatisticsRepository(conn)
    tx_repo = transaction_service.tx_repo
    admin_service = AdminService(AdminRepository(conn), wallet_repo, tx_repo, audit_service.audit_repo, audit_service,
                                 profile_repo, bank_repo, stats_repo)

    return Controllers(
        users=UserController(user_service),
        wallets=WalletController(wallet_service),
        transactions=TransactionController(transaction_service),
        audit=AuditController(audit_service),
        profiles=UserProfileController(UserProfileService(profile_repo, audit_service)),
        banks=BankController(BankService(bank_repo, wallet_repo, audit_service)),
        statistics=StatisticsController(StatisticsService(stats_repo)),
        admin=AdminController(admin_service),
    )