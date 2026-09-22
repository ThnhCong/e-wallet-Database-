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
        print("2. Login")
        print("3. Deposit")
        print("4. Withdraw")
        print("5. Transfer")
        print("6. View Wallet")
        print("7. View User")
        print("8. Register wallet")
        print("0. Exit")

        choice = input("Choose: ").strip()

        if choice == "0":
            print("Goodbye!")
            break

        if choice not in ["1", "2", "3", "4", "5", "6", "7", "8"]:
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
                try:

                    wrong_time = 0
                    while wrong_time < 3:

                        phone_input = input("Enter your phone").strip()
                        password_input = input("Enter your password").strip()

                        if user_controller.login(phone_input, password_input):
                            break
                        else:
                            wrong_time += 1

                    if wrong_time == 3:
                        print("Waiting 1 minute to login again!")

                except ValueError as e:
                    print(f"\n{e}")

            elif choice == "3":
                wallet_id = int(input("Enter wallet ID: "))
                amount = input("Enter deposit amount: ")

                result = wallet_controller.deposit(wallet_id, amount)
                print("\nDeposit successful!")
                print(result)

            elif choice == "4":
                wallet_id = int(input("Enter wallet ID: "))
                amount = input("Enter withdrawal amount: ")

                result = wallet_controller.withdraw(wallet_id, amount)
                print("\nWithdrawal successful!")
                print(result)

            elif choice == "5":
                sender_id = int(input("Enter sender user ID: "))
                receiver_id = int(input("Enter receiver user ID: "))
                amount = input("Enter transfer amount: ")

                result = wallet_controller.transfer(sender_id, receiver_id, amount)
                print("\nTransfer successful!")
                print(result)

            elif choice == "6":
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
                    print(f"Status : {wallet_info.get('status')}")
                    print(f"Create at: {wallet_info.get('create_at')}")
                    print("================================")
                else:
                    print("\nWallet not found!")

            elif choice == "7":
                user_id = int(input("Enter user ID: "))
                user_info = user_controller.get_user_by_id(user_id)

                if user_info:
                    print("\n================================")
                    print("        USER INFORMATION        ")
                    print("================================")
                    print(f"User ID   : {user_info.get('user_id')}")
                    print(f"Username  : {user_info.get('user_name')}")
                    print(f"Email     : {user_info.get('email')}")
                    print(f"Phone     : {user_info.get('phone')}")
                    print("================================")
                else:
                    print("\nUser not found!")

            elif choice == "8":
                user_id_for_wallet = int(input("Enter user_id: "))
                currency = input("Enter currency: ").strip()
                wallet_controller.create_wallet(user_id_for_wallet, currency)
                print("\nCreate wallet successful!")

        except ValueError as e:
            print(f"\n{e}")

        except Exception as e:
            print("\nOperation failed!")
            print(f"Reason: {e}")

        finally:
            # Đảm bảo connection luôn được trả về pool sau mỗi lệnh
            db_conn.close()

if __name__ == "__main__":
    main()