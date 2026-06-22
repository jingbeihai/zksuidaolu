"""
数据库初始化 - 修复版
逐个语句执行并检查结果
"""
import sys, os, pymysql, re
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import settings

conn = pymysql.connect(host=settings.DB_HOST, port=settings.DB_PORT,
    user=settings.DB_USER, password=settings.DB_PASSWORD, database=settings.DB_NAME,
    charset="utf8mb4")
cur = conn.cursor()

# 检查默认引擎
cur.execute("SELECT @@default_storage_engine")
row = cur.fetchone()
print(f"默认引擎: {row[0]}")

# 检查已有表
cur.execute("SHOW TABLES")
existing = [r[0] for r in cur.fetchall()]
print(f"\n已有表: {existing if existing else '无'}")

# 删除所有表
cur.execute("SET FOREIGN_KEY_CHECKS = 0")
for t in existing:
    cur.execute(f"DROP TABLE IF EXISTS `{t}`")
    print(f"  已删除: {t}")
cur.execute("SET FOREIGN_KEY_CHECKS = 1")
conn.commit()

# 读取SQL文件
with open(os.path.join(os.path.dirname(__file__), "init_database.sql"), "r", encoding="utf-8") as f:
    sql_content = f.read()

# 按分号拆分语句
stmts = [s.strip() for s in sql_content.split(";") if s.strip() and not s.strip().startswith("--")]

success = 0
errors = []
for i, stmt in enumerate(stmts):
    stmt = stmt + ";"
    preview = stmt[:60].replace('\n', ' ')
    try:
        cur.execute(stmt)
        conn.commit()
        success += 1
        print(f"  [OK] ({i+1}) {preview}...")
    except Exception as e:
        err_msg = str(e)[:100]
        if "Duplicate" in err_msg or "already exists" in err_msg:
            success += 1
            print(f"  [OK] ({i+1}) {preview}... (已存在)")
        else:
            errors.append(f"({i+1}) {preview}: {err_msg}")
            print(f"  [ERROR] ({i+1}) {err_msg}")

cur.close()
conn.close()

print(f"\n{'='*50}")
print(f"结果: 成功 {success}, 失败 {len(errors)}")
if errors:
    print(f"\n{len(errors)} 个错误:")
    for e in errors:
        print(f"  {e}")
