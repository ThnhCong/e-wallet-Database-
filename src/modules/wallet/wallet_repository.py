import pymysql


class WalletRepository:

    def __init__(self, db_connection):
        self.conn = db_connection

    def user_exist(self, user_id):
        cursor = self.conn.cursor()

        try:
            query = """
                    SELECT 1 
                    FROM users
                    where user_id = %s
                    LIMIT 1
                    """

            cursor.execute(query, (user_id,))
            return cursor.fetchone() is not None

        except Exception as e:
            self.conn.rollback()
            raise

        finally:
            cursor.close()

    #DELETE     get_wallet_by_user_id_for_update(self, user_id)

    def create_wallet(self, user_id, currency):
        cursor = self.conn.cursor()

        try:
            insert_wallet_query = """
                    INSERT INTO wallets 
                    (user_id, balance, currency, limit_week, status)
                    VALUE (%s, 0.00, %s, 10000000, 'ACTIVE')
                    """

            cursor.execute(insert_wallet_query, (user_id, currency))
            wallet_id = cursor.lastrowid

            insert_audit_query = """
                                INSERT INTO audit_logs
                                (user_id, wallet_id, transaction_id, action)
                                VALUES (%s, %s, NULL, 'CREATE_WALLET')
                                """

            cursor.execute(insert_audit_query, (user_id, wallet_id))
            new_wallet = cursor.fetchone()

            self.conn.commit()
            return wallet_id

        except Exception as e:
            self.conn.rollback()
            raise

        finally:
            self.conn.close()

    # =========================================================
    # GET WALLET
    # =========================================================

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
                    w.status,
                    u.user_name                    
                FROM wallets w
                INNER JOIN users u
                    ON w.user_id = u.user_id
                WHERE w.wallet_id = %s
            """

            cursor.execute(query, (wallet_id,))
            return cursor.fetchone()

        finally:
            cursor.close()

    #==========================================================
    # CHECK WHETHER 2 WALLETS ARE THE SAME CURRENCY
    # ==========================================================

    def are_the_same_currency(self, sender_id, receiver_id):
        cursor = self.conn.cursor()

        try:
            find_currency_sender = """
                                    SELECT *
                                    FROM wallets
                                    WHERE wallet_id = %s
                                    LIMIT 1
                                    """
            find_currency_receiver = """
                                    SELECT *
                                    FROM wallets
                                    WHERE wallet_id = %s
                                    LIMIT 1
                                    """

            # Find currency of sender
            cursor.execute(find_currency_sender, (sender_id,))
            sender = cursor.fetchone()

            # Find currency of receiver
            cursor.execute(find_currency_receiver, (receiver_id,))
            receiver = cursor.fetchone()

            if sender['currency'] == receiver['currency']:
                return True
            else:
                return False

        except Exception as e:
            self.conn.rollback()
            raise

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
                    w.status,
                    u.user_name
                FROM wallets w
                INNER JOIN users u
                    ON w.user_id = u.user_id
                WHERE w.user_id = %s
            """

            cursor.execute(query, (user_id,))
            return cursor.fetchone()

        finally:
            cursor.close()