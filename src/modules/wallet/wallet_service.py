# src/modules/wallet/wallet_service.py
"""Nghiep vu vi: tao vi, xem vi, khoa / mo khoa, va cac truy van quan tri.
Giao dich tai chinh (nap / rut / chuyen) thuoc module transaction."""
from src.common.db import db_transaction
from src.common.errors import ServiceError
from src.common.query_params import DEFAULT_ADMIN_LIMIT, normalize_limit, parse_optional_id
from src.common.validators import parse_currency, parse_id
from src.modules.audit_logs.audit_actions import AuditAction


class WalletService:

    def __init__(self, wallet_repository, audit_service):
        self.wallet_repo = wallet_repository
        self.audit = audit_service
        self.conn = wallet_repository.conn

    def _own_wallet(self, user_id, wallet_id):
        wallet = self.wallet_repo.get_wallet_by_id(wallet_id)
        if wallet is None:
            raise ServiceError("WALLET_NOT_FOUND", "The wallet does not exist.")
        if wallet["user_id"] != user_id:
            raise ServiceError("FORBIDDEN", "This wallet does not belong to you.")
        return wallet

    # ---------------------------------------------------------------- tao vi
    def create_wallet(self, user_id, currency):
        currency = parse_currency(currency)
        with db_transaction(self.conn, "Create wallet"):
            wallet_id = self.create_in_open_transaction(user_id, currency)
            return self.wallet_repo.get_wallet_by_id(wallet_id)

    def create_in_open_transaction(self, user_id, currency):
        """INSERT vi + audit CREATE_WALLET, KHONG tu mo giao dich. Dung khi mot service khac
        (vd dang ky tai khoan) muon tao vi trong CUNG giao dich cua no. Tra ve wallet_id."""
        wallet_id = self.wallet_repo.create_wallet(user_id, currency)
        self.audit.record(user_id, AuditAction.CREATE_WALLET, wallet_id=wallet_id)
        return wallet_id

    # ---------------------------------------------------------------- xem vi
    def list_wallets(self, user_id):
        with db_transaction(self.conn, "View wallets"):
            return self.wallet_repo.list_wallets_by_user(user_id)

    def get_wallet_by_id(self, user_id, wallet_id):
        wallet_id = parse_id(wallet_id, "Wallet")
        with db_transaction(self.conn, "View wallet"):
            return self._own_wallet(user_id, wallet_id)

    # ---------------------------------------------------------------- khoa / mo khoa
    def set_locked(self, user_id, wallet_id, locked):
        wallet_id = parse_id(wallet_id, "Wallet")
        status, action = (("LOCKED", AuditAction.LOCK_WALLET) if locked
                          else ("ACTIVE", AuditAction.UNLOCK_WALLET))
        with db_transaction(self.conn, "Update wallet"):
            self.wallet_repo.lock_wallets(wallet_id)
            self._own_wallet(user_id, wallet_id)
            self.wallet_repo.set_wallet_status(wallet_id, status)
            self.audit.record(user_id, action, wallet_id=wallet_id)
            return self.wallet_repo.get_wallet_by_id(wallet_id)

    # ---------------------------------------------------------------- quan tri
    def list_all_wallets(self, user_id=None, limit=DEFAULT_ADMIN_LIMIT):
        user_id = parse_optional_id(user_id, "User")
        limit = normalize_limit(limit)
        with db_transaction(self.conn, "View wallets"):
            return self.wallet_repo.list_all_wallets(user_id, limit)