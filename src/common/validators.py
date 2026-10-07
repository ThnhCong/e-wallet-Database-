# src/common/validators.py
"""Chi kiem tra DINH DANG dau vao; luat nghiep vu (so du, han muc, vi bi khoa...) do trigger lo."""
import re
from decimal import Decimal, InvalidOperation

from src.common.errors import ServiceError

MAX_AMOUNT = Decimal("9999999999999.99")  # DECIMAL(15,2)
CURRENCIES = ("VND", "USD")
TX_TYPES = ("DEPOSIT", "WITHDRAW", "TRANSFER")
TX_STATUSES = ("PENDING", "SUCCESS", "FAIL")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE = re.compile(r"^\d{8,15}$")


def require_text(value, label, max_len):
    v = (value or "").strip()
    if not v:
        raise ServiceError("REQUIRED", f"{label} is required.")
    if len(v) > max_len:
        raise ServiceError("TOO_LONG", f"{label} must be at most {max_len} characters.")
    return v


def validate_email(value):
    v = require_text(value, "Email", 255).lower()
    if not _EMAIL.match(v):
        raise ServiceError("EMAIL_INVALID", "The email format is invalid (example: name@example.com).")
    return v


def validate_phone(value):
    v = require_text(value, "Phone", 20)
    if not _PHONE.match(v):
        raise ServiceError("PHONE_INVALID", "The phone number must have 8-15 digits.")
    return v


def validate_password(value):
    if value is None or len(value) < 6:
        raise ServiceError("PASSWORD_WEAK", "The password must have at least 6 characters.")
    return value


def parse_currency(value):
    v = (value or "").strip().upper()
    if v not in CURRENCIES:
        raise ServiceError("CURRENCY_UNSUPPORTED", "Only VND and USD wallets are supported.")
    return v


def parse_amount(value):
    try:
        amount = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        raise ServiceError("AMOUNT_INVALID", "The amount must be a number.")
    if not amount.is_finite() or amount <= 0:
        raise ServiceError("AMOUNT_INVALID", "The amount must be greater than 0.")
    if amount > MAX_AMOUNT:
        raise ServiceError("AMOUNT_INVALID", "The amount is too large.")
    if amount != amount.quantize(Decimal("0.01")):
        raise ServiceError("AMOUNT_INVALID", "The amount can have at most 2 decimal places.")
    return amount


def parse_id(value, label="Wallet"):
    try:
        i = int(str(value).strip())
    except (TypeError, ValueError):
        raise ServiceError("ID_INVALID", f"{label} ID must be a positive integer.")
    if i <= 0:
        raise ServiceError("ID_INVALID", f"{label} ID must be a positive integer.")
    return i


def parse_choice(value, allowed, label):
    if value is None or str(value).strip() == "":
        return None
    v = str(value).strip().upper()
    if v not in allowed:
        raise ServiceError("FILTER_INVALID", f"{label} must be one of: {', '.join(allowed)}.")
    return v