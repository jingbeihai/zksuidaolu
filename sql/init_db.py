"""
数据库初始化执行脚本 - 修复版
先清理注释行，再按分号分割执行
用法: python sql/init_db.py
"""
import sys, os, pymysql, re
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import settings

def clean_sql(sql):
    """移除 SQL 中的单行注释（--）"""
    lines = sql.split("\n")
    cleaned = []
    for line in lines:
        # 跳过纯注释行
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        # 去除行尾注释（保留行内注释后的 SQL）
        cleaned.append(line)
    return "\n".join(cleaned)

def run():
    conn = pymysql.connect(host=settings.DB_HOST, port=settings.DB_PORT,
        user=settings.DB_USER, password=settings.DB_PASSWORD,
        database=settings.DB_NAME, charset="utf8mb4")
    cur = conn.cursor()

    # 检查已有表
    cur.execute("SHOW TABLES")
    existing = [r[0] for r in cur.fetchall()]
    if existing:
        print(f"发现已有表: {existing}")
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for t in existing:
            cur.execute(f"DROP TABLE IF EXISTS `{t}`")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
        print("已删除所有旧表")

    # 读取并清理 SQL
    script_dir = os.path.dirname(__file__)
    with open(os.path.join(script_dir, "init_database.sql"), "r", encoding="utf-8") as f:
        sql_content = f.read()

    sql_content = clean_sql(sql_content)

    # 按分号分割
    stmts = [s.strip() for s in sql_content.split(";") if s.strip()]

    success = 0
    errors = []
    for stmt in stmts:
        stmt_sql = stmt + ";"
        preview = stmt[:60].replace("\n", " ").replace("\r", "")
        try:
            cur.execute(stmt_sql)
            conn.commit()
            success += 1
            print(f"  [OK] {preview}...")
        except Exception as e:
            err = str(e)[:100]
            if "Duplicate" in err or "already exists" in err:
                success += 1
            else:
                errors.append(f"  [ERROR] {preview}: {err}")
                print(f"  [ERROR] {preview}: {err}")

    cur.close()
    conn.close()

    print(f"\n{'='*40}")
    print(f"结果: 成功 {success}, 失败 {len(errors)}")
    for e in errors:
        print(e)
    return len(errors) == 0

if __name__ == "__main__":
    print(f"正在初始化数据库 {settings.DB_NAME} ...")
    ok = run()
    if ok:
        print("数据库初始化完成!")
    else:
        print("有错误发生，请检查。")
