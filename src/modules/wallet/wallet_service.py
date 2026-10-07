# src/modules/wallet/wallet_service.py
"""Luong tai chinh: khoa vi -> INSERT PENDING -> UPDATE SUCCESS -> audit -> COMMIT.
Service KHONG tu cong/tru balance hay han muc tuan: trigger trong DB lam. Loi nao cung ROLLBACK het."""
from src.common.db import db_transaction
from src.common.errors import ServiceError
from src.common.validators import (TX_STATUSES, TX_TYPES, parse_amount, parse_choice, parse_currency, parse_id)


class WalletService:

    def __init__(self, wallet_repository, audit_repository):
        self.wallet_repo = wallet_repository
        self.audit_repo = audit_repository
        self.conn = wallet_repository.conn

    # ---------------------------------------------------------------- vi
    def _own_wallet(self, user_id, wallet_id):
        wallet = self.wallet_repo.get_wallet_by_id(wallet_id)
        if wallet is None:
            raise ServiceError("WALLET_NOT_FOUND", "The wallet does not exist.")
        if wallet["user_id"] != user_id:
            raise ServiceError("FORBIDDEN", "This wallet does not belong to you.")
        return wallet

    def create_wallet(self, user_id, currency):
        currency = parse_currency(currency)
        with db_transaction(self.conn, "Create wallet"):
            wallet_id = self.wallet_repo.create_wallet(user_id, currency)
            self.audit_repo.create_audit_log(user_id, wallet_id, None, "CREATE_WALLET")
            return self.wallet_repo.get_wallet_by_id(wallet_id)

    def list_wallets(self, user_id):
        with db_transaction(self.conn, "View wallets"):
            return self.wallet_repo.list_wallets_by_user(user_id)

    def get_wallet_by_id(self, user_id, wallet_id):
        wallet_id = parse_id(wallet_id, "Wallet")
        with db_transaction(self.conn, "View wallet"):
            return self._own_wallet(user_id, wallet_id)

    def set_locked(self, user_id, wallet_id, locked):
        wallet_id = parse_id(wallet_id, "Wallet")
        status, action = ("LOCKED", "LOCK_WALLET") if locked else ("ACTIVE", "UNLOCK_WALLET")
        with db_transaction(self.conn, "Update wallet"):
            self.wallet_repo.lock_wallets(wallet_id)
            self._own_wallet(user_id, wallet_id)
            self.wallet_repo.set_wallet_status(wallet_id, status)
            self.audit_repo.create_audit_log(user_id, wallet_id, None, action)
            return self.wallet_repo.get_wallet_by_id(wallet_id)

    # ---------------------------------------------------------------- giao dich
    def _run(self, operation, tx_type, user_id, sender_id, receiver_id, amount):
        with db_transaction(self.conn, operation):
            wallets = self.wallet_repo.lock_wallets(sender_id, receiver_id)   # thu tu id tang dan

            own_id = receiver_id if tx_type == "DEPOSIT" else sender_id       # vi cua nguoi thao tac
            if own_id not in wallets:
                raise ServiceError("WALLET_NOT_FOUND", "The wallet does not exist.")
            if wallets[own_id]["user_id"] != user_id:
                raise ServiceError("FORBIDDEN", "This wallet does not belong to you.")
            if tx_type == "TRANSFER" and receiver_id not in wallets:
                raise ServiceError("WALLET_NOT_FOUND", "The wallet does not exist.")

            tx_id = self.wallet_repo.create_transaction(sender_id, receiver_id, tx_type, amount)  # PENDING
            self.wallet_repo.mark_transaction_success(tx_id)                                      # -> SUCCESS

            if tx_type == "TRANSFER":
                self.audit_repo.create_audit_log(user_id, sender_id, tx_id, "TRANSFER")
                self.audit_repo.create_audit_log(wallets[receiver_id]["user_id"], receiver_id, tx_id,
                                                 "TRANSFER_RECEIVED")
            else:
                self.audit_repo.create_audit_log(user_id, own_id, tx_id, tx_type)

            wallet = self.wallet_repo.get_wallet_by_id(own_id)
        return {"transaction_id": tx_id, "type": tx_type, "status": "SUCCESS", "amount": amount,
                "wallet_id": own_id, "balance": wallet["balance"], "remain_limit_week": wallet["remain_limit_week"]}

    def deposit(self, user_id, wallet_id, amount):
        return self._run("Deposit", "DEPOSIT", user_id, None, parse_id(wallet_id), parse_amount(amount))

    def withdraw(self, user_id, wallet_id, amount):
        return self._run("Withdrawal", "WITHDRAW", user_id, parse_id(wallet_id), None, parse_amount(amount))

    def transfer(self, user_id, sender_wallet_id, receiver_wallet_id, amount):
        sender = parse_id(sender_wallet_id, "Sender wallet")
        receiver = parse_id(receiver_wallet_id, "Receiver wallet")
        if sender == receiver:
            raise ServiceError("SAME_WALLET", "You cannot transfer to the same wallet.")
        return self._run("Transfer", "TRANSFER", user_id, sender, receiver, parse_amount(amount))

    # ---------------------------------------------------------------- lich su
    def history(self, user_id, tx_type=None, status=None, limit=20):
        tx_type = parse_choice(tx_type, TX_TYPES, "Type")
        status = parse_choice(status, TX_STATUSES, "Status")
        with db_transaction(self.conn, "View history"):
            return self.wallet_repo.list_transactions(user_id, tx_type, status, limit)

    def transaction_detail(self, user_id, transaction_id):
        tid = parse_id(transaction_id, "Transaction")
        with db_transaction(self.conn, "View transaction"):
            tx = self.wallet_repo.get_transaction(tid)
        if tx is None or user_id not in (tx["sender_user_id"], tx["receiver_user_id"]):
            raise ServiceError("TRANSACTION_NOT_FOUND", "The transaction does not exist.")
        return tx