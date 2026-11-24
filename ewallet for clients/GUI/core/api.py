"""Thread-safe REST client with keep-alive pooling and background dispatch.

All API operations retain the existing POST /api/{operation} contract.
Write operations are never automatically retried. Only explicitly read-only
operations may be retried once after a transport-level connection failure.
"""
from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

import httpx
from PySide6.QtCore import QObject, QThreadPool, Slot

from GUI.core.worker import Worker


READ_OPERATIONS = {
    "profile", "wallets", "history", "transaction_detail", "activity",
    "admin_users", "admin_wallets", "admin_transactions",
    "admin_transaction_detail", "admin_audit_logs", "user_profile", "banks",
    "bank_accounts", "statistics", "admin_user_profile", "admin_user_profiles",
    "admin_bank_accounts", "admin_partner_banks", "admin_bank_statistics",
    "admin_system_statistics", "dashboard_summary", "bank_page_data",
}


def _application_root() -> Path:
    if getattr(sys, "frozen", False):
        # For onedir, config sits beside the executable. For onefile, PyInstaller
        # extracts bundled data into _MEIPASS.
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "client_config.json").exists():
            return exe_dir
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass).resolve()
        return exe_dir
    return Path(__file__).resolve().parents[2]


def _resolve_base_url() -> str:
    env_url = os.getenv("EWALLET_API_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")

    root = _application_root()
    candidates = [root / "client_config.json", root / "ewallet for clients" / "client_config.json"]
    for config_path in candidates:
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            url = str(config.get("api", {}).get("base_url", "")).strip()
            if url:
                return url.rstrip("/")
        except (OSError, ValueError, TypeError, AttributeError):
            continue
    return "http://127.0.0.1:8000"


class _CallbackBridge(QObject):
    """QObject bridge ensures callbacks execute on the GUI thread."""
    def __init__(self, success, failure, cleanup):
        super().__init__()
        self._success = success
        self._failure = failure
        self._cleanup = cleanup

    @Slot(object)
    def succeeded(self, value):
        if self._success:
            self._success(value)

    @Slot(str)
    def failed(self, message):
        if self._failure:
            self._failure(message)

    @Slot()
    def finished(self):
        self._cleanup(self)


class Api:
    def __init__(self):
        self.base_url = _resolve_base_url()
        self.token = None
        self._token_lock = threading.RLock()
        self._request_context = threading.local()
        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(connect=7.0, read=30.0, write=15.0, pool=5.0),
            limits=httpx.Limits(max_connections=16, max_keepalive_connections=8, keepalive_expiry=25.0),
            http2=True,
            follow_redirects=True,
        )
        self._pool = QThreadPool.globalInstance()
        self._pool.setMaxThreadCount(max(4, min(8, self._pool.maxThreadCount())))
        self._active = set()
        self._active_lock = threading.Lock()

    def close(self):
        self._http.close()

    def run_async(self, function, *args, on_success=None, on_error=None, **kwargs):
        """Run an existing API method in a Qt worker; callbacks run on GUI thread."""
        bridge = _CallbackBridge(on_success, on_error, self._discard_bridge)
        with self._token_lock:
            token_snapshot = self.token

        def invoke_with_session():
            # Bind the session token at dispatch time. A later logout/login must not
            # change the credentials of an already queued request.
            self._request_context.token = token_snapshot
            try:
                return function(*args, **kwargs)
            finally:
                try:
                    del self._request_context.token
                except AttributeError:
                    pass

        worker = Worker(invoke_with_session)
        worker.signals.succeeded.connect(bridge.succeeded)
        worker.signals.failed.connect(bridge.failed)
        worker.signals.finished.connect(bridge.finished)
        with self._active_lock:
            self._active.add((worker, bridge))
        self._pool.start(worker)
        return worker

    def _discard_bridge(self, bridge):
        with self._active_lock:
            self._active = {(worker, item) for worker, item in self._active if item is not bridge}
        bridge.deleteLater()

    def _request(self, operation, token_override=None, **payload):
        headers = {"Content-Type": "application/json"}
        if token_override is not None:
            token = token_override
        elif hasattr(self._request_context, "token"):
            token = self._request_context.token
        else:
            with self._token_lock:
                token = self.token
        if token:
            headers["Authorization"] = "Bearer " + token

        attempts = 2 if operation in READ_OPERATIONS else 1
        last_error = None
        for attempt in range(attempts):
            try:
                response = self._http.post(f"/api/{operation}", json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                try:
                    detail = exc.response.json().get("detail", "Request failed")
                except (ValueError, AttributeError):
                    detail = "Request failed"
                if isinstance(detail, dict):
                    detail = detail.get("message", detail)
                if exc.response.status_code == 404 and str(detail).lower().startswith("unknown api operation"):
                    detail = (
                        f"The REST API server does not recognize operation '{operation}'.\n\n"
                        "The desktop app and API server are running different source versions. "
                        "Update the SERVER folder from the same project ZIP, stop the old API "
                        "process (Ctrl+C), then restart it from the project root with:\n\n"
                        "python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 30"
                    )
                raise RuntimeError(str(detail)) from exc
            except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError, httpx.PoolTimeout) as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    break
                # httpx drops the failed socket and opens a fresh connection on retry;
                # keep the shared pool alive for other in-flight requests.
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                raise RuntimeError(f"Cannot connect to REST API at {self.base_url}: {exc}") from exc
            except ValueError as exc:
                raise RuntimeError("The REST API returned an invalid JSON response.") from exc
        raise RuntimeError(f"Cannot connect to REST API at {self.base_url}: {last_error}") from last_error

    def health(self):
        try:
            response = self._http.get("/health", timeout=7.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Cannot connect to REST API at {self.base_url}.") from exc

    def login(self, phone, password):
        result = self._request("login", phone=phone, password=password)
        with self._token_lock:
            self.token = result["access_token"]
        return result["user"]

    def register(self, name, password, email, phone, currency):
        return self._request("register", name=name, password=password, email=email, phone=phone, currency=currency)["user_id"]

    def logout(self, user_id, token_snapshot=None):
        with self._token_lock:
            token_used = token_snapshot if token_snapshot is not None else self.token
        try:
            return self._request("logout", token_override=token_used)
        finally:
            with self._token_lock:
                if self.token == token_used:
                    self.token = None

    def profile(self, user_id): return self._request("profile")
    def update_profile(self, user_id, name, email, phone): return self._request("update_profile", name=name, email=email, phone=phone)
    def change_password(self, user_id, old_password, new_password): return self._request("change_password", old_password=old_password, new_password=new_password)
    def wallets(self, user_id): return self._request("wallets")
    def create_wallet(self, user_id, currency): return self._request("create_wallet", currency=currency)
    def set_wallet_locked(self, user_id, wallet_id, locked): return self._request("set_wallet_locked", wallet_id=wallet_id, locked=locked)
    def deposit(self, user_id, wallet_id, amount): return self._request("deposit", wallet_id=wallet_id, amount=amount)
    def withdraw(self, user_id, wallet_id, amount): return self._request("withdraw", wallet_id=wallet_id, amount=amount)
    def transfer(self, user_id, sender_id, receiver_id, amount): return self._request("transfer", sender_id=sender_id, receiver_id=receiver_id, amount=amount)
    def history(self, user_id, tx_type=None, status=None, limit=100): return self._request("history", tx_type=tx_type, status=status, limit=limit)
    def transaction_detail(self, user_id, transaction_id): return self._request("transaction_detail", transaction_id=transaction_id)
    def activity(self, user_id, action=None, limit=100): return self._request("activity", action=action, limit=limit)
    def admin_users(self, user_id): return self._request("admin_users")
    def admin_wallets(self, user_id, owner_id=None): return self._request("admin_wallets", user_id=owner_id)
    def admin_set_wallet_locked(self, admin_id, wallet_id, locked): return self._request("admin_set_wallet_locked", wallet_id=wallet_id, locked=locked)
    def admin_transactions(self, user_id, tx_type=None, status=None): return self._request("admin_transactions", tx_type=tx_type, status=status)
    def admin_transaction_detail(self, user_id, transaction_id): return self._request("admin_transaction_detail", transaction_id=transaction_id)
    def admin_audit_logs(self, user_id, action=None, target_user_id=None): return self._request("admin_audit_logs", action=action, user_id=target_user_id)
    def user_profile(self, user_id): return self._request("user_profile")
    def save_user_profile(self, user_id, date_of_birth, sex, address, job, country): return self._request("save_user_profile", date_of_birth=date_of_birth, sex=sex, address=address, job=job, country=country)
    def banks(self): return self._request("banks")
    def bank_accounts(self, user_id): return self._request("bank_accounts")
    def link_bank(self, user_id, wallet_id, bank_id, account_number): return self._request("link_bank", wallet_id=wallet_id, bank_id=bank_id, account_number=account_number)
    def unlink_bank(self, user_id, bank_account_id): return self._request("unlink_bank", bank_account_id=bank_account_id)
    def statistics(self, user_id, date_from=None, date_to=None): return self._request("statistics", date_from=date_from, date_to=date_to)
    def admin_user_profile(self, user_id, target_user_id): return self._request("admin_user_profile", user_id=target_user_id)
    def admin_user_profiles(self, user_id, page=1, page_size=20, search=None, sex=None, country=None, sort_by="created_at", sort_order="DESC"):
        return self._request("admin_user_profiles", page=page, page_size=page_size, search=search, sex=sex, country=country, sort_by=sort_by, sort_order=sort_order)
    def admin_bank_accounts(self, user_id): return self._request("admin_bank_accounts")
    def admin_partner_banks(self, user_id): return self._request("admin_partner_banks")
    def admin_create_partner_bank(self, user_id, name): return self._request("admin_create_partner_bank", name=name)
    def admin_set_partner_bank_valid(self, user_id, bank_id, is_valid): return self._request("admin_set_partner_bank_valid", bank_id=bank_id, is_valid=is_valid)
    def admin_bank_statistics(self, user_id): return self._request("admin_bank_statistics")
    def admin_system_statistics(self, user_id): return self._request("admin_system_statistics")
    def dashboard_summary(self, user_id): return self._request("dashboard_summary")
    def bank_page_data(self, user_id): return self._request("bank_page_data")
