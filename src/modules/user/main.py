from src.config.database.connection import get_db_connection

from src.modules.user.user_repository import UserRepository
from src.modules.user.user_service import UserService
from src.modules.user.user_controller import UserController

from src.modules.wallet.wallet_repository import WalletRepository
from src.modules.wallet.wallet_service import WalletService
from src.modules.wallet.wallet_controller import WalletController


def main():
    print("================================")
    print("        E-WALLET SYSTEM")
    print("================================")

    while True:
        print("\n1. Register")
        print("2. Deposit")
        print("3. Withdraw")
        print("4. Transfer")
        print("5. View Wallet")
        print("0. Exit")

        choice = input("Choose: ").strip()

        if choice == "0":
            print("Goodbye!")
            break

        if choice not in ["1", "2", "3", "4", "5"]:
            print("Invalid choice.")
            continue

        # Mỗi yêu cầu thao tác sẽ lấy 1 connection mới từ pool
        db_conn = get_db_connection()

        try:
            user_repo = UserRepository(db_conn)
            user_service = UserService(user_repo)
            user_controller = UserController(user_service)

            wallet_repo = WalletRepository(db_conn)
            wallet_service = WalletService(wallet_repo)
            wallet_controller = WalletController(wallet_service)

            if choice == "1":
                user_name = input("Enter username: ").strip()
                password = input("Enter password: ").strip()
                email = input("Enter email: ").strip()
                phone = input("Enter phone: ").strip()

                result = user_controller.register(user_name, password, email, phone)
                print("\nRegistration successful!")
                print(f"User ID: {result}")

            elif choice == "2":
                user_id = int(input("Enter user ID: "))
                amount = input("Enter deposit amount: ")

                result = wallet_controller.deposit(user_id, amount)
                print("\nDeposit successful!")
                print(result)

            elif choice == "3":
                user_id = int(input("Enter user ID: "))
                amount = input("Enter withdrawal amount: ")

                result = wallet_controller.withdraw(user_id, amount)
                print("\nWithdrawal successful!")
                print(result)

            elif choice == "4":
                sender_id = int(input("Enter sender user ID: "))
                receiver_id = int(input("Enter receiver user ID: "))
                amount = input("Enter transfer amount: ")

                result = wallet_controller.transfer(sender_id, receiver_id, amount)
                print("\nTransfer successful!")
                print(result)

            elif choice == "5":
                wallet_id = int(input("Enter wallet ID: "))
                wallet_info = wallet_controller.get_wallet_by_id(wallet_id)

                if wallet_info:
                    print("\n================================")
                    print("        WALLET INFORMATION")
                    print("================================")
                    print(f"Wallet ID   : {wallet_info.get('wallet_id')}")
                    print(f"User ID     : {wallet_info.get('user_id')}")
                    print(f"Owner Name  : {wallet_info.get('user_name')}")
                    print(f"Balance     : {wallet_info.get('balance')} {wallet_info.get('currency')}")
                    print(f"Weekly Limit: {wallet_info.get('limit_week')} {wallet_info.get('currency')}")
                    print(f"User Status : {wallet_info.get('user_status')}")
                    print("================================")
                else:
                    print("\nWallet not found!")

        except Exception as e:
            print("\nOperation failed!")
            print(f"Reason: {e}")

        finally:
            # Đảm bảo connection luôn được trả về pool sau mỗi lệnh
            db_conn.close()


if __name__ == "__main__":
    main()