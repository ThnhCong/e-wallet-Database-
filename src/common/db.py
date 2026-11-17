from contextlib import contextmanager
from pymysql.err import MySQLError
from src.common.errors import ServiceError, translate_db_error

class BaseRepository:
    """Repository giữ connection và thực thi stored procedure."""
    def __init__(self, db_connection): self.conn = db_connection

    @contextmanager
    def cursor(self):
        cur = self.conn.cursor()
        try: yield cur
        finally: cur.close()

    def call(self, procedure, params=()):
        """Call a stored procedure and return its first result set as dictionaries."""
        try:
            with self.cursor() as cur:
                cur.callproc(procedure, tuple(params))
                rows = cur.fetchall() if cur.description else []
                # Drain remaining result sets before returning the pooled connection.
                while cur.nextset(): pass
                return list(rows or [])
        except MySQLError as exc:
            raise translate_db_error(exc, procedure) from exc

@contextmanager
def db_transaction(conn, operation="Operation"):
    try:
        yield
        conn.commit()
    except ServiceError:
        conn.rollback(); raise
    except MySQLError as exc:
        conn.rollback(); raise translate_db_error(exc, operation) from exc
    except Exception:
        conn.rollback(); raise
