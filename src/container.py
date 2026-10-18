# src/container.py
"""Noi duy nhat biet cach noi 4 module (repository -> service -> controller).
Tat ca repository dung CHUNG 1 connection, nen audit log nam cung giao dich DB voi thao tac.

Phu thuoc giua cac module (mot chieu, khong vong):
    user -> wallet -> audit_logs        transaction -> wallet, audit_logs
"""
from dataclasses import dataclass

from src.modules.audit_logs.audit_controller import AuditController
from src.modules.audit_logs.audit_repository import AuditRepository
from src.modules.audit_logs.audit_service import AuditService
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


def build_controllers(conn):
    audit_service = AuditService(AuditRepository(conn))

    wallet_repo = WalletRepository(conn)
    wallet_service = WalletService(wallet_repo, audit_service)

    user_service = UserService(UserRepository(conn), audit_service, wallet_service)
    transaction_service = TransactionService(TransactionRepository(conn), wallet_repo, audit_service)

    return Controllers(
        users=UserController(user_service),
        wallets=WalletController(wallet_service),
        transactions=TransactionController(transaction_service),
        audit=AuditController(audit_service),
    )