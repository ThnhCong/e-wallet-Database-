from decimal import Decimal, InvalidOperation


class WalletService:

    def __init__(self, wallet_repository):
        self.wallet_repo = wallet_repository

    def create_wallet(self, user_id, currency):
        try:
            if self.wallet_repo.user_exist(user_id):
                return  self.wallet_repo.create_wallet(user_id, currency)
            return False

        except Exception as e:
            raise

    def _validate_amount(self, amount):
        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError("Amount must be a valid number.")

        if amount <= 0:
            raise ValueError("Amount must be greater than 0.")

        if amount.as_tuple().exponent < -2:
            raise ValueError("Amount can have at most 2 decimal places.")

        return amount

    def get_wallet_by_id(self, wallet_id):
        return self.wallet_repo.get_wallet_by_id(wallet_id)

    def deposit(self, wallet_id, amount):
        amount = self._validate_amount(amount)
        repo = self.wallet_repo
        conn = repo.conn

        try:
            conn.begin()

            wallet = repo.get_wallet_by_id(wallet_id)
            if wallet is None:
                raise ValueError("Wallet does not exist.")

            if wallet["status"] != "ACTIVE":
                raise ValueError("Wallet is locked. Deposit is not allowed.")

            wallet_id = wallet["wallet_id"]

            transaction_id = repo.create_transaction(
                sender_id=None,
                receiver_id=wallet_id,
                transaction_type="DEPOSIT",
                amount=amount
            )

            repo.increase_balance(wallet_id, amount)
            repo.mark_transaction_success(transaction_id)
            repo.create_audit_log(
                user_id=wallet['user_id'],
                wallet_id=wallet_id,
                transaction_id=transaction_id,
                action="DEPOSIT"
            )

            conn.commit()
            return {
                "transaction_id": transaction_id,
                "wallet_id": wallet_id,
                "amount": amount,
                "status": "SUCCESS"
            }

        except Exception:
            conn.rollback()
            raise

    def withdraw(self, wallet_id, amount):
        amount = self._validate_amount(amount)
        repo = self.wallet_repo
        conn = repo.conn

        try:
            conn.begin()

            wallet = repo.get_wallet_by_id(wallet_id)
            if wallet is None:
                raise ValueError("Wallet does not exist.")

            if wallet["status"] != "ACTIVE":
                raise ValueError("Wallet is locked. Withdrawal is not allowed.")

            if wallet["balance"] < amount:
                raise ValueError("Insufficient balance.")

            wallet_id = wallet["wallet_id"]

            transaction_id = repo.create_transaction(
                sender_id=wallet_id,
                receiver_id=None,
                transaction_type="WITHDRAW",
                amount=amount
            )

            repo.decrease_balance(wallet_id, amount)
            repo.mark_transaction_success(transaction_id)
            repo.create_audit_log(
                user_id=wallet['user_id'],
                wallet_id=wallet_id,
                transaction_id=transaction_id,
                action="WITHDRAW"
            )

            conn.commit()
            return {
                "transaction_id": transaction_id,
                "wallet_id": wallet_id,
                "amount": amount,
                "status": "SUCCESS"
            }

        except Exception:
            conn.rollback()
            raise

    def transfer(self, sender_user_id, receiver_user_id, amount):
        amount = self._validate_amount(amount)

        if not self.wallet_repo.are_the_same_currency(sender_user_id, receiver_user_id):
            raise ValueError("Sender and receiver are not the same currency")
        elif sender_user_id == receiver_user_id:
            raise ValueError("Sender and receiver cannot be the same user.")

        repo = self.wallet_repo
        conn = repo.conn

        try:
            conn.begin()

            # --- GIẢI PHÁP CHỐNG DEADLOCK: Khóa theo thứ tự ID nhỏ hơn trước ---
            first_id = min(sender_user_id, receiver_user_id)
            second_id = max(sender_user_id, receiver_user_id)

            first_wallet = repo.get_wallet_by_id(first_id)
            second_wallet = repo.get_wallet_by_id(second_id)

            sender = first_wallet if first_id == sender_user_id else second_wallet
            receiver = first_wallet if first_id == receiver_user_id else second_wallet

            if sender is None:
                raise ValueError("Sender or sender wallet does not exist.")

            if receiver is None:
                raise ValueError("Receiver or receiver wallet does not exist.")

            if sender["status"] != "ACTIVE":
                raise ValueError("Sender is locked.")

            if receiver["status"] != "ACTIVE":
                raise ValueError("Receiver is locked.")

            sender_wallet_id = sender["wallet_id"]
            receiver_wallet_id = receiver["wallet_id"]

            if sender["balance"] < amount:
                raise ValueError("Insufficient balance.")

            if sender["limit_week"] < amount:
                raise ValueError("Transfer amount exceeds weekly limit.")

            transaction_id = repo.create_transaction(
                sender_id=sender_wallet_id,
                receiver_id=receiver_wallet_id,
                transaction_type="TRANSFER",
                amount=amount
            )

            repo.decrease_balance(sender_wallet_id, amount)
            repo.increase_balance(receiver_wallet_id, amount)
            repo.decrease_weekly_limit(sender_wallet_id, amount)
            repo.mark_transaction_success(transaction_id)

            repo.create_audit_log(
                user_id=sender['user_id'],
                wallet_id=sender_wallet_id,
                transaction_id=transaction_id,
                action="DEBIT"
            )

            repo.create_audit_log(
                user_id=receiver['user_id'],
                wallet_id=receiver_wallet_id,
                transaction_id=transaction_id,
                action="CREDIT"
            )

            conn.commit()
            return {
                "transaction_id": transaction_id,
                "sender_wallet_id": sender_wallet_id,
                "receiver_wallet_id": receiver_wallet_id,
                "amount": amount,
                "status": "SUCCESS"
            }

        except Exception:
            conn.rollback()
            raise