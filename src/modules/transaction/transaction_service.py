"""
transaction_service.py - Application Layer cho nap / rut / chuyen tien (PyMySQL).

Nguyen tac (khop bao cao muc 2.2):
  * Service KHONG BAO GIO UPDATE wallets.balance / remain_limit_week. Chi:
        lock vi -> INSERT transaction (PENDING) -> UPDATE status = SUCCESS -> INSERT audit_logs -> COMMIT
    Trigger trong DB kiem tra luat va cap nhat so du.
  * Bat ky loi nao -> ROLLBACK -> doi thanh ServiceError (thong bao than thien, theo Table 3).

Dung voi connection pool (autocommit TAT):
    from dbutils.pooled_db import PooledDB
    pool = PooledDB(pymysql, 10, host=..., user=..., password=..., database="ewallet", autocommit=False)
    result = transfer(pool.connection, actor_user_id=1, sender_id=3, receiver_id="7", amount="250000")
`get_connection` la ham tra ve 1 connection moi (vd. pool.connection); service tu close() khi xong.
"""
import logging
from decimal import Decimal, InvalidOperation

from pymysql.err import MySQLError

log = logging.getLogger(__name__)

MAX_AMOUNT = Decimal("9999999999999.99")  # DECIMAL(15,2)
CURRENCIES = ("VND", "USD")


class ServiceError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


# ------------------------------------------------------------------ input handling
def parse_amount(value):
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ServiceError("AMOUNT_INVALID", "The amount must be a number.")
    if not amount.is_finite() or amount <= 0:
        raise ServiceError("AMOUNT_INVALID", "The amount must be greater than 0.")
    if amount > MAX_AMOUNT:
        raise ServiceError("AMOUNT_INVALID", "The amount is too large.")
    if amount != amount.quantize(Decimal("0.01")):
        raise ServiceError("AMOUNT_INVALID", "The amount can have at most 2 decimal places.")
    return amount


def parse_wallet_id(value, label="Wallet"):
    try:
        wid = int(str(value).strip())
    except (TypeError, ValueError):
        raise ServiceError("WALLET_INVALID", f"{label} ID must be a positive integer.")
    if wid <= 0:
        raise ServiceError("WALLET_INVALID", f"{label} ID must be a positive integer.")
    return wid


# ------------------------------------------------------------------ DB error -> user message (Table 3)
_RULES = [  # (doan thong bao trigger viet thuong, code, thong bao hien thi)
    ("amount must be greater than 0", "AMOUNT_INVALID", "The amount must be greater than 0."),
    ("wallet does not exist", "WALLET_NOT_FOUND", "The wallet does not exist."),
    ("wallet is locked", "WALLET_LOCKED", "The wallet is locked."),
    ("insufficient balance", "INSUFFICIENT_BALANCE", "{op} failed: Insufficient balance."),
    ("weekly transfer limit exceeded", "LIMIT_EXCEEDED", "{op} failed: The weekly transfer limit has been exceeded."),
    ("same currency", "CURRENCY_MISMATCH", "The two wallets must use the same currency."),
    ("cannot be the same wallet", "SAME_WALLET", "You cannot transfer to the same wallet."),
    ("unsupported currency", "CURRENCY_UNSUPPORTED", "Only VND and USD wallets are supported."),
    ("balance can only be changed", "INTERNAL", "Internal error: the balance cannot be edited directly."),
]


def translate_db_error(exc, operation):
    errno = exc.args[0] if exc.args else None
    text = str(exc.args[1]) if len(exc.args) > 1 else str(exc)
    low = text.lower()
    for fragment, code, msg in _RULES:
        if fragment in low:
            return ServiceError(code, msg.format(op=operation))
    if errno == 1452:   # FK: khong co vi
        return ServiceError("WALLET_NOT_FOUND", "The wallet does not exist.")
    if errno == 1062:   # UNIQUE
        return ServiceError("DUPLICATE", "Email or phone number is already registered.")
    if errno == 3819:   # CHECK
        return ServiceError("CONSTRAINT", "The data violates a database rule.")
    if errno in (1213, 1205):  # deadlock / lock wait timeout
        return ServiceError("BUSY", "The system is busy, please try again.")
    log.exception("Unexpected database error: %r", exc)
    return ServiceError("DB_ERROR", "A system error occurred. Please try again later.")


# ------------------------------------------------------------------ repository (noi DUY NHAT co SQL)
def _lock_wallets(cur, *ids):
    """Khoa vi theo thu tu wallet_id TANG DAN ngay dau giao dich -> khong deadlock giua 2 chuyen khoan nguoc chieu.
    Tra ve {wallet_id: (user_id, status, currency)}; vi khong ton tai thi khong co trong dict."""
    ids = sorted({i for i in ids if i is not None})
    ph = ",".join(["%s"] * len(ids))
    cur.execute(f"SELECT wallet_id, user_id, status, currency FROM wallets "
                f"WHERE wallet_id IN ({ph}) ORDER BY wallet_id FOR UPDATE", ids)
    return {r[0]: r[1:] for r in cur.fetchall()}


def _insert_transaction(cur, tx_type, sender_id, receiver_id, amount):
    # status & created_at lay DEFAULT (PENDING / now); trigger BEFORE INSERT kiem tra luat
    cur.execute("INSERT INTO transactions (sender_id, receiver_id, type, amount) VALUES (%s,%s,%s,%s)",
                (sender_id, receiver_id, tx_type, amount))
    return cur.lastrowid


def _set_status(cur, tx_id, status):
    # trigger AFTER UPDATE cap nhat so du + remain_limit_week khi PENDING -> SUCCESS
    cur.execute("UPDATE transactions SET status=%s WHERE transaction_id=%s", (status, tx_id))


def _insert_audit(cur, user_id, wallet_id, tx_id, action):
    cur.execute("INSERT INTO audit_logs (user_id, wallet_id, transaction_id, action) VALUES (%s,%s,%s,%s)",
                (user_id, wallet_id, tx_id, action))


def _balance(cur, wallet_id):
    cur.execute("SELECT balance, remain_limit_week FROM wallets WHERE wallet_id=%s", (wallet_id,))
    return cur.fetchone()


# ------------------------------------------------------------------ service
def _financial(get_connection, operation, tx_type, actor_user_id, sender_id, receiver_id, amount):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            wallets = _lock_wallets(cur, sender_id, receiver_id)

            # --- phan quyen: chi dung vi cua chinh minh (sender, hoac vi nhan cua DEPOSIT)
            own_id = sender_id if tx_type != "DEPOSIT" else receiver_id
            if own_id not in wallets:
                raise ServiceError("WALLET_NOT_FOUND", "The wallet does not exist.")
            if wallets[own_id][0] != actor_user_id:
                raise ServiceError("FORBIDDEN", "This wallet does not belong to you.")
            # vi nhan cua TRANSFER khong ton tai: bao ngay (trigger cung se chan nhu lop bao ve thu 2)
            if tx_type == "TRANSFER" and receiver_id not in wallets:
                raise ServiceError("WALLET_NOT_FOUND", "The wallet does not exist.")

            tx_id = _insert_transaction(cur, tx_type, sender_id, receiver_id, amount)   # PENDING
            _set_status(cur, tx_id, "SUCCESS")                                           # trigger cap nhat vi

            if tx_type == "TRANSFER":
                _insert_audit(cur, actor_user_id, sender_id, tx_id, "TRANSFER")
                _insert_audit(cur, wallets[receiver_id][0], receiver_id, tx_id, "TRANSFER_RECEIVED")
            else:
                _insert_audit(cur, actor_user_id, own_id, tx_id, tx_type)

            balance, remain = _balance(cur, own_id)
        conn.commit()
        return {"transaction_id": tx_id, "type": tx_type, "status": "SUCCESS", "amount": amount,
                "wallet_id": own_id, "balance": balance, "remain_limit_week": remain}
    except ServiceError:
        conn.rollback()
        raise
    except MySQLError as exc:
        conn.rollback()
        raise translate_db_error(exc, operation) from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def deposit(get_connection, actor_user_id, wallet_id, amount):
    return _financial(get_connection, "Deposit", "DEPOSIT", actor_user_id,
                      None, parse_wallet_id(wallet_id), parse_amount(amount))


def withdraw(get_connection, actor_user_id, wallet_id, amount):
    return _financial(get_connection, "Withdrawal", "WITHDRAW", actor_user_id,
                      parse_wallet_id(wallet_id), None, parse_amount(amount))


def transfer(get_connection, actor_user_id, sender_id, receiver_id, amount):
    s = parse_wallet_id(sender_id, "Sender wallet")
    r = parse_wallet_id(receiver_id, "Receiver wallet")
    if s == r:
        raise ServiceError("SAME_WALLET", "You cannot transfer to the same wallet.")
    return _financial(get_connection, "Transfer", "TRANSFER", actor_user_id, s, r, parse_amount(amount))


# ------------------------------------------------------------------ wallet management
def create_wallet(get_connection, actor_user_id, currency="VND"):
    currency = str(currency).strip().upper()
    if currency not in CURRENCIES:
        raise ServiceError("CURRENCY_UNSUPPORTED", "Only VND and USD wallets are supported.")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # chi truyen (user_id, currency): limit_week / remain_limit_week do trigger dat
            cur.execute("INSERT INTO wallets (user_id, currency) VALUES (%s,%s)", (actor_user_id, currency))
            wid = cur.lastrowid
            _insert_audit(cur, actor_user_id, wid, None, "CREATE_WALLET")
            cur.execute("SELECT balance, currency, limit_week, remain_limit_week, status FROM wallets "
                        "WHERE wallet_id=%s", (wid,))
            b, c, lim, rem, st = cur.fetchone()
        conn.commit()
        return {"wallet_id": wid, "balance": b, "currency": c, "limit_week": lim,
                "remain_limit_week": rem, "status": st}
    except MySQLError as exc:
        conn.rollback()
        raise translate_db_error(exc, "Create wallet") from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def set_wallet_status(get_connection, actor_user_id, wallet_id, locked):
    """locked=True -> LOCKED (LOCK_WALLET), False -> ACTIVE (UNLOCK_WALLET)."""
    wid = parse_wallet_id(wallet_id)
    new_status, action = ("LOCKED", "LOCK_WALLET") if locked else ("ACTIVE", "UNLOCK_WALLET")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            wallets = _lock_wallets(cur, wid)
            if wid not in wallets:
                raise ServiceError("WALLET_NOT_FOUND", "The wallet does not exist.")
            if wallets[wid][0] != actor_user_id:
                raise ServiceError("FORBIDDEN", "This wallet does not belong to you.")
            cur.execute("UPDATE wallets SET status=%s WHERE wallet_id=%s", (new_status, wid))
            _insert_audit(cur, actor_user_id, wid, None, action)
        conn.commit()
        return {"wallet_id": wid, "status": new_status}
    except ServiceError:
        conn.rollback()
        raise
    except MySQLError as exc:
        conn.rollback()
        raise translate_db_error(exc, "Update wallet") from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()