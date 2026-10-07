# src/app.py
"""CLI e-wallet (Presentation Layer): chi nhap/xuat, goi Controller, KHONG viet SQL.

Chay (dat DB_USER, DB_PASSWORD truoc):   python src/app.py
hoac     python -m src.app

Moi thao tac lay 1 connection tu pool -> 1 thao tac = 1 giao dich DB;
xong thi tra ve pool.
"""
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # de `import src.xxx` chay duoc moi noi

from src.modules.audit_logs.audit_repository import AuditRepository                   # noqa: E402
from src.config.database.connection import get_db_connection                           # noqa: E402
from src.modules.user.user_controller import UserController                            # noqa: E402
from src.modules.user.user_repository import UserRepository                            # noqa: E402
from src.modules.user.user_service import UserService                                  # noqa: E402
from src.modules.wallet.wallet_controller import WalletController                      # noqa: E402
from src.modules.wallet.wallet_repository import WalletRepository                      # noqa: E402
from src.modules.wallet.wallet_service import WalletService                            # noqa: E402

logging.basicConfig(
    filename="ewallet.log",
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("ewallet.cli")

MAX_LOGIN_FAILS = 3
LOCKOUT_SECONDS = 60


# ---------------------------------------------------------------- hien thi
def money(v):
    return f"{v:,.2f}"


def table(rows, cols):
    """cols = [(tieu de, key hoac ham)]"""
    if not rows:
        print("(no data)")
        return

    cells = [[str(f(r) if callable(f) else r[f]) for _, f in cols] for r in rows]
    widths = [
        max(len(h), *(len(c[i]) for c in cells))
        for i, (h, _) in enumerate(cols)
    ]

    line = "  ".join(
        h.ljust(w) for (h, _), w in zip(cols, widths)
    )

    print(line)
    print("-" * len(line))

    for c in cells:
        print("  ".join(v.ljust(w) for v, w in zip(c, widths)))


def ask(prompt):
    return input(prompt).strip()


WALLET_COLS = [
    ("ID", "wallet_id"),
    ("Currency", "currency"),
    ("Balance", lambda w: money(w["balance"])),
    ("Weekly limit", lambda w: money(w["limit_week"])),
    ("Remaining", lambda w: money(w["remain_limit_week"])),
    ("Status", "status")
]


# ---------------------------------------------------------------- 1 thao tac = 1 connection
def run(action):
    """action(user_controller, wallet_controller) -> ket qua.
    Loi nghiep vu (ValueError) in ra, khong crash.
    """
    conn = get_db_connection()

    try:
        user_repo = UserRepository(conn)
        wallet_repo = WalletRepository(conn)
        audit_repo = AuditRepository(conn)

        users = UserController(
            UserService(user_repo, audit_repo, wallet_repo)
        )

        wallets = WalletController(
            WalletService(wallet_repo, audit_repo)
        )

        return action(users, wallets)

    except ValueError as e:
        # gom ca ServiceError: thong bao da than thien
        print(f"\n[ERROR] {e}")

    except RuntimeError as e:
        # vi du thieu DB_USER
        print(f"\n[ERROR] {e}")

    except Exception:
        log.exception("Unhandled error")
        print("\n[ERROR] Operation failed. See ewallet.log for details.")

    finally:
        conn.close()                            # tra connection ve pool

    return None


# ---------------------------------------------------------------- chuc nang
def do_register():
    print("--- Register ---")

    name = ask("Username: ")
    password = ask("Password (>=6 chars): ")
    email = ask("Email: ")
    phone = ask("Phone: ")

    # SUA DUY NHAT O DAY:
    # Khong dung getpass vi PyCharm console cua ban dang
    # bi dung process sau khi nhan Enter o Phone.


    currency = ask(
        "Create an initial wallet? VND/USD (Enter to skip): "
    ) or None

    user_id = run(
        lambda u, w: u.register(
            name,
            password,
            email,
            phone,
            currency
        )
    )

    if user_id:
        print(
            f"\n[OK] Registration successful! User ID: {user_id}"
        )


def do_login(state):
    now = time.time()

    if now < state["locked_until"]:
        print(
            f"\n[ERROR] Too many failed attempts. "
            f"Try again in {int(state['locked_until'] - now)} seconds."
        )
        return None

    phone = ask("Phone: ")

    # SUA DUY NHAT O DAY:
    # Khong dung getpass vi cung co the gay loi tren PyCharm console.
    password = ask("Password: ")

    user = run(
        lambda u, w: u.login(phone, password)
    )

    if user:
        state["fails"] = 0

        print(
            f"\n[OK] Login successful. "
            f"Welcome, {user['user_name']}!"
        )

        return user

    state["fails"] += 1

    if state["fails"] >= MAX_LOGIN_FAILS:
        state["fails"] = 0
        state["locked_until"] = time.time() + LOCKOUT_SECONDS

        print(
            f"[ERROR] Login is locked for {LOCKOUT_SECONDS} seconds."
        )

    return None


def do_view_user(user):
    info = run(
        lambda u, w: u.get_user_by_id(user["user_id"])
    )

    if info:
        print(
            "\n================================\n"
            "        USER INFORMATION\n"
            "================================"
        )

        print(
            f"User ID   : {info['user_id']}\n"
            f"Username  : {info['user_name']}\n"
            f"Email     : {info['email']}\n"
            f"Phone     : {info['phone']}"
        )


def do_update_profile(user):
    print("(Press Enter to keep the current value)")

    name = ask("New username: ")
    email = ask("New email: ")
    phone = ask("New phone: ")

    info = run(
        lambda u, w: u.update_profile(
            user["user_id"],
            name,
            email,
            phone
        )
    )

    if info:
        user.update(
            user_name=info["user_name"],
            email=info["email"],
            phone=info["phone"]
        )

        print("\n[OK] Profile updated.")


def do_change_password(user):
    old = ask("Current password: ")
    new = ask("New password (>=6 chars): ")

    if run(
        lambda u, w: (
            u.change_password(
                user["user_id"],
                old,
                new
            ),
            True
        )[1]
    ):
        print("\n[OK] Password changed.")


def show_wallets(user):
    rows = run(
        lambda u, w: w.list_wallets(user["user_id"])
    )

    if rows is not None:
        table(rows, WALLET_COLS)

    return rows


def do_view_wallet(user):
    show_wallets(user)

    wid = ask("Wallet ID for details: ")

    info = run(
        lambda u, w: w.get_wallet_by_id(
            user["user_id"],
            wid
        )
    )

    if info:
        print(
            "\n================================\n"
            "        WALLET INFORMATION\n"
            "================================"
        )

        print(
            f"Wallet ID    : {info['wallet_id']}\n"
            f"Owner        : {info['user_name']} (user {info['user_id']})\n"
            f"Balance      : {money(info['balance'])} {info['currency']}\n"
            f"Weekly limit : {money(info['limit_week'])} {info['currency']}\n"
            f"Remaining    : {money(info['remain_limit_week'])} {info['currency']}\n"
            f"Status       : {info['status']}\n"
            f"Created at   : {info['created_at']}"
        )


def do_create_wallet(user):
    currency = ask("Currency (VND/USD): ")

    w = run(
        lambda u, wl: wl.create_wallet(
            user["user_id"],
            currency
        )
    )

    if w:
        print(
            f"\n[OK] Wallet #{w['wallet_id']} created "
            f"({w['currency']}, weekly limit "
            f"{money(w['limit_week'])})."
        )


def do_lock(user, lock):
    show_wallets(user)

    wid = ask("Wallet ID: ")

    w = run(
        lambda u, wl: (
            wl.lock_wallet if lock else wl.unlock_wallet
        )(
            user["user_id"],
            wid
        )
    )

    if w:
        print(
            f"\n[OK] Wallet #{w['wallet_id']} "
            f"is now {w['status']}."
        )


def _print_tx(res):
    if res:
        line = (
            f"\n[OK] Transaction #{res['transaction_id']} "
            f"{res['type']} {money(res['amount'])} - SUCCESS. "
            f"New balance of wallet {res['wallet_id']}: "
            f"{money(res['balance'])}"
        )

        if res["type"] == "TRANSFER":
            line += (
                f". Remaining weekly limit: "
                f"{money(res['remain_limit_week'])}"
            )

        print(line)


def do_deposit(user):
    show_wallets(user)

    wid = ask("Wallet ID: ")
    amount = ask("Deposit amount: ")

    _print_tx(
        run(
            lambda u, w: w.deposit(
                user["user_id"],
                wid,
                amount
            )
        )
    )


def do_withdraw(user):
    show_wallets(user)

    wid = ask("Wallet ID: ")
    amount = ask("Withdrawal amount: ")

    _print_tx(
        run(
            lambda u, w: w.withdraw(
                user["user_id"],
                wid,
                amount
            )
        )
    )


def do_transfer(user):
    show_wallets(user)

    src = ask("From wallet ID (yours): ")
    dst = ask("To wallet ID: ")
    amount = ask("Transfer amount: ")

    _print_tx(
        run(
            lambda u, w: w.transfer(
                user["user_id"],
                src,
                dst,
                amount
            )
        )
    )


def do_history(user):
    tx_type = ask(
        "Filter type DEPOSIT/WITHDRAW/TRANSFER (Enter = all): "
    )

    status = ask(
        "Filter status PENDING/SUCCESS/FAIL (Enter = all): "
    )

    rows = run(
        lambda u, w: w.history(
            user["user_id"],
            tx_type,
            status
        )
    )

    if rows is None:
        return

    table(
        rows,
        [
            ("ID", "transaction_id"),
            ("Type", "type"),
            ("Amount", lambda t: money(t["amount"])),
            ("From", lambda t: t["sender_id"] or "-"),
            ("To", lambda t: t["receiver_id"] or "-"),
            ("Status", "status"),
            ("Time", "created_at")
        ]
    )

    tid = ask(
        "Transaction ID for details (Enter to skip): "
    )

    if tid:
        d = run(
            lambda u, w: w.transaction_detail(
                user["user_id"],
                tid
            )
        )

        if d:
            for k, v in d.items():
                if not k.endswith("_user_id"):
                    print(f"  {k}: {v}")


def do_activity(user):
    rows = run(
        lambda u, w: u.get_activity(
            user["user_id"]
        )
    )

    if rows is not None:
        table(
            rows,
            [
                ("Log", "audit_log_id"),
                ("Action", "action"),
                ("Wallet", lambda a: a["wallet_id"] or "-"),
                ("Transaction", lambda a: a["transaction_id"] or "-"),
                ("Time", "created_at")
            ]
        )


# ---------------------------------------------------------------- menu
GUEST_MENU = (
    "\n================================\n"
    "        E-WALLET SYSTEM\n"
    "================================\n"
    "1. Register\n"
    "2. Login\n"
    "0. Exit"
)

USER_MENU = (
    "\n=== Hello, {name} ===\n"
    " 1. View my info     2. Update info       3. Change password\n"
    " 4. My wallets       5. View wallet       6. Create wallet\n"
    " 7. Lock wallet      8. Unlock wallet\n"
    " 9. Deposit         10. Withdraw         11. Transfer\n"
    "12. Transaction history                  13. My activity log\n"
    " 0. Logout"
)


def main():
    user = None

    state = {
        "fails": 0,
        "locked_until": 0
    }

    actions = {
        "1": do_view_user,
        "2": do_update_profile,
        "3": do_change_password,
        "4": show_wallets,
        "5": do_view_wallet,
        "6": do_create_wallet,
        "7": lambda u: do_lock(u, True),
        "8": lambda u: do_lock(u, False),
        "9": do_deposit,
        "10": do_withdraw,
        "11": do_transfer,
        "12": do_history,
        "13": do_activity
    }

    while True:
        try:
            if user is None:
                print(GUEST_MENU)

                choice = ask("Choose: ")

                if choice == "1":
                    do_register()

                elif choice == "2":
                    user = do_login(state)

                elif choice == "0":
                    print("Goodbye!")
                    break

                else:
                    print("Invalid choice.")

            else:
                print(
                    USER_MENU.format(
                        name=user["user_name"]
                    )
                )

                choice = ask("Choose: ")

                if choice == "0":
                    run(
                        lambda u, w: u.logout(
                            user["user_id"]
                        )
                    )

                    print("\n[OK] Logged out.")
                    user = None

                elif choice in actions:
                    actions[choice](user)

                else:
                    print("Invalid choice.")

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
