# src/modules/audit_logs/audit_actions.py
"""13 hanh dong audit (Bang 1 trong bao cao) va quy tac tham chieu cua tung hanh dong."""


class AuditAction:
    REGISTER = "REGISTER"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CHANGE_PASSWORD = "CHANGE_PASSWORD"
    UPDATE_PROFILE = "UPDATE_PROFILE"
    CREATE_WALLET = "CREATE_WALLET"
    LOCK_WALLET = "LOCK_WALLET"
    UNLOCK_WALLET = "UNLOCK_WALLET"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    TRANSFER = "TRANSFER"
    TRANSFER_RECEIVED = "TRANSFER_RECEIVED"
    LINK_BANK = "LINK_BANK"


# action -> (co wallet_id?, co transaction_id?)   True = phai co, False = phai NULL
AUDIT_REFERENCES = {
    AuditAction.REGISTER:          (False, False),
    AuditAction.LOGIN:             (False, False),
    AuditAction.LOGOUT:            (False, False),
    AuditAction.CHANGE_PASSWORD:   (False, False),
    AuditAction.UPDATE_PROFILE:    (False, False),
    AuditAction.CREATE_WALLET:     (True, False),
    AuditAction.LOCK_WALLET:       (True, False),
    AuditAction.UNLOCK_WALLET:     (True, False),
    AuditAction.DEPOSIT:           (True, True),
    AuditAction.WITHDRAW:          (True, True),
    AuditAction.TRANSFER:          (True, True),
    AuditAction.TRANSFER_RECEIVED: (True, True),
    AuditAction.LINK_BANK:         (True, False),
}

AUDIT_ACTIONS = tuple(AUDIT_REFERENCES)