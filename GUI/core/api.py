from contextlib import contextmanager

from src.config.database.connection import get_db_connection
from src.container import build_controllers
from src.modules.admin.admin_controller import AdminController
from src.modules.admin.admin_repository import AdminRepository
from src.modules.admin.admin_service import AdminService


class Api:
    """Bridge the GUI to application controllers; SQL stays in repositories."""

    @contextmanager
    def _controllers(self):
        conn = get_db_connection()
        try:
            controllers = build_controllers(conn)
            audit_service = controllers.audit.audit_service
            admin_service = AdminService(
                AdminRepository(conn),
                controllers.wallets.wallet_service.wallet_repo,
                controllers.transactions.transaction_service.tx_repo,
                controllers.audit.audit_service.audit_repo,
                audit_service,
            )
            yield controllers, AdminController(admin_service)
        finally:
            conn.close()

    def _call(self, callback):
        with self._controllers() as (controllers, admin):
            return callback(controllers, admin)

    def login(self, phone, password):
        return self._call(lambda c, a: c.users.login(phone, password))

    def register(self, name, password, email, phone, currency):
        return self._call(lambda c, a: c.users.register(name, password, email, phone, currency))

    def logout(self, user_id):
        return self._call(lambda c, a: c.users.logout(user_id))

    def profile(self, user_id):
        return self._call(lambda c, a: c.users.get_user_by_id(user_id))

    def update_profile(self, user_id, name, email, phone):
        return self._call(lambda c, a: c.users.update_profile(user_id, name, email, phone))

    def change_password(self, user_id, old_password, new_password):
        return self._call(lambda c, a: c.users.change_password(user_id, old_password, new_password))

    def wallets(self, user_id):
        return self._call(lambda c, a: c.wallets.list_wallets(user_id))

    def create_wallet(self, user_id, currency):
        return self._call(lambda c, a: c.wallets.create_wallet(user_id, currency))

    def set_wallet_locked(self, user_id, wallet_id, locked):
        method = lambda c, a: c.wallets.lock_wallet(user_id, wallet_id) if locked else c.wallets.unlock_wallet(user_id, wallet_id)
        return self._call(method)

    def deposit(self, user_id, wallet_id, amount):
        return self._call(lambda c, a: c.transactions.deposit(user_id, wallet_id, amount))

    def withdraw(self, user_id, wallet_id, amount):
        return self._call(lambda c, a: c.transactions.withdraw(user_id, wallet_id, amount))

    def transfer(self, user_id, sender_id, receiver_id, amount):
        return self._call(lambda c, a: c.transactions.transfer(user_id, sender_id, receiver_id, amount))

    def history(self, user_id, tx_type=None, status=None, limit=100):
        return self._call(lambda c, a: c.transactions.history(user_id, tx_type, status, limit))

    def transaction_detail(self, user_id, transaction_id):
        return self._call(lambda c, a: c.transactions.transaction_detail(user_id, transaction_id))

    def activity(self, user_id, action=None, limit=100):
        return self._call(lambda c, a: c.audit.get_activity(user_id, action, limit))

    def admin_users(self, user_id):
        return self._call(lambda c, a: a.list_users(user_id))

    def admin_wallets(self, user_id):
        return self._call(lambda c, a: a.list_wallets(user_id))

    def admin_set_wallet_locked(self, admin_id, wallet_id, locked):
        method = lambda c, a: a.lock_wallet(admin_id, wallet_id) if locked else a.unlock_wallet(admin_id, wallet_id)
        return self._call(method)

    def admin_transactions(self, user_id, tx_type=None, status=None):
        return self._call(lambda c, a: a.list_transactions(user_id, tx_type, status))

    def admin_audit_logs(self, user_id, action=None):
        return self._call(lambda c, a: a.list_audit_logs(user_id, action=action))
