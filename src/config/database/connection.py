"""MySQL connection pool; all connection details come from the central config."""
from functools import lru_cache
from dbutils.pooled_db import PooledDB
import pymysql
from src.config.settings import get_settings

@lru_cache(maxsize=1)
def _pool():
    cfg = get_settings()["database"]
    pool_cfg = cfg.get("pool", {})
    return PooledDB(
        creator=pymysql,
        maxconnections=int(pool_cfg.get("max_connections", 10)),
        mincached=int(pool_cfg.get("min_cached", 2)),
        maxcached=int(pool_cfg.get("max_cached", 5)),
        blocking=True,
        host=cfg["host"], port=int(cfg.get("port", 3306)),
        user=cfg["user"], password=cfg["password"], database=cfg.get("name", "ewallet"),
        autocommit=False, setsession=["SET AUTOCOMMIT = 0"],
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4",
    )

def get_db_connection():
    return _pool().connection()
