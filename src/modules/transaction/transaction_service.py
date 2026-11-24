# src/modules/transaction/transaction_service.py
"""Luong tai chinh: khoa vi -> INSERT PENDING -> UPDATE SUCCESS -> audit -> COMMIT.
Service KHONG tu cong/tru balance hay han muc tuan: trigger trong DB lam.
Loi nao cung ROLLBACK het, tru truong hop duy nhat: giao dich PENDING da luu nhung trigger
AFTER UPDATE tu choi -> giao dich duoc danh dau FAIL (khong doi so du) roi moi bao loi (bao cao 2.2.2.B)."""
from src.common.db import db_transaction
from src.common.errors import ServiceError
from src.common.query_params import DEFAULT_ADMIN_LIMIT, DEFAULT_LIMIT, normalize_limit
from src.common.validators import TX_STATUSES, TX_TYPES, parse_amount, parse_choice, parse_id
from src.modules.audit_logs.audit_actions import AuditAction

DEPOSIT, WITHDRAW, TRANSFER = "DEPOSIT", "WITHDRAW", "TRANSFER"
_AUDIT_ACTION_OF = {DEPOSIT: AuditAction.DEPOSIT, WITHDRAW: AuditAction.WITHDRAW}


class TransactionService:

    def __init__(self, transaction_repository, wallet_repository, audit_service, bank_repository=None):
        self.tx_repo = transaction_repository
        self.wallet_repo = wallet_repository        # chi dung de khoa vi va doc so du sau giao dich
        self.audit = audit_service
        self.bank_repo = bank_repository
        self.conn = transaction_repository.conn

    # ---------------------------------------------------------------- nap / rut / chuyen
    def deposit(self, user_id, wallet_id, amount):
        return self._execute("Deposit", DEPOSIT, user_id,
                             None, parse_id(wallet_id, "Wallet"), parse_amount(amount))

    def withdraw(self, user_id, wallet_id, amount):
        return self._execute("Withdrawal", WITHDRAW, user_id,
                             parse_id(wallet_id, "Wallet"), None, parse_amount(amount))

    def transfer(self, user_id, sender_wallet_id, receiver_wallet_id, amount):
        sender = parse_id(sender_wallet_id, "Sender wallet")
        receiver = parse_id(receiver_wallet_id, "Receiver wallet")
        if sender == receiver:
            raise ServiceError("SAME_WALLET", "You cannot transfer to the same wallet.")
        return self._execute("Transfer", TRANSFER, user_id, sender, receiver, parse_amount(amount))

    def _execute(self, operation, tx_type, user_id, sender_id, receiver_id, amount):
        """Trinh tu chung cua 1 giao dich tai chinh trong 1 giao dich DB."""
        failure = None
        with db_transaction(self.conn, operation):
            wallets = self.wallet_repo.lock_wallets(sender_id, receiver_id)      # thu tu id tang dan
            own_id = self._authorize(tx_type, user_id, sender_id, receiver_id, wallets)
            if self.bank_repo is not None:
                for wid in (sender_id, receiver_id):
                    if wid is not None and not self.bank_repo.has_active_link(wid):
                        raise ServiceError("BANK_NOT_LINKED", f"Wallet #{wid} must be linked to an active partner bank before transacting.")

            tx_id = self.tx_repo.create_transaction(sender_id, receiver_id, tx_type, amount)   # PENDING
            failure = self._settle(tx_id)                                                      # -> SUCCESS / FAIL
            if failure is None:
                self._record_audit(tx_type, user_id, tx_id, sender_id, receiver_id, wallets)
                wallet = self.wallet_repo.get_wallet_by_id(own_id)

        if failure is not None:
            self._reraise(operation, failure)

        return {"transaction_id": tx_id, "type": tx_type, "status": "SUCCESS", "amount": amount,
                "wallet_id": own_id, "balance": wallet["balance"], "remain_limit_week": wallet["remain_limit_week"]}

    @staticmethod
    def _authorize(tx_type, user_id, sender_id, receiver_id, wallets):
        """Vi phai ton tai va thuoc ve nguoi thao tac. Tra ve wallet_id cua nguoi thao tac."""
        own_id = receiver_id if tx_type == DEPOSIT else sender_id
        if own_id not in wallets:
            raise ServiceError("WALLET_NOT_FOUND", "The wallet does not exist.")
        if wallets[own_id]["user_id"] != user_id:
            raise ServiceError("FORBIDDEN", "This wallet does not belong to you.")
        if tx_type == TRANSFER and receiver_id not in wallets:
            raise ServiceError("WALLET_NOT_FOUND", "The wallet does not exist.")
        return own_id

    def _settle(self, tx_id):
        """PENDING -> SUCCESS (trigger cap nhat vi). Neu bi tu choi: PENDING -> FAIL va tra ve loi
        de caller commit dong FAIL truoc khi bao loi; thanh cong thi tra ve None."""
        try:
            self.tx_repo.mark_transaction_success(tx_id)
        except Exception as error:
            self.tx_repo.mark_transaction_failed(tx_id)
            return error
        return None

    def _record_audit(self, tx_type, user_id, tx_id, sender_id, receiver_id, wallets):
        if tx_type == TRANSFER:
            self.audit.record(user_id, AuditAction.TRANSFER, wallet_id=sender_id, transaction_id=tx_id)
            self.audit.record(wallets[receiver_id]["user_id"], AuditAction.TRANSFER_RECEIVED,
                              wallet_id=receiver_id, transaction_id=tx_id)
        else:
            wallet_id = receiver_id if tx_type == DEPOSIT else sender_id
            self.audit.record(user_id, _AUDIT_ACTION_OF[tx_type], wallet_id=wallet_id, transaction_id=tx_id)

    def _reraise(self, operation, error):
        """Nem lai loi qua db_transaction de no duoc doi thanh thong bao than thien
        giong moi loi khac (khoi giao dich nay rong nen rollback khong anh huong gi)."""
        with db_transaction(self.conn, operation):
            raise error

    # ---------------------------------------------------------------- lich su
    def history(self, user_id, tx_type=None, status=None, limit=DEFAULT_LIMIT):
        tx_type = parse_choice(tx_type, TX_TYPES, "Type")
        status = parse_choice(status, TX_STATUSES, "Status")
        limit = normalize_limit(limit)
        with db_transaction(self.conn, "View history"):
            return self.tx_repo.list_transactions(user_id, tx_type, status, limit)

    def transaction_detail(self, user_id, transaction_id):
        tx = self._get(transaction_id)
        if tx is None or user_id not in (tx["sender_user_id"], tx["receiver_user_id"]):
            raise ServiceError("TRANSACTION_NOT_FOUND", "The transaction does not exist.")
        return tx

    # ---------------------------------------------------------------- quan tri
    def list_all_transactions(self, tx_type=None, status=None, limit=DEFAULT_ADMIN_LIMIT):
        tx_type = parse_choice(tx_type, TX_TYPES, "Type")
        status = parse_choice(status, TX_STATUSES, "Status")
        limit = normalize_limit(limit)
        with db_transaction(self.conn, "View transactions"):
            return self.tx_repo.list_all_transactions(tx_type, status, limit)

    def get_transaction_by_id(self, transaction_id):
        tx = self._get(transaction_id)
        if tx is None:
            raise ServiceError("TRANSACTION_NOT_FOUND", "The transaction does not exist.")
        return tx

    def _get(self, transaction_id):
        tid = parse_id(transaction_id, "Transaction")
        with db_transaction(self.conn, "View transaction"):
            return self.tx_repo.get_transaction(tid)