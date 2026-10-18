# src/modules/audit_logs/audit_controller.py
class AuditController:

    def __init__(self, audit_service):
        self.audit_service = audit_service

    def get_activity(self, user_id, action=None, limit=20):
        return self.audit_service.get_user_activity(user_id, action, limit)

    def list_logs(self, user_id=None, action=None, limit=50):
        return self.audit_service.list_logs(user_id, action, limit)