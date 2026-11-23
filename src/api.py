"""REST API entry point. GUI is an HTTP client; all business logic remains in services."""
import base64
import hashlib
import hmac
import json
import time
from contextlib import contextmanager

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import get_settings
from src.config.database.connection import get_db_connection
from src.container import build_controllers
from src.common.errors import ServiceError

app = FastAPI(title="E-Wallet REST API", version="1.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@contextmanager
def controllers():
    conn = get_db_connection()
    try:
        c = build_controllers(conn)
        yield c, c.admin
    finally:
        conn.close()

def _b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def create_token(user_id):
    cfg = get_settings()["security"]
    payload = _b64(json.dumps({"sub": int(user_id), "exp": int(time.time()) + int(cfg.get("token_ttl_seconds", 43200))}, separators=(",", ":")).encode())
    signature = _b64(hmac.new(cfg["token_secret"].encode(), payload.encode(), hashlib.sha256).digest())
    return payload + "." + signature

def token_user(authorization):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required.")
    try:
        payload, signature = authorization[7:].split(".", 1)
        secret = get_settings()["security"]["token_secret"].encode()
        expected = _b64(hmac.new(secret, payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected): raise ValueError()
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if int(data["exp"]) < int(time.time()): raise ValueError()
        return int(data["sub"])
    except Exception:
        raise HTTPException(401, "Invalid or expired session. Please sign in again.")

def run(operation, authorization=None, body=None):
    body = body or {}
    try:
        uid = None if operation in ("login", "register") else token_user(authorization)
        with controllers() as (c, a):
            if operation == "login":
                user = c.users.login(body.get("phone", ""), body.get("password", ""))
                return {"user": user, "access_token": create_token(user["user_id"]), "token_type": "bearer"}
            if operation == "register":
                uid = c.users.register(body.get("name"), body.get("password"), body.get("email"), body.get("phone"), body.get("currency"))
                return {"user_id": uid}
            if operation == "logout": return c.users.logout(uid) or {"ok": True}
            if operation == "profile": return c.users.get_user_by_id(uid)
            if operation == "update_profile": return c.users.update_profile(uid, body.get("name"), body.get("email"), body.get("phone"))
            if operation == "change_password": return c.users.change_password(uid, body.get("old_password"), body.get("new_password")) or {"ok": True}
            if operation == "wallets": return c.wallets.list_wallets(uid)
            if operation == "create_wallet": return c.wallets.create_wallet(uid, body.get("currency"))
            if operation == "set_wallet_locked":
                return c.wallets.lock_wallet(uid, body.get("wallet_id")) if body.get("locked") else c.wallets.unlock_wallet(uid, body.get("wallet_id"))
            if operation == "deposit": return c.transactions.deposit(uid, body.get("wallet_id"), body.get("amount"))
            if operation == "withdraw": return c.transactions.withdraw(uid, body.get("wallet_id"), body.get("amount"))
            if operation == "transfer": return c.transactions.transfer(uid, body.get("sender_id"), body.get("receiver_id"), body.get("amount"))
            if operation == "history": return c.transactions.history(uid, body.get("tx_type"), body.get("status"), body.get("limit", 100))
            if operation == "transaction_detail": return c.transactions.transaction_detail(uid, body.get("transaction_id"))
            if operation == "activity": return c.audit.get_activity(uid, body.get("action"), body.get("limit", 100))
            if operation == "user_profile": return c.profiles.get_profile(uid) or {}
            if operation == "save_user_profile":
                return c.profiles.save_profile(uid, body.get("age"), body.get("sex"), body.get("address"), body.get("job"), body.get("country"))
            if operation == "banks": return c.banks.list_banks()
            if operation == "bank_accounts": return c.banks.list_my_links(uid)
            if operation == "link_bank": return c.banks.link_wallet(uid, body.get("wallet_id"), body.get("bank_id"))
            if operation == "statistics": return c.statistics.my_statistics(uid, body.get("date_from"), body.get("date_to"))
            if operation == "admin_users": return a.list_users(uid)
            if operation == "admin_wallets": return a.list_wallets(uid, user_id=body.get("user_id"))
            if operation == "admin_set_wallet_locked":
                return a.lock_wallet(uid, body.get("wallet_id")) if body.get("locked") else a.unlock_wallet(uid, body.get("wallet_id"))
            if operation == "admin_transactions": return a.list_transactions(uid, body.get("tx_type"), body.get("status"))
            if operation == "admin_transaction_detail": return a.get_transaction(uid, body.get("transaction_id"))
            if operation == "admin_audit_logs": return a.list_audit_logs(uid, user_id=body.get("user_id"), action=body.get("action"))
            if operation == "admin_user_profile": return a.get_user_profile(uid, body.get("user_id")) or {}
            if operation == "admin_user_profiles":
                return a.list_user_profiles(uid, page=body.get("page", 1), page_size=body.get("page_size", 20),
                                            search=body.get("search"), sex=body.get("sex"), country=body.get("country"),
                                            sort_by=body.get("sort_by", "created_at"), sort_order=body.get("sort_order", "DESC"))
            if operation == "admin_bank_accounts": return a.list_bank_accounts(uid)
            if operation == "admin_partner_banks": return a.list_partner_banks(uid)
            if operation == "admin_create_partner_bank": return a.create_partner_bank(uid, body.get("name"))
            if operation == "admin_delete_partner_bank": return a.delete_partner_bank(uid, body.get("bank_id"))
            if operation == "admin_bank_statistics": return a.bank_statistics(uid)
            if operation == "admin_system_statistics": return a.system_statistics(uid)
            # Composite read endpoints reduce Cloudflare round-trips on high-latency links.
            if operation == "dashboard_summary":
                return {"wallets": c.wallets.list_wallets(uid),
                        "transactions": c.transactions.history(uid, None, None, 8)}
            if operation == "bank_page_data":
                return {"wallets": c.wallets.list_wallets(uid),
                        "banks": c.banks.list_banks(),
                        "bank_accounts": c.banks.list_my_links(uid)}
            raise HTTPException(404, "Unknown API operation.")
    except ServiceError as exc:
        code = getattr(exc, "code", "")
        status = 403 if code == "FORBIDDEN" else 401 if code == "AUTH_FAILED" else 400
        raise HTTPException(status_code=status, detail={"code": getattr(exc, "code", "ERROR"), "message": str(exc)})

@app.get("/health")
def health():
    # Lets desktop clients and operators confirm that the updated API process
    # is running, rather than an older uvicorn process still bound to the port.
    return {
        "status": "ok",
        "service": "ewallet-rest-api",
        "api_version": app.version,
        "capabilities": [
            "user_profile", "save_user_profile", "banks", "bank_accounts",
            "statistics", "admin_bank_accounts", "admin_partner_banks",
            "admin_create_partner_bank", "admin_delete_partner_bank", "admin_bank_statistics",
            "admin_system_statistics", "admin_transaction_detail", "admin_user_profiles",
            "dashboard_summary", "bank_page_data",
        ],
    }

@app.post("/api/{operation}")
def api_operation(operation: str, body: dict = None, authorization: str | None = Header(default=None)):
    return run(operation, authorization, body)

if __name__ == "__main__":
    import uvicorn
    api_cfg = get_settings()["api"]
    uvicorn.run("src.api:app", host=api_cfg.get("host", "127.0.0.1"), port=int(api_cfg.get("port", 8000)), reload=False, timeout_keep_alive=30)
