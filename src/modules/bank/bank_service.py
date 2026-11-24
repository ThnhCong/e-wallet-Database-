# src/modules/bank/bank_service.py
"""Partner banks and wallet-bank links (simulated: a link is SUCCESS at once, no real bank is called)."""
from src.common.db import db_transaction
from src.common.errors import ServiceError
from src.common.validators import parse_id, require_text
from src.modules.audit_logs.audit_actions import AuditAction


class BankService:
    def __init__(self, bank_repository, wallet_repository, audit_service):
        self.bank_repo = bank_repository
        self.wallet_repo = wallet_repository
        self.audit = audit_service
        self.conn = bank_repository.conn

    def list_banks(self):
        with db_transaction(self.conn, "View banks"):
            return self.bank_repo.list_banks()

    def list_my_links(self, user_id):
        with db_transaction(self.conn, "View bank accounts"):
            return self.bank_repo.list_links_by_user(user_id)

    def link_wallet(self, user_id, wallet_id, bank_id, account_number):
        """Link one of MY wallets to a partner bank. The BEFORE INSERT trigger checks that the wallet
        is ACTIVE, the bank exists and the pair is not linked yet; the audit log is in the same transaction."""
        wallet_id = parse_id(wallet_id, "Wallet")
        bank_id = parse_id(bank_id, "Bank")
        account_number=require_text(account_number, "Bank account number", 34)
        if not account_number.isdigit() or not 6<=len(account_number)<=34: raise ServiceError("ACCOUNT_NUMBER_INVALID", "Bank account number must contain 6-34 digits.")
        with db_transaction(self.conn, "Link bank"):
            self.wallet_repo.lock_wallets(wallet_id)
            wallet = self.wallet_repo.get_wallet_by_id(wallet_id)
            if wallet is None:
                raise ServiceError("WALLET_NOT_FOUND", "The wallet does not exist.")
            if wallet["user_id"] != user_id:
                raise ServiceError("FORBIDDEN", "This wallet does not belong to you.")
            link = self.bank_repo.link(wallet_id, bank_id, account_number)
            self.audit.record(user_id, AuditAction.LINK_BANK, wallet_id=wallet_id)
            bank = self.bank_repo.get_bank(bank_id)
            return {"bank_account_id": link["bank_account_id"], "account_number": link.get("account_number"), "wallet_id": wallet_id, "bank_id": bank_id, "bank_name": bank["name"], "status": "SUCCESS"}

    def unlink_wallet(self, user_id, bank_account_id):
        bank_account_id=parse_id(bank_account_id, "Bank account")
        with db_transaction(self.conn, "Unlink bank"):
            unlinked=self.bank_repo.unlink(user_id, bank_account_id)
            if not unlinked: raise ServiceError("BANK_LINK_NOT_FOUND", "The active bank link was not found.")
            self.audit.record(user_id, AuditAction.UNLINK_BANK, wallet_id=unlinked["wallet_id"])
            return {"bank_account_id": bank_account_id, "status": "CANCELLED"}
