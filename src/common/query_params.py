# src/common/query_params.py
"""Chuan hoa cac tham so chung cua truy van danh sach (limit, id loc tuy chon)."""
from src.common.errors import ServiceError
from src.common.validators import parse_id

DEFAULT_LIMIT = 20          # so dong mac dinh cho nguoi dung
DEFAULT_ADMIN_LIMIT = 50    # so dong mac dinh cho man hinh quan tri
MAX_LIMIT = 200


def normalize_limit(limit, default=DEFAULT_LIMIT, maximum=MAX_LIMIT):
    """Rong -> default; phai la so nguyen >= 1; bi chan tren boi `maximum`."""
    if limit is None or str(limit).strip() == "":
        return default
    try:
        value = int(str(limit).strip())
    except ValueError:
        raise ServiceError("INVALID_LIMIT", "The limit must be a whole number.") from None
    if value < 1:
        raise ServiceError("INVALID_LIMIT", "The limit must be at least 1.")
    return min(value, maximum)


def parse_optional_id(value, label):
    """Bo loc id tuy chon: rong -> None, nguoc lai dung parse_id."""
    if value is None or str(value).strip() == "":
        return None
    return parse_id(value, label)