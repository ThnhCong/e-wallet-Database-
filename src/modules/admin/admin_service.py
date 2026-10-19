# src/modules/admin/admin_service.py
"""Nghiep vu quan tri (bao cao 1.2.H): xem user, vi, giao dich, audit log; khoa / mo khoa vi cua bat ky ai.

QUY TAC AN TOAN
  * Moi ham cong khai cua AdminService PHAI co @admin_action. Decorator mo giao dich DB, doc role cua
    admin_id TU DATABASE (khong tin du lieu phia GUI), roi moi chay ham. Day la diem kiem tra quyen duy nhat.
  * Audit log cua thao tac ghi nam cung giao dich: thao tac loi thi log cung rollback.
  * Khoa / mo khoa vi ghi action LOCK_WALLET / UNLOCK_WALLET voi user_id = ADMIN (nguoi lam). Phan biet voi
    chu vi tu khoa bang cach so user_id cua log voi wallets.user_id.
"""
from functools import wraps

from src.common.db import db_transaction
from src.common.errors import ServiceError
from src.common.query_params import DEFAULT_ADMIN_LIMIT, normalize_limit, parse_optional_id
from src.common.validators import TX_STATUSES, TX_TYPES, parse_choice, parse_id
from src.modules.audit_logs.audit_actions import AUDIT_ACTIONS, AuditAction

ROLE_ADMIN = "admin"


def admin_action(operation):
    """Boc mot ham cua AdminService: (1) mo giao dich DB, (2) kiem tra admin, (3) chay ham, (4) commit / rollback."""
    def decorator(method):
        @wraps(method)
        def wrapper(self, admin_id, *args, **kwargs):
            with db_transaction(self.conn, operation):
                self._require_admin(admin_id)
                return method(self, admin_id, *args, **kwargs)
        wrapper.is_admin_action = True          # test_admin.py dung dau hieu nay de bat ham quen decorator
        return wrapper
    return decorator


class AdminService:

    def __init__(self, admin_repository, wallet_repository, transaction_repository, audit_repository, audit_service):
        self.admin_repo = admin_repository
        self.wallet_repo = wallet_repository
        self.tx_repo = transaction_repository
        self.audit_repo = audit_repository          # chi de DOC log
        self.audit = audit_service                  # de GHI log (cung giao dich)
        self.conn = admin_repository.conn

    def _require_admin(self, admin_id):
        role = self.admin_repo.get_role(admin_id)
        if role is None or str(role).lower() != ROLE_ADMIN:
            raise ServiceError("FORBIDDEN", "Administrator access is required.")

    # ---------------------------------------------------------------- xem
    @admin_action("View users")
    def list_users(self, admin_id, limit=DEFAULT_ADMIN_LIMIT):
        return self.admin_repo.list_users(normalize_limit(limit))

    @admin_action("View wallets")
    def list_wallets(self, admin_id, user_id=None, limit=DEFAULT_ADMIN_LIMIT):
        return self.wallet_repo.list_all_wallets(parse_optional_id(user_id, "User"), normalize_limit(limit))

    @admin_action("View transactions")
    def list_transactions(self, admin_id, tx_type=None, status=None, limit=DEFAULT_ADMIN_LIMIT):
        return self.tx_repo.list_all_transactions(parse_choice(tx_type, TX_TYPES, "Type"),
                                                  parse_choice(status, TX_STATUSES, "Status"),
                                                  normalize_limit(limit))

    @admin_action("View transaction")
    def get_transaction(self, admin_id, transaction_id):
        tx = self.tx_repo.get_transaction(parse_id(transaction_id, "Transaction"))
        if tx is None:
            raise ServiceError("TRANSACTION_NOT_FOUND", "The transaction does not exist.")
        return tx

    @admin_action("View audit logs")
    def list_audit_logs(self, admin_id, user_id=None, action=None, limit=DEFAULT_ADMIN_LIMIT):
        return self.audit_repo.list_logs(user_id=parse_optional_id(user_id, "User"),
                                         action=parse_choice(action, AUDIT_ACTIONS, "Action"),
                                         limit=normalize_limit(limit))

    # ---------------------------------------------------------------- khoa / mo khoa vi (moi vi)
    @admin_action("Update wallet")
    def set_wallet_locked(self, admin_id, wallet_id, locked):
        wallet_id = parse_id(wallet_id, "Wallet")
        status, action = (("LOCKED", AuditAction.LOCK_WALLET) if locked
                          else ("ACTIVE", AuditAction.UNLOCK_WALLET))

        self.wallet_repo.lock_wallets(wallet_id)                     # SELECT ... FOR UPDATE
        wallet = self.wallet_repo.get_wallet_by_id(wallet_id)
        if wallet is None:
            raise ServiceError("WALLET_NOT_FOUND", "The wallet does not exist.")
        if wallet["status"] == status:                               # khong ghi log "ma" cho thao tac khong doi gi
            raise ServiceError("WALLET_UNCHANGED", f"The wallet is already {status.lower()}.")

        self.wallet_repo.set_wallet_status(wallet_id, status)
        self.audit.record(admin_id, action, wallet_id=wallet_id)
        return self.wallet_repo.get_wallet_by_id(wallet_id)
