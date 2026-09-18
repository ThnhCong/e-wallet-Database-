# main.py
from src.config.database.connection import get_db_connection
from src.modules.users.user_repository import UserRepository
from src.modules.users.user_service import UserService

def main():
    # 1. Khởi tạo kết nối DB
    try:
        db_conn = get_db_connection()
        print(" Connected to Database successfully!")
    except Exception as e:
        print(f" Connect Database failed: {e}")
        return

    # 2. Khởi tạo Repository và Service
    user_repo = UserRepository(db_conn)
    user_service = UserService(user_repo)

    # 3. Dữ liệu đăng ký thử nghiệm
    test_user = {
        "user_name": "Nguyen Van A",
        "plain_password": "MySecretPassword123",
        "email": "nguyenvana@example.com",
        "phone": "0901234567"
    }

    # 4. Gọi hàm đăng ký
    try:
        new_user_id = user_service.register_user(
            user_name=test_user["user_name"],
            plain_password=test_user["plain_password"],
            email=test_user["email"],
            phone=test_user["phone"]
        )
        print(f" Register success! Created User ID: {new_user_id}")

    except Exception as err:
        print(f" Register failed: {err}")

    finally:
        # Đóng kết nối DB khi hoàn thành
        db_conn.close()

if __name__ == "__main__":
    main()