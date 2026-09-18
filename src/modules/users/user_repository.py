# src/modules/users/user_repository.py
import pymysql

class UserRepository:
    def __init__(self, db_connection):
        self.conn = db_connection

    def register(self, user_name, password_hash, email, phone):
        cursor = self.conn.cursor()
        try:
            self.conn.begin() # Bắt đầu transaction với PyMySQL

            # 1. INSERT vào bảng Users
            insert_user_query = """
                INSERT INTO Users (User_name, Password_hash, Email, Phone, Status)
                VALUES (%s, %s, %s, %s, 'ACTIVE')
            """
            cursor.execute(insert_user_query, (user_name, password_hash, email, phone))
            user_id = cursor.lastrowid

            # 2. INSERT vào bảng Wallets
            insert_wallet_query = """
                INSERT INTO Wallets (User_id, Balance, Currency, Limit_week)
                VALUES (%s, 0.00, 'VND', 10000000.00)
            """
            cursor.execute(insert_wallet_query, (user_id,))

            self.conn.commit()
            return user_id

        except Exception as err:
            self.conn.rollback()
            raise err

        finally:
            cursor.close()
            self.conn.close() # Dòng này sẽ trả kết nối về lại cho DBUtils Pool!