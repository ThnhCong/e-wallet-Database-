# src/config/database.py
from dbutils.pooled_db import PooledDB
import pymysql

pool = PooledDB(
    creator=pymysql,
    maxconnections=10,
    mincached=2,
    maxcached=5,
    blocking=True,
    host="localhost",
    user="Cong",  # Thay 'root' thành user 'clients' vừa tạo
    password="141106",  # Thay bằng mật khẩu bạn đã thiết lập cho user 'clients'
    database="ewallet",
    port=3306,
    autocommit=False,
    setsession=["SET AUTOCOMMIT = 0"],  # Ép Session MySQL tắt Autocommit tuyệt đối
    cursorclass=pymysql.cursors.DictCursor,
)


def get_db_connection():
    return pool.connection()