"""HTTP client for the REST API. The desktop app does not access DB/services directly."""
import json
import os
import urllib.error
import urllib.request

class Api:
    def __init__(self):
        self.base_url = os.getenv("EWALLET_API_URL", "http://127.0.0.1:8000").rstrip("/")
        self.token = None

    def _request(self, operation, **payload):
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.token: headers["Authorization"] = "Bearer " + self.token
        request = urllib.request.Request(f"{self.base_url}/api/{operation}", data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try: detail = json.loads(exc.read().decode("utf-8")).get("detail", "Request failed")
            except Exception: detail = "Request failed"
            if isinstance(detail, dict): detail = detail.get("message", detail)
            # A 404 with this message almost always means the desktop client was
            # updated but the REST API process is still running older source.
            if exc.code == 404 and str(detail).lower().startswith("unknown api operation"):
                detail = (
                    f"The REST API server does not recognize operation '{operation}'.\n\n"
                    "Your desktop app and API server are running different source versions. "
                    "Update the SERVER folder from this same project ZIP, stop the old API "
                    "process (Ctrl+C), then restart it from the project root with:\n\n"
                    "python -m uvicorn src.api:app --host 0.0.0.0 --port 8000\n\n"
                    "Then sign out and sign in again. Updating only the GUI is not sufficient."
                )
            raise RuntimeError(str(detail)) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Cannot connect to REST API at {self.base_url}. Start the API server first.") from exc
        return result

    def health(self):
        """Return server build metadata without requiring authentication."""
        request = urllib.request.Request(f"{self.base_url}/health", method="GET")
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Cannot connect to REST API at {self.base_url}.") from exc

    def login(self, phone, password):
        result = self._request("login", phone=phone, password=password)
        self.token = result["access_token"]
        return result["user"]
    def register(self, name, password, email, phone, currency): return self._request("register", name=name, password=password, email=email, phone=phone, currency=currency)["user_id"]
    def logout(self, user_id):
        try: return self._request("logout")
        finally: self.token = None
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
    def save_user_profile(self, user_id, age, sex, address, job, country): return self._request("save_user_profile", age=age, sex=sex, address=address, job=job, country=country)
    def banks(self): return self._request("banks")
    def bank_accounts(self, user_id): return self._request("bank_accounts")
    def link_bank(self, user_id, wallet_id, bank_id): return self._request("link_bank", wallet_id=wallet_id, bank_id=bank_id)
    def statistics(self, user_id, date_from=None, date_to=None): return self._request("statistics", date_from=date_from, date_to=date_to)
    def admin_user_profile(self, user_id, target_user_id): return self._request("admin_user_profile", user_id=target_user_id)
    def admin_user_profiles(self, user_id, page=1, page_size=20, search=None, sex=None, country=None,
                            sort_by="created_at", sort_order="DESC"):
        return self._request("admin_user_profiles", page=page, page_size=page_size, search=search,
                             sex=sex, country=country, sort_by=sort_by, sort_order=sort_order)
    def admin_bank_accounts(self, user_id): return self._request("admin_bank_accounts")
    def admin_partner_banks(self, user_id): return self._request("admin_partner_banks")
    def admin_create_partner_bank(self, user_id, name): return self._request("admin_create_partner_bank", name=name)
    def admin_delete_partner_bank(self, user_id, bank_id): return self._request("admin_delete_partner_bank", bank_id=bank_id)
    def admin_bank_statistics(self, user_id): return self._request("admin_bank_statistics")
    def admin_system_statistics(self, user_id): return self._request("admin_system_statistics")
