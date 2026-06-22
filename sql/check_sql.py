"""检查 SQL 文件的分句情况"""
with open("sql/init_database.sql", "r", encoding="utf-8") as f:
    content = f.read()

stmts = [s.strip() for s in content.split(";") if s.strip()]
for i, s in enumerate(stmts):
    first_line = s.split("\n")[0].strip()[:80]
    print(f"{i}: {first_line}")
print(f"\n总共 {len(stmts)} 条语句")
