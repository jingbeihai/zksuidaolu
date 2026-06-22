"""运行迁移脚本"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymysql
import settings

conn = pymysql.connect(
    host=settings.DB_HOST, port=settings.DB_PORT,
    user=settings.DB_USER, password=settings.DB_PASSWORD,
    database=settings.DB_NAME, charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor, autocommit=True
)
cur = conn.cursor()

with open(os.path.join(os.path.dirname(__file__), "migrate_001_add_current_furnace_id.sql"), "r", encoding="utf-8") as f:
    sql = f.read()

for stmt in sql.split(";"):
    stmt = stmt.strip()
    if stmt:
        try:
            cur.execute(stmt)
            print(f"OK: {stmt[:60]}...")
        except Exception as e:
            print(f"SKIP ({e}): {stmt[:60]}...")

cur.close()
conn.close()
print("迁移完成")
