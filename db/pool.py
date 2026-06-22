import pymysql
from queue import LifoQueue
import logging
import settings

logger = logging.getLogger(__name__)

class ConnectionPool:
    def __init__(self, maxsize=8):
        self._maxsize = maxsize
        self._pool = LifoQueue(maxsize)
        for _ in range(maxsize):
            self._pool.put(self._create_conn())

    def _create_conn(self):
        return pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )

    def get(self):
        return self._pool.get()

    def put(self, conn):
        try:
            conn.ping(reconnect=True)
            self._pool.put(conn)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            self._pool.put(self._create_conn())

    def close_all(self):
        while not self._pool.empty():
            try:
                self._pool.get_nowait().close()
            except Exception:
                pass

pool = ConnectionPool(maxsize=8)

def query(sql, params=None):
    conn = pool.get()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            if sql.strip().upper().startswith("SELECT"):
                return cur.fetchall()
            conn.commit()
            return cur.lastrowid
    finally:
        pool.put(conn)

def query_one(sql, params=None):
    rows = query(sql, params)
    return rows[0] if rows else None
