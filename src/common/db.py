# src/common/db.py
from contextlib import contextmanager

from pymysql.err import MySQLError

from src.common.errors import ServiceError, translate_db_error


class BaseRepository:
    """Repository chi giu connection va mo cursor; moi cau SQL nam trong repository."""

    def __init__(self, db_connection):
        self.conn = db_connection

    @contextmanager
    def cursor(self):
        cur = self.conn.cursor()
        try:
            yield cur
        finally:
            cur.close()


@contextmanager
def db_transaction(conn, operation="Operation"):
    """with db_transaction(conn, "Deposit"): ...   commit khi xong; rollback + doi loi MySQL thanh ServiceError."""
    try:
        yield
        conn.commit()
    except ServiceError:
        conn.rollback()
        raise
    except MySQLError as exc:
        conn.rollback()
        raise translate_db_error(exc, operation) from exc
    except Exception:
        conn.rollback()
        raise