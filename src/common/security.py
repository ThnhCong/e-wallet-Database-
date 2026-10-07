# src/common/security.py
"""PBKDF2-HMAC-SHA256 co salt. Van dang nhap duoc voi hash SHA-256 cu (64 hex) cua cac user da dang ky
bang code cu, va tu nang cap len PBKDF2 o lan dang nhap dau tien."""
import hashlib
import hmac
import os

_PREFIX = "pbkdf2_sha256"
_ITER = 200_000


def hash_password(password):
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITER)
    return f"{_PREFIX}${_ITER}${salt.hex()}${dk.hex()}"


def verify_password(password, stored):
    if stored.startswith(_PREFIX + "$"):
        _, it, salt, h = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(it))
        return hmac.compare_digest(dk.hex(), h)
    if len(stored) == 64:
        return hmac.compare_digest(hashlib.sha256(password.encode("utf-8")).hexdigest(), stored.lower())
    return False


def needs_rehash(stored):
    return not stored.startswith(_PREFIX + "$")