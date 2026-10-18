# src/app.py
"""CLI e-wallet (Presentation Layer): chi nhap/xuat, goi Controller, KHONG viet SQL.

Chay (dat DB_USER, DB_PASSWORD truoc):   python src/app.py
hoac     python -m src.app

Che do quan tri (bao cao muc 1.2.H): dat bien moi truong EWALLET_ADMIN_KEY roi chon "Admin" o menu dau.

Moi thao tac lay 1 connection tu pool -> 1 thao tac = 1 giao dich DB;
xong thi tra ve pool.
"""
import hmac
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # de `import src.xxx` chay duoc moi noi

from src.config.database.connection import get_db_connection   # noqa: E402
from src.container import build_controllers                    # noqa: E402

logging.basicConfig(
    filename="ewallet.log",
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("ewallet.cli")

MAX_LOGIN_FAILS = 3
LOCKOUT_SECONDS = 60
ADMIN_KEY_ENV = "EWALLET_ADMIN_KEY"


# ================================================================ hien thi
def money(v):
    return f"{v:,.2f}"


def table(rows, cols):
    """cols = [(tieu de, key hoac ham)]"""
    if not rows:
        print("(no data)")
        return

    cells = [[str(f(r) if callable(f) else r[f]) for _, f in cols] for r in rows]
    widths = [max(len(h), *(len(c[i]) for c in cells)) for i, (h, _) in enumerate(cols)]

    line = "  ".join(h.ljust(w) for (h, _), w in zip(cols, widths))
    print(line)
    print("-" * len(line))
    for c in cells:
        print("  ".join(v.ljust(w) for v, w in zip(c, widths)))


def print_record(record, hidden_suffix=None):
    """In dict dang 'key: value'; bo qua key ket thuc bang hidden_suffix (neu co)."""
    for key, value in record.items():
        if not (hidden_suffix and key.endswith(hidden_suffix)):
            print(f"  {key}: {value}")


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

ADMIN_WALLET_COLS = [WALLET_COLS[0], ("Owner", lambda w: f"{w['user_name']} (#{w['user_id']})")] + WALLET_COLS[1:]

TRANSACTION_COLS = [
    ("ID", "transaction_id"),
    ("Type", "type"),
    ("Amount", lambda t: money(t["amount"])),
    ("From", lambda t: t["sender_id"] or "-"),
    ("To", lambda t: t["receiver_id"] or "-"),
    ("Status", "status"),
    ("Time", "created_at")
]

AUDIT_COLS = [
    ("Log", "audit_log_id"),
    ("Action", "action"),
    ("Wallet", lambda a: a["wallet_id"] or "-"),
    ("Transaction", lambda a: a["transaction_id"] or "-"),
    ("Time", "created_at")
]


# ================================================================ 1 thao tac = 1 connection
def run(action):
    """action(controllers) -> ket qua. Controllers co: .users .wallets .transactions .audit
    Loi nghiep vu (ValueError) in ra, khong crash. Loi -> tra ve None.
    """
    conn = get_db_connection()

    try:
        return action(build_controllers(conn))

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


def run_void(action):
    """Nhu run() cho thao tac khong tra ve gi. Tra ve True neu thanh cong, False neu loi."""
    def wrapper(controllers):
        action(controllers)
        return True

    return bool(run(wrapper))


# ================================================================ nguoi dung: tai khoan
def do_register():
    print("--- Register ---")

    # Dung input() thay vi getpass vi console cua PyCharm bi treo khi dung getpass.
    name = ask("Username: ")
    password = ask("Password (>=6 chars): ")
    email = ask("Email: ")
    phone = ask("Phone: ")
    currency = ask("Create an initial wallet? VND/USD (Enter to skip): ") or None

    user_id = run(lambda c: c.users.register(name, password, email, phone, currency))
    if user_id:
        print(f"\n[OK] Registration successful! User ID: {user_id}")


def do_login(state):
    now = time.time()

    if now < state["locked_until"]:
        print(f"\n[ERROR] Too many failed attempts. Try again in {int(state['locked_until'] - now)} seconds.")
        return None

    phone = ask("Phone: ")
    password = ask("Password: ")

    user = run(lambda c: c.users.login(phone, password))

    if user:
        state["fails"] = 0
        print(f"\n[OK] Login successful. Welcome, {user['user_name']}!")
        return user

    state["fails"] += 1
    if state["fails"] >= MAX_LOGIN_FAILS:
        state["fails"] = 0
        state["locked_until"] = time.time() + LOCKOUT_SECONDS
        print(f"[ERROR] Login is locked for {LOCKOUT_SECONDS} seconds.")

    return None


def do_view_user(user):
    info = run(lambda c: c.users.get_user_by_id(user["user_id"]))
    if info:
        print("\n================================\n"
              "        USER INFORMATION\n"
              "================================")
        print(f"User ID   : {info['user_id']}\n"
              f"Username  : {info['user_name']}\n"
              f"Email     : {info['email']}\n"
              f"Phone     : {info['phone']}")


def do_update_profile(user):
    print("(Press Enter to keep the current value)")

    name = ask("New username: ")
    email = ask("New email: ")
    phone = ask("New phone: ")

    info = run(lambda c: c.users.update_profile(user["user_id"], name, email, phone))
    if info:
        user.update(user_name=info["user_name"], email=info["email"], phone=info["phone"])
        print("\n[OK] Profile updated.")


def do_change_password(user):
    old = ask("Current password: ")
    new = ask("New password (>=6 chars): ")

    if run_void(lambda c: c.users.change_password(user["user_id"], old, new)):
        print("\n[OK] Password changed.")


# ================================================================ nguoi dung: vi
def show_wallets(user):
    rows = run(lambda c: c.wallets.list_wallets(user["user_id"]))
    if rows is not None:
        table(rows, WALLET_COLS)
    return rows


def do_view_wallet(user):
    show_wallets(user)
    wid = ask("Wallet ID for details: ")

    info = run(lambda c: c.wallets.get_wallet_by_id(user["user_id"], wid))
    if info:
        print("\n================================\n"
              "        WALLET INFORMATION\n"
              "================================")
        print(f"Wallet ID    : {info['wallet_id']}\n"
              f"Owner        : {info['user_name']} (user {info['user_id']})\n"
              f"Balance      : {money(info['balance'])} {info['currency']}\n"
              f"Weekly limit : {money(info['limit_week'])} {info['currency']}\n"
              f"Remaining    : {money(info['remain_limit_week'])} {info['currency']}\n"
              f"Status       : {info['status']}\n"
              f"Created at   : {info['created_at']}")


def do_create_wallet(user):
    currency = ask("Currency (VND/USD): ")

    wallet = run(lambda c: c.wallets.create_wallet(user["user_id"], currency))
    if wallet:
        print(f"\n[OK] Wallet #{wallet['wallet_id']} created "
              f"({wallet['currency']}, weekly limit {money(wallet['limit_week'])}).")


def do_lock(user, lock):
    show_wallets(user)
    wid = ask("Wallet ID: ")

    wallet = run(lambda c: (c.wallets.lock_wallet if lock else c.wallets.unlock_wallet)(user["user_id"], wid))
    if wallet:
        print(f"\n[OK] Wallet #{wallet['wallet_id']} is now {wallet['status']}.")


# ================================================================ nguoi dung: giao dich
def _print_tx(res):
    if res:
        line = (f"\n[OK] Transaction #{res['transaction_id']} "
                f"{res['type']} {money(res['amount'])} - SUCCESS. "
                f"New balance of wallet {res['wallet_id']}: {money(res['balance'])}")
        if res["type"] == "TRANSFER":
            line += f". Remaining weekly limit: {money(res['remain_limit_week'])}"
        print(line)


def do_deposit(user):
    show_wallets(user)
    wid = ask("Wallet ID: ")
    amount = ask("Deposit amount: ")
    _print_tx(run(lambda c: c.transactions.deposit(user["user_id"], wid, amount)))


def do_withdraw(user):
    show_wallets(user)
    wid = ask("Wallet ID: ")
    amount = ask("Withdrawal amount: ")
    _print_tx(run(lambda c: c.transactions.withdraw(user["user_id"], wid, amount)))


def do_transfer(user):
    show_wallets(user)
    src = ask("From wallet ID (yours): ")
    dst = ask("To wallet ID: ")
    amount = ask("Transfer amount: ")
    _print_tx(run(lambda c: c.transactions.transfer(user["user_id"], src, dst, amount)))


def do_history(user):
    tx_type = ask("Filter type DEPOSIT/WITHDRAW/TRANSFER (Enter = all): ")
    status = ask("Filter status PENDING/SUCCESS/FAIL (Enter = all): ")

    rows = run(lambda c: c.transactions.history(user["user_id"], tx_type, status))
    if rows is None:
        return
    table(rows, TRANSACTION_COLS)

    tid = ask("Transaction ID for details (Enter to skip): ")
    if tid:
        detail = run(lambda c: c.transactions.transaction_detail(user["user_id"], tid))
        if detail:
            print_record(detail, hidden_suffix="_user_id")


def do_activity(user):
    action = ask("Filter action (Enter = all): ")
    rows = run(lambda c: c.audit.get_activity(user["user_id"], action))
    if rows is not None:
        table(rows, AUDIT_COLS)


# ================================================================ quan tri
def admin_authenticated():
    """Schema chua co cot vai tro (role), nen quan tri duoc bao ve bang khoa trong bien moi truong."""
    expected = os.environ.get(ADMIN_KEY_ENV)
    if not expected:
        print(f"\n[ERROR] Admin mode is disabled. Set the {ADMIN_KEY_ENV} environment variable to enable it.")
        return False
    if hmac.compare_digest(ask("Admin key: ").encode(), expected.encode()):
        return True
    print("\n[ERROR] Wrong admin key.")
    return False


def admin_users():
    rows = run(lambda c: c.users.list_users())
    if rows is not None:
        table(rows, [("ID", "user_id"), ("Username", "user_name"), ("Email", "email"), ("Phone", "phone")])


def admin_wallets():
    user_id = ask("Filter by user ID (Enter = all): ")
    rows = run(lambda c: c.wallets.list_all_wallets(user_id))
    if rows is not None:
        table(rows, ADMIN_WALLET_COLS)


def admin_transactions():
    tx_type = ask("Filter type DEPOSIT/WITHDRAW/TRANSFER (Enter = all): ")
    status = ask("Filter status PENDING/SUCCESS/FAIL (Enter = all): ")
    rows = run(lambda c: c.transactions.list_all_transactions(tx_type, status))
    if rows is not None:
        table(rows, TRANSACTION_COLS)


def admin_transaction_detail():
    tid = ask("Transaction ID: ")
    detail = run(lambda c: c.transactions.get_transaction_by_id(tid))
    if detail:
        print_record(detail)


def admin_audit_logs():
    user_id = ask("Filter by user ID (Enter = all): ")
    action = ask("Filter action (Enter = all): ")
    rows = run(lambda c: c.audit.list_logs(user_id, action))
    if rows is not None:
        table(rows, [("User", "user_id")] + AUDIT_COLS)


ADMIN_MENU = (
    "\n=== ADMIN ===\n"
    "1. Users              2. Wallets\n"
    "3. Transactions       4. Transaction detail\n"
    "5. Audit logs\n"
    "0. Back"
)

ADMIN_ACTIONS = {
    "1": admin_users,
    "2": admin_wallets,
    "3": admin_transactions,
    "4": admin_transaction_detail,
    "5": admin_audit_logs
}


def admin_loop():
    if not admin_authenticated():
        return

    while True:
        print(ADMIN_MENU)
        choice = ask("Choose: ")

        if choice == "0":
            return
        if choice in ADMIN_ACTIONS:
            ADMIN_ACTIONS[choice]()
        else:
            print("Invalid choice.")


# ================================================================ menu
GUEST_MENU = (
    "\n================================\n"
    "        E-WALLET SYSTEM\n"
    "================================\n"
    "1. Register\n"
    "2. Login\n"
    "3. Admin\n"
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

USER_ACTIONS = {
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


def main():
    user = None
    state = {"fails": 0, "locked_until": 0}

    while True:
        try:
            if user is None:
                print(GUEST_MENU)
                choice = ask("Choose: ")

                if choice == "1":
                    do_register()
                elif choice == "2":
                    user = do_login(state)
                elif choice == "3":
                    admin_loop()
                elif choice == "0":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice.")

            else:
                print(USER_MENU.format(name=user["user_name"]))
                choice = ask("Choose: ")

                if choice == "0":
                    run(lambda c: c.users.logout(user["user_id"]))
                    print("\n[OK] Logged out.")
                    user = None
                elif choice in USER_ACTIONS:
                    USER_ACTIONS[choice](user)
                else:
                    print("Invalid choice.")

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()