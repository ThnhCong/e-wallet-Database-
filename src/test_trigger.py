#!/usr/bin/env python3
"""
test_triggers.py - Kiem thu trigger / event / quyen cua he thong e-wallet (MySQL 8).

Cai dat:  pip install PyMySQL

Chay (bang tai khoan ADMIN, tren DB test):
    python test_triggers.py --user root --password 123456
    python test_triggers.py --user root --password 123456 --client-user Tina514160 --client-password '...'
    python test_triggers.py --skip-concurrency
Co the dung bien moi truong DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME.

LUU Y: transactions / audit_logs khong the DELETE (do trigger bao ve) nen du lieu test
(email 'trgtest_...') se con lai. Hay chay tren DB test (chay lai install.sh de lam sach).
"""
import argparse
import os
import sys
import threading
import uuid
from decimal import Decimal

import pymysql
from pymysql import err as mysql_errors

CFG = {}
ARGS = None
RESULTS = []  # (name, ok, detail)
NOTES = []
D = Decimal


# ----------------------------------------------------------------- helpers
def connect(user=None, password=None):
    cfg = dict(CFG)
    if user is not None:
        cfg["user"], cfg["password"] = user, password or ""
    conn = pymysql.connect(**cfg)
    conn.autocommit(False)
    return conn


def record(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  -> {detail}" if detail and not ok else ""))


def check(name, cond, detail=""):
    record(name, bool(cond), detail)


def error_sqlstate(e):
    """Lay SQLSTATE tu exception PyMySQL, neu co."""
    sqlstate = getattr(e, "sqlstate", None)
    if sqlstate:
        return sqlstate

    # PyMySQL thuong khong expose sqlstate truc tiep tren exception.
    # Mot so exception co sqlstate thong qua args / thuoc tinh cua class.
    return getattr(e, "sqlstate", None)


def error_msg(e):
    """Lay message theo phong cach gan voi mysql-connector."""
    return getattr(e, "msg", str(e))


def expect_reject(conn, name, fn, msg_part):
    """fn() phai bi trigger tu choi (SQLSTATE 45000) voi thong bao chua msg_part."""
    try:
        fn()
        conn.rollback()
        record(name, False, "Khong bi tu choi (lenh da chay thanh cong)")
    except mysql_errors.Error as e:
        conn.rollback()
        text = error_msg(e)

        # PyMySQL khong phai exception nao cung expose SQLSTATE truc tiep.
        # Trigger SIGNAL SQLSTATE 45000 cua MySQL van can duoc kiem tra.
        sqlstate = error_sqlstate(e)

        # Neu driver khong expose sqlstate, kiem tra message trigger.
        # MySQL SIGNAL voi SQLSTATE 45000 thuong duoc PyMySQL tra ve
        # voi errno 1644.
        ok_state = (
            sqlstate == "45000"
            or getattr(e, "args", [None])[0] == 1644
            or getattr(e, "errno", None) == 1644
        )

        ok = ok_state and (msg_part.lower() in text.lower())

        record(
            name,
            ok,
            f"sqlstate={sqlstate}, errno={getattr(e, 'errno', None)}, "
            f"msg='{text}' (mong doi chua '{msg_part}')"
        )


def expect_errno(conn, name, fn, errnos):
    """fn() phai bi tu choi boi rang buoc / quyen (errno nam trong errnos)."""
    errnos = (errnos,) if isinstance(errnos, int) else tuple(errnos)
    try:
        fn()
        conn.rollback()
        record(name, False, "Khong bi tu choi")
    except mysql_errors.Error as e:
        conn.rollback()
        errno = getattr(e, "errno", None)
        record(
            name,
            errno in errnos,
            f"errno={errno} (mong doi {errnos}), msg='{error_msg(e)}'"
        )


def exec_(conn, sql, params=()):
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur


def create_user(conn):
    tag = uuid.uuid4().hex[:10]
    cur = exec_(conn,
                "INSERT INTO users (user_name, password_hash, email, phone) VALUES (%s,%s,%s,%s)",
                (f"trgtest_{tag}", "x" * 20, f"trgtest_{tag}@test.com", f"9{int(tag, 16) % 10**11:011d}"))
    conn.commit()
    return cur.lastrowid


def create_wallet(conn, user_id, currency="VND", limit=None, status="ACTIVE"):
    """Tao vi CHI voi (user_id, currency, status): limit_week / remain_limit_week do trigger dat.
    Neu truyen `limit` thi UPDATE lai (chi de tao vi han muc nho phuc vu test)."""
    cur = exec_(conn, "INSERT INTO wallets (user_id, currency, status) VALUES (%s,%s,%s)",
                (user_id, currency, status))
    wid = cur.lastrowid
    if limit is not None:
        exec_(conn, "UPDATE wallets SET limit_week=%s, remain_limit_week=%s WHERE wallet_id=%s",
              (limit, limit, wid))
    conn.commit()
    return wid


def get_wallet(conn, wid):
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("SELECT * FROM wallets WHERE wallet_id=%s", (wid,))
    row = cur.fetchone()
    conn.commit()
    return row


def get_tx(conn, tid):
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("SELECT * FROM transactions WHERE transaction_id=%s", (tid,))
    row = cur.fetchone()
    conn.commit()
    return row


def insert_tx(conn, tx_type, sender, receiver, amount, status=None, commit=True):
    if status is None:
        cur = exec_(conn, "INSERT INTO transactions (sender_id, receiver_id, type, amount) VALUES (%s,%s,%s,%s)",
                    (sender, receiver, tx_type, amount))
    else:
        cur = exec_(conn,
                    "INSERT INTO transactions (sender_id, receiver_id, type, amount, status) VALUES (%s,%s,%s,%s,%s)",
                    (sender, receiver, tx_type, amount, status))
    if commit:
        conn.commit()
    return cur.lastrowid


def set_status(conn, tid, status, commit=True):
    exec_(conn, "UPDATE transactions SET status=%s WHERE transaction_id=%s", (status, tid))
    if commit:
        conn.commit()


def lock_wallets(conn, *ids):
    """Khoa cac vi theo thu tu wallet_id tang dan NGAY DAU giao dich (tranh deadlock do khoa chia se FK)."""
    ids = sorted({i for i in ids if i is not None})
    if not ids:
        return
    ph = ",".join(["%s"] * len(ids))
    exec_(conn, f"SELECT wallet_id FROM wallets WHERE wallet_id IN ({ph}) ORDER BY wallet_id FOR UPDATE",
          tuple(ids)).fetchall()


def run_tx(conn, tx_type, sender, receiver, amount, final="SUCCESS"):
    """Quy trinh chuan: lock vi -> insert PENDING -> doi sang SUCCESS/FAIL -> commit (1 DB transaction)."""
    try:
        lock_wallets(conn, sender, receiver)
        tid = insert_tx(conn, tx_type, sender, receiver, amount, commit=False)
        set_status(conn, tid, final, commit=False)
        conn.commit()
        return tid
    except Exception:
        conn.rollback()
        raise


def fund(conn, wid, amount):
    return run_tx(conn, "DEPOSIT", None, wid, amount)


def flag_is_off(conn):
    v = exec_(conn, "SELECT IFNULL(@allow_balance_update, 0)").fetchone()[0]
    conn.commit()
    return int(v) == 0


# ----------------------------------------------------------------- schema / metadata
def check_schema_and_triggers(conn):
    db = CFG["database"]
    cur = exec_(conn, "SELECT column_name, column_type, column_default FROM information_schema.columns "
                      "WHERE table_schema=%s AND table_name='wallets'", (db,))
    cols = {r[0].lower(): r for r in cur.fetchall()}
    conn.commit()
    if "remain_limit_week" not in cols:
        print("!! Bang wallets thieu cot remain_limit_week -> chay lai install.sh")
        return False
    check("wallets.status la ENUM('ACTIVE','LOCKED')", "'locked'" in str(cols["status"][1]).lower(),
          str(cols["status"][1]))
    check("wallets.limit_week / remain_limit_week co DEFAULT",
          cols["limit_week"][2] is not None and cols["remain_limit_week"][2] is not None)

    expected = [
        "trg_transactions_before_insert", "trg_transactions_after_update",
        "trg_transactions_before_update", "trg_transactions_before_delete",
        "trg_wallets_before_insert", "trg_wallets_before_update",
        "trg_wallets_before_delete", "trg_audit_logs_before_update",
        "trg_audit_logs_before_delete",
    ]
    cur = exec_(conn, "SELECT trigger_name FROM information_schema.triggers WHERE trigger_schema=%s", (db,))
    found = {r[0].lower() for r in cur.fetchall()}
    conn.commit()
    for t in expected:
        check(f"Trigger ton tai: {t}", t in found)
    check("Dung 9 trigger (khong co trigger thua)", len(found) == 9, str(sorted(found)))
    return True


# ----------------------------------------------------------------- tests
def test_wallet_triggers(conn, ctx):
    u = ctx["user"]
    w = ctx["A"]
    row = get_wallet(conn, create_wallet(conn, u))
    check("Vi VND moi (chi truyen user_id, currency): balance=0, ACTIVE, limit=10.000.000, remain=limit",
          row["balance"] == 0 and row["status"] == "ACTIVE"
          and row["limit_week"] == D("10000000") and row["remain_limit_week"] == row["limit_week"], str(row))
    row = get_wallet(conn, ctx["USD"])
    check("Vi USD moi: limit_week=500, remain=500",
          row["limit_week"] == D("500") and row["remain_limit_week"] == D("500"), str(row))

    cur = exec_(conn, "INSERT INTO wallets (user_id, currency, limit_week, remain_limit_week) "
                      "VALUES (%s,'usd',123,123)", (u,))
    conn.commit()
    row = get_wallet(conn, cur.lastrowid)
    check("Currency 'usd' (chu thuong) duoc chuan hoa 'USD'; limit_week nguoi dung truyen bi ghi de = 500",
          row["currency"] == "USD" and row["limit_week"] == D("500") and row["remain_limit_week"] == D("500"),
          str(row))
    expect_reject(conn, "Tao vi currency khong ho tro (EUR) bi tu choi",
                  lambda: exec_(conn, "INSERT INTO wallets (user_id, currency) VALUES (%s,'EUR')", (u,)),
                  "Unsupported currency")
    expect_reject(conn, "Tao vi voi balance > 0 bi tu choi",
                  lambda: exec_(conn, "INSERT INTO wallets (user_id, currency, balance) VALUES (%s,'VND',100)", (u,)),
                  "must start with balance 0")

    expect_errno(conn, "CHECK: remain_limit_week > limit_week bi tu choi",
                 lambda: exec_(conn, "UPDATE wallets SET remain_limit_week = limit_week + 1 WHERE wallet_id=%s", (w,)),
                 3819)
    expect_errno(conn, "CHECK: remain_limit_week am bi tu choi",
                 lambda: exec_(conn, "UPDATE wallets SET remain_limit_week = -1 WHERE wallet_id=%s", (w,)), 3819)
    expect_reject(conn, "Doi currency cua vi bi tu choi",
                  lambda: exec_(conn, "UPDATE wallets SET currency='USD' WHERE wallet_id=%s", (w,)),
                  "currency cannot be changed")


def test_insert_validation(conn, ctx):
    A, B, USD, LOCKED, LIM = ctx["A"], ctx["B"], ctx["USD"], ctx["LOCKED"], ctx["LIM"]
    NOEXIST = 999_999_999

    expect_reject(conn, "INSERT: amount = 0 bi tu choi",
                  lambda: insert_tx(conn, "DEPOSIT", None, A, 0), "Amount must be greater than 0")
    expect_reject(conn, "INSERT: amount am bi tu choi",
                  lambda: insert_tx(conn, "DEPOSIT", None, A, -5), "Amount must be greater than 0")
    expect_reject(conn, "INSERT: status SUCCESS ngay tu dau bi tu choi",
                  lambda: insert_tx(conn, "DEPOSIT", None, A, 10, status="SUCCESS"), "must have status PENDING")
    expect_reject(conn, "INSERT: DEPOSIT co sender bi tu choi",
                  lambda: insert_tx(conn, "DEPOSIT", B, A, 10), "DEPOSIT requires")
    expect_reject(conn, "INSERT: DEPOSIT khong co receiver bi tu choi",
                  lambda: insert_tx(conn, "DEPOSIT", None, None, 10), "DEPOSIT requires")
    expect_reject(conn, "INSERT: WITHDRAW co receiver bi tu choi",
                  lambda: insert_tx(conn, "WITHDRAW", A, B, 10), "WITHDRAW requires")
    expect_reject(conn, "INSERT: WITHDRAW khong co sender bi tu choi",
                  lambda: insert_tx(conn, "WITHDRAW", None, None, 10), "WITHDRAW requires")
    expect_reject(conn, "INSERT: TRANSFER thieu receiver bi tu choi",
                  lambda: insert_tx(conn, "TRANSFER", A, None, 10), "TRANSFER requires both")
    expect_reject(conn, "INSERT: TRANSFER thieu sender bi tu choi",
                  lambda: insert_tx(conn, "TRANSFER", None, B, 10), "TRANSFER requires both")
    expect_reject(conn, "INSERT: TRANSFER cung vi bi tu choi",
                  lambda: insert_tx(conn, "TRANSFER", A, A, 10), "cannot be the same wallet")

    # --- vi khong ton tai: phai nhan DUNG thong bao cua trigger, khong phai loi he thong (1329 / 1452)
    expect_reject(conn, "INSERT: TRANSFER den vi KHONG TON TAI -> 'Receiver wallet does not exist'",
                  lambda: insert_tx(conn, "TRANSFER", A, NOEXIST, 10), "Receiver wallet does not exist")
    expect_reject(conn, "INSERT: TRANSFER tu vi KHONG TON TAI -> 'Sender wallet does not exist'",
                  lambda: insert_tx(conn, "TRANSFER", NOEXIST, B, 10), "Sender wallet does not exist")
    expect_reject(conn, "INSERT: DEPOSIT vao vi KHONG TON TAI -> 'Receiver wallet does not exist'",
                  lambda: insert_tx(conn, "DEPOSIT", None, NOEXIST, 10), "Receiver wallet does not exist")
    expect_reject(conn, "INSERT: WITHDRAW tu vi KHONG TON TAI -> 'Sender wallet does not exist'",
                  lambda: insert_tx(conn, "WITHDRAW", NOEXIST, None, 10), "Sender wallet does not exist")

    expect_reject(conn, "INSERT: DEPOSIT vao vi LOCKED bi tu choi",
                  lambda: insert_tx(conn, "DEPOSIT", None, LOCKED, 10), "Receiver wallet is locked")
    expect_reject(conn, "INSERT: WITHDRAW tu vi LOCKED bi tu choi",
                  lambda: insert_tx(conn, "WITHDRAW", LOCKED, None, 10), "Sender wallet is locked")
    expect_reject(conn, "INSERT: TRANSFER tu vi LOCKED bi tu choi",
                  lambda: insert_tx(conn, "TRANSFER", LOCKED, B, 10), "Sender wallet is locked")
    expect_reject(conn, "INSERT: TRANSFER den vi LOCKED bi tu choi",
                  lambda: insert_tx(conn, "TRANSFER", A, LOCKED, 10), "Receiver wallet is locked")

    bal = get_wallet(conn, A)["balance"]
    expect_reject(conn, "INSERT: WITHDRAW vuot so du bi tu choi",
                  lambda: insert_tx(conn, "WITHDRAW", A, None, bal + 1), "Insufficient balance")
    expect_reject(conn, "INSERT: TRANSFER vuot so du bi tu choi",
                  lambda: insert_tx(conn, "TRANSFER", A, B, bal + 1), "Insufficient balance")
    expect_reject(conn, "INSERT: TRANSFER khac currency (VND -> USD) bi tu choi",
                  lambda: insert_tx(conn, "TRANSFER", A, USD, 10), "same currency")
    expect_reject(conn, "INSERT: TRANSFER vuot han muc tuan bi tu choi (limit 1000, chuyen 1500)",
                  lambda: insert_tx(conn, "TRANSFER", LIM, B, 1500), "Weekly transfer limit exceeded")

    try:
        fund(conn, LIM, 50_000)
        record("DEPOSIT 50.000 vao vi co limit_week 1000: khong bi gioi han", True)
    except Exception as e:
        conn.rollback()
        record("DEPOSIT 50.000 vao vi co limit_week 1000: khong bi gioi han", False, str(e))


def test_successful_flows(conn, ctx):
    A, B, LIM = ctx["A"], ctx["B"], ctx["LIM"]

    a0 = get_wallet(conn, A)
    tid = fund(conn, A, 1_000)
    a1 = get_wallet(conn, A)
    check("DEPOSIT SUCCESS: balance tang dung so tien", a1["balance"] == a0["balance"] + 1000,
          f"{a0['balance']} -> {a1['balance']}")
    check("DEPOSIT SUCCESS: transaction.status = SUCCESS", get_tx(conn, tid)["status"] == "SUCCESS")
    check("DEPOSIT khong doi remain_limit_week", a1["remain_limit_week"] == a0["remain_limit_week"])

    a0 = get_wallet(conn, A)
    run_tx(conn, "WITHDRAW", A, None, 300)
    a1 = get_wallet(conn, A)
    check("WITHDRAW SUCCESS: balance giam dung so tien", a1["balance"] == a0["balance"] - 300,
          f"{a0['balance']} -> {a1['balance']}")
    check("WITHDRAW khong tru remain_limit_week", a1["remain_limit_week"] == a0["remain_limit_week"])

    a0, b0 = get_wallet(conn, A), get_wallet(conn, B)
    run_tx(conn, "TRANSFER", A, B, 400)
    a1, b1 = get_wallet(conn, A), get_wallet(conn, B)
    check("TRANSFER SUCCESS: sender giam, receiver tang",
          a1["balance"] == a0["balance"] - 400 and b1["balance"] == b0["balance"] + 400,
          f"A {a0['balance']}->{a1['balance']}, B {b0['balance']}->{b1['balance']}")
    check("TRANSFER SUCCESS: tong tien 2 vi khong doi",
          a1["balance"] + b1["balance"] == a0["balance"] + b0["balance"])
    check("TRANSFER SUCCESS: sender.remain_limit_week giam dung so tien",
          a1["remain_limit_week"] == a0["remain_limit_week"] - 400,
          f"{a0['remain_limit_week']} -> {a1['remain_limit_week']}")
    check("TRANSFER SUCCESS: limit_week (co dinh) khong doi", a1["limit_week"] == a0["limit_week"])
    check("TRANSFER SUCCESS: remain_limit_week <= limit_week", a1["remain_limit_week"] <= a1["limit_week"])
    check("TRANSFER SUCCESS: receiver.remain_limit_week khong doi",
          b1["remain_limit_week"] == b0["remain_limit_week"])

    a0 = get_wallet(conn, A)
    tid = run_tx(conn, "WITHDRAW", A, None, 100, final="FAIL")
    check("PENDING -> FAIL: balance khong doi", get_wallet(conn, A)["balance"] == a0["balance"])
    check("PENDING -> FAIL: status = FAIL", get_tx(conn, tid)["status"] == "FAIL")

    rem = get_wallet(conn, LIM)["remain_limit_week"]  # 1000
    run_tx(conn, "TRANSFER", LIM, B, rem)
    check("TRANSFER dung bang remain_limit_week: remain = 0", get_wallet(conn, LIM)["remain_limit_week"] == 0)
    expect_reject(conn, "TRANSFER khi remain_limit_week = 0 bi tu choi",
                  lambda: insert_tx(conn, "TRANSFER", LIM, B, 1), "Weekly transfer limit exceeded")


def test_transaction_protection(conn, ctx):
    A, B = ctx["A"], ctx["B"]
    done = run_tx(conn, "DEPOSIT", None, A, 50)

    expect_reject(conn, "UPDATE giao dich SUCCESS -> FAIL bi tu choi",
                  lambda: set_status(conn, done, "FAIL"), "Completed transactions cannot be modified")
    expect_reject(conn, "UPDATE amount cua giao dich SUCCESS bi tu choi",
                  lambda: exec_(conn, "UPDATE transactions SET amount=999 WHERE transaction_id=%s", (done,)),
                  "Completed transactions cannot be modified")
    failed = run_tx(conn, "DEPOSIT", None, A, 50, final="FAIL")
    expect_reject(conn, "UPDATE giao dich FAIL -> SUCCESS bi tu choi",
                  lambda: set_status(conn, failed, "SUCCESS"), "Completed transactions cannot be modified")

    pend = insert_tx(conn, "DEPOSIT", None, A, 70)
    expect_reject(conn, "PENDING -> PENDING (khong doi trang thai) bi tu choi",
                  lambda: set_status(conn, pend, "PENDING"), "can only become SUCCESS or FAIL")
    expect_reject(conn, "PENDING: doi amount bi tu choi",
                  lambda: exec_(conn, "UPDATE transactions SET amount=700, status='SUCCESS' WHERE transaction_id=%s",
                                (pend,)), "Only the status")
    expect_reject(conn, "PENDING: doi receiver_id bi tu choi",
                  lambda: exec_(conn, "UPDATE transactions SET receiver_id=%s, status='SUCCESS' "
                                      "WHERE transaction_id=%s", (B, pend)), "Only the status")
    expect_reject(conn, "PENDING: doi type bi tu choi",
                  lambda: exec_(conn, "UPDATE transactions SET type='WITHDRAW', status='SUCCESS' "
                                      "WHERE transaction_id=%s", (pend,)), "Only the status")
    t = get_tx(conn, pend)
    check("Giao dich PENDING van nguyen sau cac lan bi tu choi", t["status"] == "PENDING" and t["amount"] == 70)
    set_status(conn, pend, "SUCCESS")

    expect_reject(conn, "DELETE transaction bi tu choi",
                  lambda: exec_(conn, "DELETE FROM transactions WHERE transaction_id=%s", (done,)),
                  "cannot be deleted")


def test_wallet_protection(conn, ctx):
    A = ctx["A"]
    expect_reject(conn, "UPDATE truc tiep balance (tang) bi tu choi",
                  lambda: exec_(conn, "UPDATE wallets SET balance = balance + 1 WHERE wallet_id=%s", (A,)),
                  "Balance can only be changed")
    expect_reject(conn, "UPDATE truc tiep balance (so am) bi tu choi",
                  lambda: exec_(conn, "UPDATE wallets SET balance = -1 WHERE wallet_id=%s", (A,)),
                  "cannot be negative")
    try:
        exec_(conn, "UPDATE wallets SET status='LOCKED' WHERE wallet_id=%s", (A,))
        exec_(conn, "UPDATE wallets SET status='ACTIVE' WHERE wallet_id=%s", (A,))
        conn.commit()
        record("Khoa/mo khoa vi (UPDATE status) van hoat dong", True)
    except Exception as e:
        conn.rollback()
        record("Khoa/mo khoa vi (UPDATE status) van hoat dong", False, str(e))

    check("Flag @allow_balance_update tu tat sau giao dich", flag_is_off(conn))
    expect_reject(conn, "DELETE vi co lich su giao dich bi tu choi",
                  lambda: exec_(conn, "DELETE FROM wallets WHERE wallet_id=%s", (A,)), "cannot be deleted")

    empty = create_wallet(conn, ctx["user"])
    try:
        exec_(conn, "DELETE FROM wallets WHERE wallet_id=%s", (empty,))
        conn.commit()
        record("DELETE vi KHONG co lich su giao dich: duoc phep", True)
    except Exception as e:
        conn.rollback()
        record("DELETE vi KHONG co lich su giao dich: duoc phep", False, str(e))


def test_recheck_on_success(conn, ctx):
    """Kiem tra lai khi PENDING -> SUCCESS (so du / trang thai / han muc doi o giua)."""
    w = create_wallet(conn, ctx["user"])
    other = ctx["B"]
    fund(conn, w, 1000)

    p1 = insert_tx(conn, "WITHDRAW", w, None, 800)
    p2 = insert_tx(conn, "WITHDRAW", w, None, 800)  # ca 2 deu qua BEFORE INSERT vi so du 1000
    set_status(conn, p1, "SUCCESS")
    expect_reject(conn, "Re-check: PENDING thu 2 -> SUCCESS bi tu choi (het so du)",
                  lambda: set_status(conn, p2, "SUCCESS"), "Insufficient balance")
    check("Re-check: giao dich bi tu choi van la PENDING, so du = 200",
          get_tx(conn, p2)["status"] == "PENDING" and get_wallet(conn, w)["balance"] == 200)
    set_status(conn, p2, "FAIL")
    check("Re-check: danh dau FAIL khong doi so du", get_wallet(conn, w)["balance"] == 200)

    p3 = insert_tx(conn, "WITHDRAW", w, None, 100)
    exec_(conn, "UPDATE wallets SET status='LOCKED' WHERE wallet_id=%s", (w,))
    conn.commit()
    expect_reject(conn, "Re-check: sender bi khoa sau khi PENDING -> SUCCESS bi tu choi",
                  lambda: set_status(conn, p3, "SUCCESS"), "Sender wallet is locked")
    exec_(conn, "UPDATE wallets SET status='ACTIVE' WHERE wallet_id=%s", (w,))
    conn.commit()
    set_status(conn, p3, "SUCCESS")
    check("Re-check: mo khoa vi roi SUCCESS thanh cong, so du = 100", get_wallet(conn, w)["balance"] == 100)

    p4 = insert_tx(conn, "TRANSFER", w, other, 10)
    exec_(conn, "UPDATE wallets SET status='LOCKED' WHERE wallet_id=%s", (other,))
    conn.commit()
    expect_reject(conn, "Re-check: receiver bi khoa sau khi PENDING -> SUCCESS bi tu choi",
                  lambda: set_status(conn, p4, "SUCCESS"), "Receiver wallet is locked")
    exec_(conn, "UPDATE wallets SET status='ACTIVE' WHERE wallet_id=%s", (other,))
    conn.commit()
    set_status(conn, p4, "FAIL")
    check("Re-check: flag @allow_balance_update van tat sau khi trigger nem loi", flag_is_off(conn))

    w2 = create_wallet(conn, ctx["user"], limit=1000)
    fund(conn, w2, 5000)
    q1 = insert_tx(conn, "TRANSFER", w2, other, 800)
    q2 = insert_tx(conn, "TRANSFER", w2, other, 800)
    set_status(conn, q1, "SUCCESS")
    expect_reject(conn, "Re-check: PENDING thu 2 vuot remain_limit_week bi tu choi",
                  lambda: set_status(conn, q2, "SUCCESS"), "Weekly transfer limit exceeded")
    set_status(conn, q2, "FAIL")
    w2r = get_wallet(conn, w2)
    check("Re-check: remain_limit_week = 200 (limit_week van 1000)",
          w2r["remain_limit_week"] == 200 and w2r["limit_week"] == 1000, str(w2r))


def test_audit_logs(conn, ctx):
    cur = exec_(conn, "INSERT INTO audit_logs (user_id, wallet_id, action) VALUES (%s,%s,'CREATE_WALLET')",
                (ctx["user"], ctx["A"]))
    conn.commit()
    log_id = cur.lastrowid
    check("Audit log: INSERT duoc phep", log_id is not None)
    expect_errno(conn, "Audit log: action ngoai 12 gia tri bi tu choi (CHECK)",
                 lambda: exec_(conn, "INSERT INTO audit_logs (user_id, action) VALUES (%s,'HACK')", (ctx["user"],)),
                 3819)
    expect_reject(conn, "Audit log: UPDATE bi tu choi",
                  lambda: exec_(conn, "UPDATE audit_logs SET action='LOGIN' WHERE audit_log_id=%s", (log_id,)),
                  "cannot be modified")
    expect_reject(conn, "Audit log: DELETE bi tu choi",
                  lambda: exec_(conn, "DELETE FROM audit_logs WHERE audit_log_id=%s", (log_id,)),
                  "cannot be deleted")


def test_weekly_reset_event(conn, ctx):
    row = exec_(conn, "SELECT status, starts FROM information_schema.events "
                      "WHERE event_schema=%s AND event_name='ev_reset_weekly_limit'", (CFG["database"],)).fetchone()
    check("Event ev_reset_weekly_limit ton tai", row is not None)
    if row:
        check("Event ev_reset_weekly_limit dang ENABLED", row[0] == "ENABLED", f"status={row[0]}")
        st = row[1]
        check("Event bat dau luc thu Hai 00:00", st.weekday() == 0 and st.hour == 0 and st.minute == 0, str(st))
    v = exec_(conn, "SHOW VARIABLES LIKE 'event_scheduler'").fetchone()
    conn.commit()
    check("event_scheduler = ON", v and v[1].upper() == "ON", f"event_scheduler={v[1] if v else None}")

    LIM = ctx["LIM"]
    before = get_wallet(conn, LIM)
    check("(chuan bi) vi LIM da dung het han muc", before["remain_limit_week"] == 0)
    exec_(conn, "UPDATE wallets SET remain_limit_week = limit_week WHERE remain_limit_week <> limit_week")
    conn.commit()  # = noi dung cua event
    after = get_wallet(conn, LIM)
    check("Reset: remain_limit_week = limit_week", after["remain_limit_week"] == after["limit_week"])
    check("Reset: khong dong vao balance", after["balance"] == before["balance"])
    try:
        run_tx(conn, "TRANSFER", LIM, ctx["B"], 100)
        record("Sau reset: co the TRANSFER lai", True)
    except Exception as e:
        conn.rollback()
        record("Sau reset: co the TRANSFER lai", False, str(e))


def test_client_privileges(conn, ctx):
    """Tai khoan ung dung (006): chi duoc quyen theo cot, van nap/rut/chuyen tien qua trigger duoc."""
    cc = connect(ARGS.client_user, ARGS.client_password)
    try:
        A, B = ctx["A"], ctx["B"]
        denied = (1142, 1143)
        expect_errno(cc, "Client: UPDATE truc tiep balance bi tu choi (quyen cot)",
                     lambda: exec_(cc, "UPDATE wallets SET balance = balance + 1 WHERE wallet_id=%s", (A,)), denied)

        def spoof():
            exec_(cc, "SET @allow_balance_update = 1")
            exec_(cc, "UPDATE wallets SET balance = balance + 1000000 WHERE wallet_id=%s", (A,))
        expect_errno(cc, "Client: gia mao co @allow_balance_update=1 van khong sua duoc balance", spoof, denied)
        expect_errno(cc, "Client: UPDATE remain_limit_week bi tu choi",
                     lambda: exec_(cc, "UPDATE wallets SET remain_limit_week = limit_week WHERE wallet_id=%s", (A,)),
                     denied)
        expect_errno(cc, "Client: INSERT wallet co balance bi tu choi",
                     lambda: exec_(cc, "INSERT INTO wallets (user_id, currency, balance) VALUES (%s,'VND',5)",
                                   (ctx["user"],)), denied)
        expect_errno(cc, "Client: DELETE transactions bi tu choi",
                     lambda: exec_(cc, "DELETE FROM transactions LIMIT 1"), denied)
        expect_errno(cc, "Client: UPDATE audit_logs bi tu choi",
                     lambda: exec_(cc, "UPDATE audit_logs SET action='LOGIN' LIMIT 1"), denied)

        try:
            exec_(cc, "UPDATE wallets SET status='LOCKED' WHERE wallet_id=%s", (ctx["LOCKED"],))
            exec_(cc, "UPDATE wallets SET status='ACTIVE' WHERE wallet_id=%s", (ctx["LOCKED"],))
            cc.rollback()
            record("Client: doi status vi (khoa/mo khoa) duoc phep", True)
        except Exception as e:
            cc.rollback()
            record("Client: doi status vi (khoa/mo khoa) duoc phep", False, str(e))

        a0, b0 = get_wallet(conn, A), get_wallet(conn, B)
        try:
            run_tx(cc, "DEPOSIT", None, A, 123)
            run_tx(cc, "WITHDRAW", A, None, 23)
            run_tx(cc, "TRANSFER", A, B, 50)
            ok, err = True, ""
        except Exception as e:
            cc.rollback()
            ok, err = False, str(e)
        a1, b1 = get_wallet(conn, A), get_wallet(conn, B)
        check("Client: NAP/RUT/CHUYEN qua trigger thanh cong", ok, err)
        if ok:
            check("Client: so du dung (A +123 -23 -50, B +50)",
                  a1["balance"] == a0["balance"] + 50 and b1["balance"] == b0["balance"] + 50,
                  f"A {a0['balance']}->{a1['balance']}, B {b0['balance']}->{b1['balance']}")
    finally:
        cc.close()


def test_concurrency(conn, ctx, iterations=30):
    """2 luong chuyen tien nguoc chieu X<->Y dong thoi: kiem tra bao toan tien va deadlock."""
    u = ctx["user"]
    X, Y = create_wallet(conn, u), create_wallet(conn, u)
    fund(conn, X, 1_000_000)
    fund(conn, Y, 1_000_000)
    stats = {"ok": [0, 0], "retry": 0, "err": []}
    lock = threading.Lock()

    def worker(idx, src, dst):
        c = connect()
        try:
            for _ in range(iterations):
                for _attempt in range(5):
                    try:
                        run_tx(c, "TRANSFER", src, dst, 1000)
                        with lock:
                            stats["ok"][idx] += 1
                        break
                    except mysql_errors.Error as e:
                        errno = getattr(e, "errno", None)
                        if errno in (1213, 1205):  # deadlock / lock wait timeout
                            with lock:
                                stats["retry"] += 1
                            continue
                        with lock:
                            stats["err"].append(f"{errno}: {error_msg(e)}")
                        break
        finally:
            c.close()

    t1 = threading.Thread(target=worker, args=(0, X, Y))
    t2 = threading.Thread(target=worker, args=(1, Y, X))
    t1.start(); t2.start(); t1.join(); t2.join()

    x, y = get_wallet(conn, X)["balance"], get_wallet(conn, Y)["balance"]
    ex = 1_000_000 - 1000 * stats["ok"][0] + 1000 * stats["ok"][1]
    ey = 1_000_000 + 1000 * stats["ok"][0] - 1000 * stats["ok"][1]
    check("Dong thoi: tong tien 2 vi bao toan", x + y == 2_000_000, f"X={x}, Y={y}")
    check("Dong thoi: so du khop voi so giao dich thanh cong", x == ex and y == ey,
          f"X={x} (mong doi {ex}), Y={y} (mong doi {ey})")
    check("Dong thoi: khong co loi bat ngo", not stats["err"], "; ".join(stats["err"][:3]))
    check("Dong thoi: khoa vi theo thu tu tang dan -> khong deadlock", stats["retry"] == 0,
          f"{stats['retry']} lan deadlock/timeout")
    NOTES.append(f"Dong thoi: X->Y {stats['ok'][0]}, Y->X {stats['ok'][1]}, retry deadlock/timeout: {stats['retry']}")


# ----------------------------------------------------------------- main
def main():
    global ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=os.getenv("DB_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.getenv("DB_PORT", "3306")))
    ap.add_argument("--user", default="Tina514160")
    ap.add_argument("--password", default="514160")
    ap.add_argument("--database", default=os.getenv("DB_NAME", "ewallet"))
    ap.add_argument("--client-user", default=os.getenv("DB_CLIENT_USER", ""))
    ap.add_argument("--client-password", default=os.getenv("DB_CLIENT_PASSWORD", ""))
    ap.add_argument("--skip-concurrency", action="store_true")
    ARGS = ap.parse_args()
    CFG.update(host=ARGS.host, port=ARGS.port, user=ARGS.user, password=ARGS.password, database=ARGS.database)

    print(f"Ket noi MySQL {ARGS.user}@{ARGS.host}:{ARGS.port}/{ARGS.database} ...")
    try:
        conn = connect()
    except mysql_errors.Error as e:
        print(f"Khong ket noi duoc: {e}")
        sys.exit(2)

    print("\n=== Schema + danh sach trigger ===")
    if not check_schema_and_triggers(conn):
        sys.exit(2)

    u = create_user(conn)
    ctx = {"user": u}
    ctx["A"] = create_wallet(conn, u)
    ctx["B"] = create_wallet(conn, create_user(conn))
    ctx["USD"] = create_wallet(conn, u, currency="USD")
    ctx["LOCKED"] = create_wallet(conn, u, status="LOCKED")
    ctx["LIM"] = create_wallet(conn, u, limit=1000)
    fund(conn, ctx["A"], 5000)
    fund(conn, ctx["B"], 1000)
    fund(conn, ctx["LIM"], 5000)

    groups = [
        ("Trigger tao vi + CHECK constraint", test_wallet_triggers),
        ("Validate Transaction BEFORE INSERT", test_insert_validation),
        ("Luong thanh cong DEPOSIT/WITHDRAW/TRANSFER", test_successful_flows),
        ("Bao ve giao dich (BEFORE UPDATE/DELETE)", test_transaction_protection),
        ("Bao ve vi (balance / xoa vi)", test_wallet_protection),
        ("Re-check khi PENDING -> SUCCESS", test_recheck_on_success),
        ("Audit logs bat bien", test_audit_logs),
        ("Event reset han muc tuan", test_weekly_reset_event),
    ]
    if ARGS.client_user:
        groups.append(("Quyen cua tai khoan ung dung (client)", test_client_privileges))
    else:
        NOTES.append("Bo qua test quyen client (them --client-user / --client-password de chay)")
    if not ARGS.skip_concurrency:
        groups.append(("Dong thoi / deadlock", test_concurrency))

    for title, fn in groups:
        print(f"\n=== {title} ===")
        try:
            fn(conn, ctx)
        except Exception as e:
            conn.rollback()
            record(f"{title}: bai test bi loi", False, f"{type(e).__name__}: {e}")

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = [r for r in RESULTS if not r[1]]
    print("\n" + "=" * 60)
    for n in NOTES:
        print("  * " + n)
    print(f"TONG KET: {passed}/{len(RESULTS)} PASS, {len(failed)} FAIL")
    for name, _, detail in failed:
        print(f"  - {name}\n      {detail}")
    conn.close()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
