# src/common/errors.py
"""ServiceError KE THUA ValueError nen `except ValueError` trong main van bat duoc."""
import logging

log = logging.getLogger(__name__)


class ServiceError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


_RULES = [  # (doan thong bao cua trigger, viet thuong) -> (code, thong bao)   {op} = ten thao tac   (Table 3)
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


def translate_db_error(exc, operation="Operation"):
    """Loi MySQL (pymysql) -> ServiceError than thien."""
    errno = exc.args[0] if exc.args else None
    text = str(exc.args[1]) if len(exc.args) > 1 else str(exc)
    low = text.lower()
    for fragment, code, msg in _RULES:
        if fragment in low:
            return ServiceError(code, msg.format(op=operation))
    if errno == 1062:
        if "phone" in low:
            return ServiceError("DUPLICATE_PHONE", "This phone number is already registered.")
        if "email" in low:
            return ServiceError("DUPLICATE_EMAIL", "This email is already registered.")
        return ServiceError("DUPLICATE", "The value already exists.")
    if errno == 1452:
        return ServiceError("WALLET_NOT_FOUND", "The wallet does not exist.")
    if errno == 3819:
        return ServiceError("CONSTRAINT", "The data violates a database rule.")
    if errno in (1213, 1205):
        return ServiceError("BUSY", "The system is busy, please try again.")
    log.error("Unexpected database error: %r", exc)
    return ServiceError("DB_ERROR", "A system error occurred. Please try again later.")