# src/modules/admin/admin_service.py
"""Nghiep vu quan tri (bao cao 1.2.H): xem user, vi, giao dich, audit log; khoa / mo khoa vi cua bat ky ai.

QUY TAC AN TOAN
  * Moi ham cong khai cua AdminService PHAI co @admin_action. Decorator mo giao dich DB, kiem tra admin_id theo danh sach admin_accounts
    trong config server-side, roi moi chay ham. Day la diem kiem tra quyen duy nhat.
  * Audit log cua thao tac ghi nam cung giao dich: thao tac loi thi log cung rollback.
  * Khoa / mo khoa vi ghi action LOCK_WALLET / UNLOCK_WALLET voi user_id = ADMIN (nguoi lam). Phan biet voi
    chu vi tu khoa bang cach so user_id cua log voi wallets.user_id.
"""
from functools import wraps

from src.common.db import db_transaction
from src.common.errors import ServiceError
from src.common.query_params import DEFAULT_ADMIN_LIMIT, normalize_limit, parse_optional_id
from src.common.validators import TX_STATUSES, TX_TYPES, parse_choice, parse_id, require_text
from src.modules.audit_logs.audit_actions import AUDIT_ACTIONS, AuditAction
from src.config.settings import get_settings


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

    def __init__(self, admin_repository, wallet_repository, transaction_repository, audit_repository, audit_service,
                 profile_repository=None, bank_repository=None, statistics_repository=None):
        self.admin_repo = admin_repository
        self.profile_repo = profile_repository
        self.bank_repo = bank_repository
        self.stats_repo = statistics_repository
        self.wallet_repo = wallet_repository
        self.tx_repo = transaction_repository
        self.audit_repo = audit_repository          # chi de DOC log
        self.audit = audit_service                  # de GHI log (cung giao dich)
        self.conn = admin_repository.conn

    def _require_admin(self, admin_id):
        admin_accounts = get_settings().get("admin_accounts", [])
        if not self.admin_repo.is_admin(admin_id, admin_accounts):
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

    # ---------------------------------------------------------------- ho so, ngan hang, thong ke
    @admin_action("View user profile")
    def get_user_profile(self, admin_id, user_id):
        return self.profile_repo.get_profile(parse_id(user_id, "User"))

    @admin_action("View user profiles")
    def list_user_profiles(self, admin_id, page=1, page_size=20, search=None, sex=None, country=None,
                           sort_by="created_at", sort_order="DESC"):
        page = parse_id(page, "Page")
        page_size = normalize_limit(page_size, default=20, maximum=100)
        sort_by = str(sort_by or "created_at").strip().lower()
        if sort_by not in ("created_at", "user_id"):
            raise ServiceError("SORT_INVALID", "Sort field must be created_at or user_id.")
        sort_order = str(sort_order or "DESC").strip().upper()
        if sort_order not in ("ASC", "DESC"):
            raise ServiceError("SORT_INVALID", "Sort order must be ASC or DESC.")
        search = (str(search).strip()[:255] if search is not None and str(search).strip() else None)
        country = (str(country).strip()[:100] if country is not None and str(country).strip() else None)
        sex = parse_choice(sex, ("MALE", "FEMALE", "OTHER"), "Sex")
        offset = (page - 1) * page_size
        rows = self.profile_repo.list_profiles_for_admin(
            search, sex, country, sort_by, sort_order, page_size, offset
        ) or []

        # The SQL procedure returns a sentinel row with user_profile_id=NULL
        # when no matching profile exists. It keeps the total count available
        # even when the page contains zero records.
        total = int(rows[0].get("total_count") or 0) if rows else 0
        items = [
            {key: value for key, value in row.items() if key != "total_count"}
            for row in rows
            if row.get("user_profile_id") is not None
        ]
        total_pages = (total + page_size - 1) // page_size
        return {
            "items": items,
            "total": total,
            "page": page if total_pages else 1,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    @admin_action("View bank accounts")
    def list_bank_accounts(self, admin_id, limit=DEFAULT_ADMIN_LIMIT):
        return self.bank_repo.list_all_links(normalize_limit(limit))

    @admin_action("View partner banks")
    def list_partner_banks(self, admin_id):
        return self.bank_repo.list_banks()

    @admin_action("Add partner bank")
    def create_partner_bank(self, admin_id, name):
        name = require_text(name, "Bank name", 100)
        return self.bank_repo.create_partner_bank(name)

    @admin_action("Delete partner bank")
    def delete_partner_bank(self, admin_id, bank_id):
        bank_id = parse_id(bank_id, "Bank")
        return self.bank_repo.delete_partner_bank(bank_id)

    @admin_action("View bank statistics")
    def bank_statistics(self, admin_id):
        return self.stats_repo.bank_statistics()

    @admin_action("View system statistics")
    def system_statistics(self, admin_id):
        return self.stats_repo.system_statistics()
