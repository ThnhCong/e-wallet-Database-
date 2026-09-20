import pymysql

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

        except pymysql.err.IntegrityError as e:
            self.conn.rollback()

            error_code = e.args[0]
            error_message = str(e)

            if error_code == 1062:
                if "uq_users_email" in error_message:
                    raise ValueError("Error: Email has been exist!")
                if "uq_users_phone" in error_message:
                    raise ValueError("Error: Phone number has been exist")

            raise

        except Exception:
            # Nếu một bước lỗi -> rollback toàn bộ
            self.conn.rollback()
            raise

        finally:
            cursor.close()

    def login(self, phone_input, password_hash_input):
        cursor = self.conn.cursor()

        try:
            query = """
                SELECT password_hash 
                FROM users 
                WHERE phone = %s 
                LIMIT 1
            """
            cursor.execute(query, (phone_input,))
            result = cursor.fetchone()

            #User is not exist
            if result is None:
                return False

            # result is a tuple (password_hash,)
            db_password_hash = result['password_hash']

            # Compare password hash
            return password_hash_input == db_password_hash

        except Exception as e:
            self.conn.rollback()
            raise

        finally:
            cursor.close()
    def view_user_by_id(self, user_id):
        cursor = self.conn.cursor()

        try:
            query = """
                    SELECT *
                    FROM users
                    WHERE user_id = %s
                    LIMIT 1
                    """

            cursor.execute(query, (user_id,))
            user = cursor.fetchone()

            if not user: #User is not exist!
                return False

            return user

        except Exception as e:
            self.conn.rollback()
            raise

        finally:
            cursor.close()