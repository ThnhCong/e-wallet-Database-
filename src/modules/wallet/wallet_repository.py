import pymysql


class WalletRepository:

    def __init__(self, db_connection):
        self.conn = db_connection

    # =========================================================
    # GET WALLET
    # =========================================================

    def get_wallet_by_user_id_for_update(self, user_id):
        cursor = self.conn.cursor()

        try:
            query = """
                SELECT
                    w.wallet_id,
                    w.user_id,
                    w.balance,
                    w.currency,
                    w.limit_week,
                    u.user_name,
                    u.status AS user_status
                FROM wallets w
                INNER JOIN users u
                    ON w.user_id = u.user_id
                WHERE w.user_id = %s
                FOR UPDATE
            """

            cursor.execute(query, (user_id,))
            return cursor.fetchone()

        finally:
            cursor.close()

    def get_wallet_by_id(self, wallet_id):
        cursor = self.conn.cursor()

        try:
            query = """
                SELECT
                    w.wallet_id,
                    w.user_id,
                    w.balance,
                    w.currency,
                    w.limit_week,
                    u.user_name,
                    u.status AS user_status
                FROM wallets w
                INNER JOIN users u
                    ON w.user_id = u.user_id
                WHERE w.wallet_id = %s
            """

            cursor.execute(query, (wallet_id,))
            return cursor.fetchone()

        finally:
            cursor.close()

    # =========================================================
    # CREATE TRANSACTION
    # =========================================================

    def create_transaction(
        self,
        sender_id,
        receiver_id,
        transaction_type,
        amount
    ):
        cursor = self.conn.cursor()

        try:
            query = """
                INSERT INTO transactions
                (
                    sender_id,
                    receiver_id,
                    type,
                    amount,
                    status
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    'PENDING'
                )
            """

            cursor.execute(
                query,
                (
                    sender_id,
                    receiver_id,
                    transaction_type,
                    amount
                )
            )

            return cursor.lastrowid

        finally:
            cursor.close()

    # =========================================================
    # CREATE LEDGER
    # =========================================================

    def create_ledger(
        self,
        wallet_id,
        transaction_id,
        ledger_type,
        amount
    ):
        cursor = self.conn.cursor()

        try:
            query = """
                INSERT INTO ledgers
                (
                    wallet_id,
                    transaction_id,
                    type,
                    amount
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
            """

            cursor.execute(
                query,
                (
                    wallet_id,
                    transaction_id,
                    ledger_type,
                    amount
                )
            )

            return cursor.lastrowid

        finally:
            cursor.close()

    # =========================================================
    # UPDATE BALANCE
    # =========================================================

    def increase_balance(self, wallet_id, amount):

        cursor = self.conn.cursor()

        try:
            query = """
                UPDATE wallets
                SET balance = balance + %s
                WHERE wallet_id = %s
            """

            cursor.execute(
                query,
                (
                    amount,
                    wallet_id
                )
            )

        finally:
            cursor.close()

    def decrease_balance(self, wallet_id, amount):

        cursor = self.conn.cursor()

        try:
            query = """
                UPDATE wallets
                SET balance = balance - %s
                WHERE wallet_id = %s
                  AND balance >= %s
            """

            cursor.execute(
                query,
                (
                    amount,
                    wallet_id,
                    amount
                )
            )

            if cursor.rowcount != 1:
                raise ValueError("Insufficient balance.")

        finally:
            cursor.close()

    # =========================================================
    # UPDATE WEEKLY LIMIT
    # =========================================================

    def decrease_weekly_limit(self, wallet_id, amount):

        cursor = self.conn.cursor()

        try:
            query = """
                UPDATE wallets
                SET limit_week = limit_week - %s
                WHERE wallet_id = %s
                  AND limit_week >= %s
            """

            cursor.execute(
                query,
                (
                    amount,
                    wallet_id,
                    amount
                )
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    "Transfer amount exceeds weekly limit."
                )

        finally:
            cursor.close()

    # =========================================================
    # TRANSACTION SUCCESS
    # =========================================================

    def mark_transaction_success(self, transaction_id):

        cursor = self.conn.cursor()

        try:
            query = """
                UPDATE transactions
                SET status = 'SUCCESS'
                WHERE transaction_id = %s
                  AND status = 'PENDING'
            """

            cursor.execute(
                query,
                (transaction_id,)
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "Cannot update transaction status."
                )

        finally:
            cursor.close()

    # =========================================================
    # AUDIT LOG
    # =========================================================

    def create_audit_log(
        self,
        user_id,
        wallet_id,
        transaction_id,
        action
    ):

        cursor = self.conn.cursor()

        try:
            query = """
                INSERT INTO audit_logs
                (
                    transaction_id,
                    wallet_id,
                    user_id,
                    action
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
            """

            cursor.execute(
                query,
                (
                    transaction_id,
                    wallet_id,
                    user_id,
                    action
                )
            )

            return cursor.lastrowid

        finally:
            cursor.close()

    # =========================================================
    # GET WALLET AFTER TRANSACTION
    # =========================================================

    def get_wallet(self, user_id):

        cursor = self.conn.cursor()

        try:
            query = """
                SELECT
                    w.wallet_id,
                    w.user_id,
                    w.balance,
                    w.currency,
                    w.limit_week,
                    u.user_name,
                    u.status AS user_status
                FROM wallets w
                INNER JOIN users u
                    ON w.user_id = u.user_id
                WHERE w.user_id = %s
            """

            cursor.execute(query, (user_id,))
            return cursor.fetchone()

        finally:
            cursor.close()