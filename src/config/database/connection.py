# src/config/database.py
import pymysql
from dbutils.pooled_db import PooledDB

# 1. Khởi tạo Connection Pool tập trung với PyMySQL
pool = PooledDB(
    creator=pymysql,       # Sử dụng driver PyMySQL
    maxconnections=10,     # Số lượng kết nối tối đa trong pool
    mincached=2,           # Số lượng kết nối nhàn rỗi tối thiểu duy trì sẵn
    maxcached=5,           # Số lượng kết nối nhàn rỗi tối đa duy trì
    blocking=True,         # Đợi kết nối rảnh nếu pool chạm ngưỡng maxconnections
    host="localhost",
    user="root",           # Thay bằng user MySQL của bạn
    password="Tindao514160#", # Thay bằng password MySQL của bạn
    database="ewallet",
    port=3306,
    autocommit=False,      # Để quản lý Transaction thủ công (commit/rollback)
    cursorclass=pymysql.cursors.DictCursor
)

def get_db_connection():
    """
    Rút 1 kết nối từ Connection Pool ra để sử dụng.
    Khi gọi conn.close(), kết nối sẽ KHÔNG bị đóng hẳn mà trả về lại Pool.
    """
    return pool.connection()