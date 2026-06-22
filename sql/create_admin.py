"""
创建默认管理员账号
用法: python sql/create_admin.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pymysql
import settings
from services.auth_service import hash_password

conn = pymysql.connect(host=settings.DB_HOST, port=settings.DB_PORT,
    user=settings.DB_USER, password=settings.DB_PASSWORD,
    database=settings.DB_NAME, charset="utf8mb4")
cur = conn.cursor()

username = "admin"
password = "262626"
real_name = "系统管理员"

hashed = hash_password(password)

try:
    cur.execute("SELECT id FROM users WHERE username=%s", (username,))
    existing = cur.fetchone()
    if existing:
        print(f"管理员账号 '{username}' 已存在 (id={existing[0]})")
    else:
        cur.execute("INSERT INTO users (username, password_hash, real_name, is_admin, permissions) VALUES (%s,%s,%s,1,'{}')",
                    (username, hashed, real_name))
        conn.commit()
        print(f"管理员账号创建成功!")
        print(f"  用户名: {username}")
        print(f"  密码: {password}")
        print(f"  姓名: {real_name}")
except Exception as e:
    print(f"错误: {e}")
finally:
    cur.close()
    conn.close()
