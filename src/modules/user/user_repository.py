class UserRepository:

    def __init__(self, db_connection):
        self.conn = db_connection

    def register(self, user_name, password_hash, email, phone):
        cursor = self.conn.cursor()

        try:
            # 1. INSERT users
            insert_user_query = """
                INSERT INTO users (user_name, password_hash, email, phone, status)
                VALUES (%s, %s, %s, %s, 'ACTIVE')
            """

            cursor.execute(
                insert_user_query,
                (user_name, password_hash, email, phone)
            )

            user_id = cursor.lastrowid

            # 2. INSERT wallets
            insert_wallet_query = """
                INSERT INTO wallets (user_id, balance, currency, limit_week)
                VALUES (%s, 0.00, 'VND', 10000000.00)
            """

            cursor.execute(
                insert_wallet_query,
                (user_id,)
            )

            wallet_id = cursor.lastrowid

            # 3. INSERT audit_logs
            insert_audit_query = """
                INSERT INTO audit_logs
                (transaction_id, wallet_id, user_id, action)
                VALUES (NULL, %s, %s, 'REGISTER')
            """

            cursor.execute(
                insert_audit_query,
                (wallet_id, user_id)
            )

            # Commit cả 3 INSERT
            self.conn.commit()

            return user_id

        except Exception:
            # Nếu một bước lỗi -> rollback toàn bộ
            self.conn.rollback()
            raise

        finally:
            cursor.close()
