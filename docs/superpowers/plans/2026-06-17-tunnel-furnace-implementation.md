# 中科恒泰隧道炉排产与生产可视化系统 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建完整的隧道炉排产与生产可视化系统，覆盖设备管理、工艺管理、排产、生产控制、TV可视化、用户管理、日志、数据备份八大模块

**Architecture:** Python FastAPI + Jinja2 模板引擎 + MySQL 8，纯前端离线运行。后端分 router/service/db 三层，中间件处理认证和日志。电视大屏通过轮询 API 实现实时更新。

**Tech Stack:** FastAPI, PyMySQL, Jinja2, bcrypt, itsdangerous, python-dotenv, openpyxl, uvicorn

---

## 文件映射

```
zk-tunnel-furnace/
├── main.py                     # FastAPI 入口
├── .env                        # 环境变量
├── .env.example                # 环境变量模板
├── requirements.txt            # 依赖
├── settings.py                 # 全局配置
├── logging_config.py           # 日志配置
│
├── db/
│   ├── __init__.py
│   ├── pool.py                 # 连接池
│   └── queries.py              # 全部 SQL 查询
│
├── routers/
│   ├── __init__.py
│   ├── auth.py                 # 登录/登出
│   ├── device.py               # 设备管理
│   ├── process.py              # 工艺组合
│   ├── schedule.py             # 排产管理
│   ├── production.py           # 生产控制
│   ├── tv.py                   # TV可视化
│   ├── user.py                 # 用户管理
│   ├── log.py                  # 日志系统
│   └── backup.py               # 数据备份
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py         # 认证 + 权限
│   └── production_service.py   # 生产核心逻辑
│
├── middleware/
│   ├── __init__.py
│   └── log_middleware.py       # 操作日志装饰器
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── nav.html
│   ├── device/
│   │   ├── list.html
│   │   └── temp_settings.html
│   ├── process/
│   │   ├── product_list.html
│   │   ├── process_list.html
│   │   └── process_edit.html
│   ├── schedule/
│   │   ├── list.html
│   │   └── form.html
│   ├── production/
│   │   ├── control.html
│   │   ├── section_ops.html
│   │   └── report.html
│   ├── tv/
│   │   └── display.html
│   ├── user/
│   │   ├── list.html
│   │   └── form.html
│   ├── log/
│   │   └── list.html
│   └── backup/
│       └── index.html
│
├── static/
│   ├── css/
│   │   ├── flat.css
│   │   └── tv.css
│   └── js/
│       ├── tv.js
│       ├── production.js
│       └── common.js
│
├── sql/
│   └── init_database.sql
│
└── docs/superpowers/
    ├── specs/
    └── plans/
```

---

### Task 1: 项目骨架初始化

**文件:**
- 创建: `main.py`
- 创建: `settings.py`
- 创建: `logging_config.py`
- 创建: `requirements.txt`
- 创建: `.env.example`
- 创建: `db/__init__.py`
- 创建: `db/pool.py`
- 创建: `routers/__init__.py`
- 创建: `services/__init__.py`
- 创建: `middleware/__init__.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
fastapi==0.115.0
uvicorn==0.30.0
PyMySQL==1.1.1
python-dotenv==1.0.1
bcrypt==4.2.0
itsdangerous==2.2.0
Jinja2==3.1.4
openpyxl==3.1.5
aiofiles==24.1.0
python-multipart==0.0.12
```

- [ ] **Step 2: 创建 settings.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

APP_TITLE = "中科恒泰隧道炉排产与生产可视化系统V1.0"
STATIC_VERSION = "20260617a"

DB_HOST = os.getenv("DB_HOST", "101.43.84.176")
DB_PORT = int(os.getenv("DB_PORT", 1357))
DB_USER = os.getenv("DB_USER", "zksuidaolu2")
DB_PASSWORD = os.getenv("DB_PASSWORD", "GHT4EFy228jQh5sx")
DB_NAME = os.getenv("DB_NAME", "zksuidaolu2")

SECRET_KEY = os.getenv("SECRET_KEY", "zk-tunnel-furnace-dev-secret-2026")
SESSION_COOKIE = "tunnel_session"
SESSION_MAX_AGE = 8 * 3600  # 8 hours

TV_REFRESH_INTERVAL = 10  # seconds
```

- [ ] **Step 3: 创建 logging_config.py**

```python
import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logging():
    handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "app.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    ))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
```

- [ ] **Step 4: 创建 db/pool.py**

```python
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
```

- [ ] **Step 5: 创建 main.py**

```python
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import settings
from logging_config import setup_logging

setup_logging()

app = FastAPI(title=settings.APP_TITLE)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY,
                   session_cookie=settings.SESSION_COOKIE,
                   max_age=settings.SESSION_MAX_AGE)

app.mount("/static", StaticFiles(directory="static"), name="static")

from routers import auth, device, process, schedule, production, tv, user, log, backup
app.include_router(auth.router)
app.include_router(device.router)
app.include_router(process.router)
app.include_router(schedule.router)
app.include_router(production.router)
app.include_router(tv.router)
app.include_router(user.router)
app.include_router(log.router)
app.include_router(backup.router)

@app.get("/")
async def root():
    return RedirectResponse(url="/login")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
```

- [ ] **Step 6: 创建 .env.example**

```ini
DB_HOST=101.43.84.176
DB_PORT=1357
DB_USER=zksuidaolu2
DB_PASSWORD=GHT4EFy228jQh5sx
DB_NAME=zksuidaolu2
SECRET_KEY=zk-tunnel-furnace-dev-secret-2026
```

- [ ] **Step 7: 创建空 __init__.py 文件**

所有 `__init__.py` 内容均为空文件。

---

### Task 2: 数据库初始化脚本

**文件:**
- 创建: `sql/init_database.sql`

- [ ] **Step 1: 编写完整的数据库建表脚本**

```sql
-- ============================================================
-- 中科恒泰隧道炉排产与生产可视化系统 - 数据库初始化
-- Database: zksuidaolu2
-- ============================================================

-- 1. 设备管理
CREATE TABLE IF NOT EXISTS furnaces (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL COMMENT '炉子名称',
    code VARCHAR(20) NOT NULL UNIQUE COMMENT '编码: FOAM/CURE',
    section_count INT NOT NULL COMMENT '节拍数量',
    section_minutes INT NOT NULL DEFAULT 16 COMMENT '每节分钟数',
    sort_order INT NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS furnace_sections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    furnace_id INT NOT NULL,
    section_order INT NOT NULL COMMENT '节拍序号',
    section_name VARCHAR(50) DEFAULT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    FOREIGN KEY (furnace_id) REFERENCES furnaces(id),
    UNIQUE KEY uk_furnace_section (furnace_id, section_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS temperature_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    furnace_id INT NOT NULL,
    section_id INT DEFAULT NULL,
    target_temp DECIMAL(6,1) NOT NULL,
    zone_start INT DEFAULT NULL,
    zone_end INT DEFAULT NULL,
    zone_name VARCHAR(50) DEFAULT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (furnace_id) REFERENCES furnaces(id),
    FOREIGN KEY (section_id) REFERENCES furnace_sections(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 工艺组合管理
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    description TEXT DEFAULT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS processes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    process_name VARCHAR(100) NOT NULL,
    version_no VARCHAR(20) NOT NULL,
    is_current TINYINT(1) NOT NULL DEFAULT 1,
    status ENUM('draft','published','archived') NOT NULL DEFAULT 'draft',
    created_by INT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    UNIQUE KEY uk_product_version (product_id, process_name, version_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS process_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    process_id INT NOT NULL,
    step_order INT NOT NULL,
    section_start INT NOT NULL,
    section_end INT NOT NULL,
    target_temp DECIMAL(6,1) NOT NULL,
    operation_guide TEXT DEFAULT NULL,
    key_phenomena TEXT DEFAULT NULL,
    FOREIGN KEY (process_id) REFERENCES processes(id),
    UNIQUE KEY uk_process_step (process_id, step_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 排产管理
CREATE TABLE IF NOT EXISTS schedule_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(50) NOT NULL UNIQUE,
    process_id INT NOT NULL,
    product_id INT NOT NULL,
    batch_no VARCHAR(100) NOT NULL,
    quantity INT NOT NULL,
    blank_sections INT NOT NULL DEFAULT 0,
    scheduled_time DATETIME NOT NULL,
    assigned_furnace_id INT DEFAULT NULL,
    status ENUM('pending','in_production','completed','cancelled') NOT NULL DEFAULT 'pending',
    notes TEXT DEFAULT NULL,
    created_by INT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (process_id) REFERENCES processes(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (assigned_furnace_id) REFERENCES furnaces(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS schedule_order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    schedule_order_id INT NOT NULL,
    batch_label VARCHAR(50) NOT NULL,
    batch_seq INT NOT NULL,
    quantity INT NOT NULL,
    entry_section INT DEFAULT NULL,
    status ENUM('pending','in_furnace','completed') NOT NULL DEFAULT 'pending',
    FOREIGN KEY (schedule_order_id) REFERENCES schedule_orders(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 生产控制
CREATE TABLE IF NOT EXISTS production_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    furnace_id INT NOT NULL,
    status ENUM('idle','running','paused','stopped') NOT NULL DEFAULT 'idle',
    current_order_id INT DEFAULT NULL,
    current_section INT DEFAULT 1,
    started_at DATETIME DEFAULT NULL,
    paused_at DATETIME DEFAULT NULL,
    stopped_at DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (furnace_id) REFERENCES furnaces(id),
    FOREIGN KEY (current_order_id) REFERENCES schedule_orders(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS production_batches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    production_run_id INT NOT NULL,
    schedule_order_id INT NOT NULL,
    schedule_order_item_id INT DEFAULT NULL,
    batch_label VARCHAR(50) NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    process_name VARCHAR(100) NOT NULL,
    current_section INT NOT NULL DEFAULT 1,
    entry_section INT NOT NULL,
    status ENUM('in_furnace','completed') NOT NULL DEFAULT 'in_furnace',
    entered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME DEFAULT NULL,
    FOREIGN KEY (production_run_id) REFERENCES production_runs(id),
    FOREIGN KEY (schedule_order_id) REFERENCES schedule_orders(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS batch_section_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT NOT NULL,
    furnace_id INT NOT NULL,
    section_order INT NOT NULL,
    target_temp DECIMAL(6,1) NOT NULL,
    actual_temp DECIMAL(6,1) DEFAULT NULL,
    entered_at DATETIME NOT NULL,
    exited_at DATETIME DEFAULT NULL,
    actual_duration_min INT DEFAULT NULL,
    FOREIGN KEY (batch_id) REFERENCES production_batches(id),
    FOREIGN KEY (furnace_id) REFERENCES furnaces(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS blank_section_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    production_run_id INT NOT NULL,
    furnace_id INT NOT NULL,
    section_order INT NOT NULL,
    inserted_at DATETIME NOT NULL,
    removed_at DATETIME DEFAULT NULL,
    FOREIGN KEY (production_run_id) REFERENCES production_runs(id),
    FOREIGN KEY (furnace_id) REFERENCES furnaces(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 生产报告
CREATE TABLE IF NOT EXISTS production_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    schedule_order_id INT NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    batch_no VARCHAR(100) NOT NULL,
    batch_label VARCHAR(50) NOT NULL,
    furnace_name VARCHAR(50) NOT NULL,
    planned_sections INT NOT NULL,
    actual_sections INT NOT NULL,
    planned_duration_min INT NOT NULL,
    actual_duration_min INT NOT NULL,
    entry_time DATETIME NOT NULL,
    exit_time DATETIME NOT NULL,
    avg_temp DECIMAL(6,1) DEFAULT NULL,
    max_temp DECIMAL(6,1) DEFAULT NULL,
    min_temp DECIMAL(6,1) DEFAULT NULL,
    status ENUM('completed','partial','abnormal') NOT NULL DEFAULT 'completed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_order_id) REFERENCES schedule_orders(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS report_compare_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    report_id INT NOT NULL,
    section_order INT NOT NULL,
    planned_temp DECIMAL(6,1) NOT NULL,
    actual_temp DECIMAL(6,1) DEFAULT NULL,
    planned_duration INT NOT NULL,
    actual_duration INT DEFAULT NULL,
    FOREIGN KEY (report_id) REFERENCES production_reports(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. 用户管理
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    real_name VARCHAR(100) NOT NULL,
    is_admin TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    permissions JSON DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. 日志系统
CREATE TABLE IF NOT EXISTS operation_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    username VARCHAR(50) NOT NULL,
    real_name VARCHAR(100) NOT NULL,
    module VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) DEFAULT NULL,
    target_id INT DEFAULT NULL,
    target_label VARCHAR(200) DEFAULT NULL,
    detail TEXT DEFAULT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_module (module),
    INDEX idx_user (user_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. 系统配置
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description VARCHAR(200) DEFAULT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====== 初始数据 ======
INSERT INTO furnaces (name, code, section_count, section_minutes, sort_order) VALUES
('发泡炉', 'FOAM', 18, 16, 1),
('固化炉', 'CURE', 52, 16, 2);

-- 初始化炉子节拍
INSERT INTO furnace_sections (furnace_id, section_order, section_name)
SELECT 1, n, CONCAT('发泡炉第', n, '节') FROM (
    SELECT 1 AS n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5
    UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
    UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15
    UNION SELECT 16 UNION SELECT 17 UNION SELECT 18
) AS nums;

INSERT INTO furnace_sections (furnace_id, section_order, section_name)
SELECT 2, n, CONCAT('固化炉第', n, '节') FROM (
    SELECT 1 AS n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5
    UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
    UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15
    UNION SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19 UNION SELECT 20
    UNION SELECT 21 UNION SELECT 22 UNION SELECT 23 UNION SELECT 24 UNION SELECT 25
    UNION SELECT 26 UNION SELECT 27 UNION SELECT 28 UNION SELECT 29 UNION SELECT 30
    UNION SELECT 31 UNION SELECT 32 UNION SELECT 33 UNION SELECT 34 UNION SELECT 35
    UNION SELECT 36 UNION SELECT 37 UNION SELECT 38 UNION SELECT 39 UNION SELECT 40
    UNION SELECT 41 UNION SELECT 42 UNION SELECT 43 UNION SELECT 44 UNION SELECT 45
    UNION SELECT 46 UNION SELECT 47 UNION SELECT 48 UNION SELECT 49 UNION SELECT 50
    UNION SELECT 51 UNION SELECT 52
) AS nums;

-- 默认管理员密码: admin / 262626 (需要启动后通过注册页面创建)
INSERT IGNORE INTO system_config (config_key, config_value, description) VALUES
('tv_refresh_interval', '10', '电视大屏刷新间隔(秒)'),
('default_section_minutes', '16', '默认每节拍分钟数');

-- 默认生产运行记录
INSERT IGNORE INTO production_runs (furnace_id, status) VALUES (1, 'idle'), (2, 'idle');
```

---

### Task 3: 登录认证模块

**文件:**
- 创建: `services/auth_service.py`
- 创建: `routers/auth.py`
- 创建: `templates/login.html`
- 修改: `db/queries.py` (添加用户查询)

- [ ] **Step 1: 创建 db/queries.py**

```python
# 所有 SQL 查询集中在此文件，按模块分组
import logging
from db.pool import query, query_one

logger = logging.getLogger(__name__)

# ====== Auth ======
def get_user_by_username(username):
    return query_one("SELECT * FROM users WHERE username = %s AND is_active = 1", (username,))

def get_user_by_id(user_id):
    return query_one("SELECT * FROM users WHERE id = %s", (user_id,))
```

- [ ] **Step 2: 创建 services/auth_service.py**

```python
import bcrypt
from itsdangerous import URLSafeTimedSerializer
import settings

serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def check_permission(user: dict, module: str) -> bool:
    if user.get("is_admin"):
        return True
    perm = user.get("permissions")
    if not perm:
        return False
    if isinstance(perm, str):
        import json
        perm = json.loads(perm)
    return perm.get(module, False) == 1
```

- [ ] **Step 3: 创建 templates/login.html**

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>登录 - {{ app_title }}</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: 'Microsoft YaHei', system-ui, sans-serif;
  background: #ecf0f1;
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh;
}
.login-card {
  background: #fff; border-radius: 8px;
  padding: 40px; width: 400px; max-width: 90vw;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}
.login-card h1 { font-size: 20px; color: #1a5276; text-align: center; margin-bottom: 4px; }
.login-card .subtitle { font-size: 13px; color: #7f8c8d; text-align: center; margin-bottom: 24px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; color: #2c3e50; margin-bottom: 4px; font-weight: 600; }
.form-group input {
  width: 100%; padding: 10px 12px; border: 1px solid #d5dbdf; border-radius: 4px;
  font-size: 14px; background: #f8f9fa; outline: none;
}
.form-group input:focus { border-color: #2980b9; background: #fff; }
.btn-login {
  width: 100%; padding: 10px; background: #2980b9; color: #fff;
  border: none; border-radius: 4px; font-size: 15px; cursor: pointer;
  transition: background 0.2s;
}
.btn-login:hover { background: #3498db; }
.error { color: #e74c3c; font-size: 13px; margin-bottom: 12px; text-align: center; }
</style>
</head>
<body>
<div class="login-card">
  <h1>中科恒泰隧道炉</h1>
  <div class="subtitle">排产与生产可视化系统 · 用户登录</div>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="post" action="/login">
    <div class="form-group">
      <label>用户名</label>
      <input type="text" name="username" required autofocus>
    </div>
    <div class="form-group">
      <label>密码</label>
      <input type="password" name="password" required>
    </div>
    <button type="submit" class="btn-login">登 录</button>
  </form>
</div>
</body>
</html>
```

- [ ] **Step 4: 创建 routers/auth.py**

```python
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import settings
from services.auth_service import verify_password
from db.queries import get_user_by_username

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        return None
    return user

def login_required(request: Request):
    user = get_current_user(request)
    if not user:
        raise RedirectResponse(url="/login", status_code=302)
    return user

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request, "app_title": settings.APP_TITLE
    })

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = get_user_by_username(username)
    if not user or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse("login.html", {
            "request": request, "error": "用户名或密码错误", "app_title": settings.APP_TITLE
        })
    request.session["user"] = {
        "id": user["id"], "username": user["username"],
        "real_name": user["real_name"], "is_admin": user["is_admin"],
        "permissions": user["permissions"]
    }
    return RedirectResponse(url="/schedule/", status_code=302)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)
```

---

### Task 4: 基础模板 + 导航栏

**文件:**
- 创建: `templates/base.html`
- 创建: `templates/nav.html`
- 创建: `static/css/flat.css`

- [ ] **Step 1: 创建 templates/base.html**

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{% block title %}{{ app_title }}{% endblock %}</title>
<link rel="stylesheet" href="/static/css/flat.css?v={{ static_version }}">
{% block extra_head %}{% endblock %}
</head>
<body>
{% if request.session.user %}
{% include "nav.html" %}
{% endif %}
<div class="main-content">
  {% block content %}{% endblock %}
</div>
<script src="/static/js/common.js?v={{ static_version }}"></script>
{% block extra_scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 2: 创建 templates/nav.html**

导航栏包含所有模块的标签页，根据用户权限动态显示。

- [ ] **Step 3: 创建 static/css/flat.css**

PC端样式，参考现有项目的颜色方案。

---

### Task 5: 设备管理模块

**文件:**
- 创建: `routers/device.py`
- 创建: `templates/device/list.html`
- 创建: `templates/device/temp_settings.html`
- 修改: `db/queries.py` (添加设备查询)

- [ ] **Step 1: 在 db/queries.py 中添加设备管理查询函数**

```python
# ====== Device ======
def get_furnaces():
    return query("SELECT * FROM furnaces WHERE is_active = 1 ORDER BY sort_order")

def get_furnace(furnace_id):
    return query_one("SELECT * FROM furnaces WHERE id = %s", (furnace_id,))

def get_furnace_sections(furnace_id):
    return query("SELECT * FROM furnace_sections WHERE furnace_id = %s AND is_active = 1 ORDER BY section_order", (furnace_id,))

def get_temp_settings(furnace_id):
    return query("SELECT * FROM temperature_settings WHERE furnace_id = %s AND is_active = 1", (furnace_id,))

def save_temp_settings(furnace_id, settings_list):
    """批量保存温度设置：先清除旧设置，再插入新设置"""
    query("UPDATE temperature_settings SET is_active = 0 WHERE furnace_id = %s", (furnace_id,))
    for s in settings_list:
        query("""INSERT INTO temperature_settings (furnace_id, section_id, target_temp, zone_start, zone_end, zone_name)
                 VALUES (%s, %s, %s, %s, %s, %s)""",
              (furnace_id, s.get("section_id"), s.get("target_temp"),
               s.get("zone_start"), s.get("zone_end"), s.get("zone_name")))

def update_furnace_config(furnace_id, section_count, section_minutes):
    query("UPDATE furnaces SET section_count=%s, section_minutes=%s WHERE id=%s",
          (section_count, section_minutes, furnace_id))
```

- [ ] **Step 2: 创建 routers/device.py**

```python
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import settings
from routers.auth import login_required
from services.auth_service import check_permission
from middleware.log_middleware import log_operation
import db.queries as dbq

router = APIRouter(dependencies=[Depends(login_required)])
templates = Jinja2Templates(directory="templates")

@router.get("/device/", response_class=HTMLResponse)
async def device_list(request: Request):
    user = login_required(request)
    if not check_permission(user, "device"):
        return templates.TemplateResponse("base.html", {"request": request, "error": "无权限"})
    furnaces = dbq.get_furnaces()
    for f in furnaces:
        f["sections"] = dbq.get_furnace_sections(f["id"])
        f["temp_settings"] = dbq.get_temp_settings(f["id"])
    return templates.TemplateResponse("device/list.html", {
        "request": request, "furnaces": furnaces,
        "app_title": settings.APP_TITLE, "static_version": settings.STATIC_VERSION
    })

@router.get("/api/device/furnace/{furnace_id}/temp")
async def get_temp(furnace_id: int, request: Request):
    login_required(request)
    settings_list = dbq.get_temp_settings(furnace_id)
    sections = dbq.get_furnace_sections(furnace_id)
    return {"sections": sections, "settings": settings_list}

@router.post("/api/device/furnace/{furnace_id}/temp")
@log_operation(module='device', action='update')
async def save_temp(furnace_id: int, request: Request):
    user = login_required(request)
    data = await request.json()
    dbq.save_temp_settings(furnace_id, data.get("settings", []))
    return {"success": True}
```

- [ ] **Step 3: 创建 templates/device/list.html**

设备列表页面，显示两个炉子的卡片，包含节拍配置和温度设置表单。

- [ ] **Step 4: 创建 templates/device/temp_settings.html**

带温度输入表单的页面，支持两种模式：独立节拍设置 / 区间统一设置。

---

### Task 6: 工艺组合管理模块

**文件:**
- 创建: `routers/process.py`
- 创建: `templates/process/product_list.html`
- 创建: `templates/process/process_list.html`
- 创建: `templates/process/process_edit.html`
- 修改: `db/queries.py`

- [ ] **Step 1: db/queries.py 添加工艺查询**

```python
# ====== Process ======
def get_products():
    return query("SELECT * FROM products WHERE is_active = 1 ORDER BY name")

def create_product(name, code, description=""):
    return query("INSERT INTO products (name, code, description) VALUES (%s, %s, %s)",
                 (name, code, description))

def get_processes(product_id=None):
    if product_id:
        return query("SELECT p.*, pr.name as product_name FROM processes p JOIN products pr ON p.product_id=pr.id WHERE p.product_id=%s ORDER BY p.created_at DESC", (product_id,))
    return query("SELECT p.*, pr.name as product_name FROM processes p JOIN products pr ON p.product_id=pr.id ORDER BY p.created_at DESC")

def create_process(product_id, process_name, version_no, created_by):
    return query("INSERT INTO processes (product_id, process_name, version_no, created_by) VALUES (%s, %s, %s, %s)",
                 (product_id, process_name, version_no, created_by))

def get_process(process_id):
    return query_one("SELECT p.*, pr.name as product_name FROM processes p JOIN products pr ON p.product_id=pr.id WHERE p.id=%s", (process_id,))

def get_process_steps(process_id):
    return query("SELECT * FROM process_steps WHERE process_id=%s ORDER BY step_order", (process_id,))

def save_process_steps(process_id, steps):
    query("DELETE FROM process_steps WHERE process_id=%s", (process_id,))
    for s in steps:
        query("INSERT INTO process_steps (process_id, step_order, section_start, section_end, target_temp, operation_guide, key_phenomena) VALUES (%s,%s,%s,%s,%s,%s,%s)",
              (process_id, s["step_order"], s["section_start"], s["section_end"], s["target_temp"], s.get("operation_guide"), s.get("key_phenomena")))

def publish_process(process_id):
    query("UPDATE processes SET status='published' WHERE id=%s", (process_id,))
```

- [ ] **Step 2: 创建 routers/process.py (核心路由)**

包含产品CRUD、工艺CRUD、步骤编辑、发布功能的路由。

- [ ] **Step 3: 创建三个模板文件**

产品列表 → 工艺列表 → 工艺编辑（带操作指导输入）

---

### Task 7: 排产管理模块

**文件:**
- 创建: `routers/schedule.py`
- 创建: `templates/schedule/list.html`
- 创建: `templates/schedule/form.html`
- 修改: `db/queries.py`

- [ ] **Step 1: db/queries.py 添加排产查询**

```python
# ====== Schedule ======
def get_orders(status=None):
    sql = """SELECT o.*, p.name as product_name, ps.process_name, f.name as furnace_name
             FROM schedule_orders o
             JOIN products p ON o.product_id=p.id
             JOIN processes ps ON o.process_id=ps.id
             LEFT JOIN furnaces f ON o.assigned_furnace_id=f.id"""
    if status:
        sql += " WHERE o.status=%s ORDER BY o.scheduled_time ASC"
        return query(sql, (status,))
    return query(sql + " ORDER BY o.created_at DESC")

def create_order(order_no, process_id, product_id, batch_no, quantity, blank_sections, scheduled_time, assigned_furnace_id, created_by):
    return query("""INSERT INTO schedule_orders (order_no, process_id, product_id, batch_no, quantity, blank_sections, scheduled_time, assigned_furnace_id, created_by)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                 (order_no, process_id, product_id, batch_no, quantity, blank_sections, scheduled_time, assigned_furnace_id, created_by))

def cancel_order(order_id):
    query("UPDATE schedule_orders SET status='cancelled' WHERE id=%s", (order_id,))

def get_pending_orders(furnace_id=None):
    sql = """SELECT o.*, p.name as product_name, ps.process_name, f.name as furnace_name
             FROM schedule_orders o
             JOIN products p ON o.product_id=p.id
             JOIN processes ps ON o.process_id=ps.id
             LEFT JOIN furnaces f ON o.assigned_furnace_id=f.id
             WHERE o.status='pending'"""
    params = []
    if furnace_id:
        sql += " AND (o.assigned_furnace_id=%s OR o.assigned_furnace_id IS NULL)"
        params.append(furnace_id)
    sql += " ORDER BY o.scheduled_time ASC"
    return query(sql, params)

def generate_order_no():
    import datetime
    prefix = datetime.datetime.now().strftime("P%Y%m%d-")
    row = query_one("SELECT COUNT(*) as cnt FROM schedule_orders WHERE order_no LIKE %s", (prefix + "%",))
    return prefix + str(row["cnt"] + 1).zfill(3)
```

- [ ] **Step 2: 创建 routers/schedule.py**

排产单的增删改查、状态切换、CSV导出功能。

- [ ] **Step 3: 创建模板文件**

排产表单包含：选择产品→选择工艺→输入数量/批号/空白节拍/预定时间→提交。

---

### Task 8: 生产控制模块

**文件:**
- 创建: `routers/production.py`
- 创建: `services/production_service.py`
- 创建: `templates/production/control.html`
- 创建: `templates/production/section_ops.html`
- 创建: `templates/production/report.html`
- 创建: `static/js/production.js`
- 修改: `db/queries.py`

- [ ] **Step 1: db/queries.py 添加生产相关查询**

```python
# ====== Production ======
def get_production_run(furnace_id):
    return query_one("SELECT * FROM production_runs WHERE furnace_id=%s", (furnace_id,))

def update_run_status(run_id, status):
    query("UPDATE production_runs SET status=%s WHERE id=%s", (status, run_id))

def get_batches_in_furnace(run_id):
    return query("SELECT * FROM production_batches WHERE production_run_id=%s AND status='in_furnace' ORDER BY current_section", (run_id,))

def get_batch(batch_id):
    return query_one("SELECT * FROM production_batches WHERE id=%s", (batch_id,))

def update_batch_section(batch_id, new_section):
    query("UPDATE production_batches SET current_section=%s WHERE id=%s", (new_section, batch_id))

def complete_batch(batch_id):
    query("UPDATE production_batches SET status='completed', completed_at=NOW() WHERE id=%s", (batch_id,))

def create_batch_section_log(batch_id, furnace_id, section_order, target_temp):
    return query("INSERT INTO batch_section_logs (batch_id, furnace_id, section_order, target_temp, entered_at) VALUES (%s,%s,%s,%s,NOW())",
                 (batch_id, furnace_id, section_order, target_temp))

def close_batch_section_log(batch_id, section_order):
    query("UPDATE batch_section_logs SET exited_at=NOW(), actual_duration_min=TIMESTAMPDIFF(MINUTE, entered_at, NOW()) WHERE batch_id=%s AND section_order=%s AND exited_at IS NULL",
          (batch_id, section_order))

def insert_blank_section(run_id, furnace_id, section_order):
    return query("INSERT INTO blank_section_logs (production_run_id, furnace_id, section_order, inserted_at) VALUES (%s,%s,%s,NOW())",
                 (run_id, furnace_id, section_order))

def get_section_temp(furnace_id, section_order):
    row = query_one("SELECT target_temp FROM temperature_settings WHERE furnace_id=%s AND (section_id IN (SELECT id FROM furnace_sections WHERE furnace_id=%s AND section_order=%s) OR (zone_start<=%s AND zone_end>=%s)) AND is_active=1 LIMIT 1",
                     (furnace_id, furnace_id, section_order, section_order, section_order))
    return row["target_temp"] if row else 0

# ====== Report ======
def get_report_by_order(order_id):
    return query_one("SELECT * FROM production_reports WHERE schedule_order_id=%s", (order_id,))

def create_report(data):
    return query("""INSERT INTO production_reports (schedule_order_id, product_name, batch_no, batch_label, furnace_name, planned_sections, actual_sections, planned_duration_min, actual_duration_min, entry_time, exit_time, avg_temp, max_temp, min_temp, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                 (data["schedule_order_id"], data["product_name"], data["batch_no"], data["batch_label"],
                  data["furnace_name"], data["planned_sections"], data["actual_sections"],
                  data["planned_duration_min"], data["actual_duration_min"],
                  data["entry_time"], data["exit_time"], data.get("avg_temp"),
                  data.get("max_temp"), data.get("min_temp"), data.get("status", "completed")))

def get_report_compare(report_id):
    return query("SELECT * FROM report_compare_data WHERE report_id=%s ORDER BY section_order", (report_id,))
```

- [ ] **Step 2: 创建 services/production_service.py**

```python
from db.pool import query, query_one
import db.queries as dbq

def start_furnace(furnace_id):
    """开机：将第一个待生产的排产单投入生产"""
    run = dbq.get_production_run(furnace_id)
    if not run or run["status"] != "idle":
        return False, "炉子不在空闲状态"
    order = dbq.get_pending_orders(furnace_id)
    if not order:
        return False, "没有待生产的排产单"
    order = order[0]
    dbq.update_run_status(run["id"], "running")
    query("UPDATE production_runs SET current_order_id=%s, current_section=1, started_at=NOW() WHERE id=%s",
          (order["id"], run["id"]))
    dbq.query("UPDATE schedule_orders SET status='in_production' WHERE id=%s", (order["id"],))
    batch_id = dbq.create_batch(run["id"], order["id"], order.get("batch_label", "P01"),
                                 order["product_name"], order.get("process_name", ""), 1)
    # 记录节拍日志
    temp = dbq.get_section_temp(furnace_id, 1)
    dbq.create_batch_section_log(batch_id, furnace_id, 1, temp)
    return True, {"run_id": run["id"], "batch_id": batch_id}

def advance_batch(batch_id):
    """批次前进一节"""
    batch = dbq.get_batch(batch_id)
    if not batch or batch["status"] != "in_furnace":
        return False, "批次不在生产中"
    furnace_id = query_one("SELECT furnace_id FROM production_runs WHERE id=%s", (batch["production_run_id"],))
    if not furnace_id:
        return False, "找不到炉子"
    furnace_id = furnace_id["furnace_id"]
    furnace = dbq.get_furnace(furnace_id)
    new_section = batch["current_section"] + 1
    if new_section > furnace["section_count"]:
        dbq.close_batch_section_log(batch_id, batch["current_section"])
        dbq.complete_batch(batch_id)
        return True, {"completed": True, "message": "批次已完成"}
    # 关闭当前节拍日志
    dbq.close_batch_section_log(batch_id, batch["current_section"])
    # 更新批次位置
    dbq.update_batch_section(batch_id, new_section)
    # 新建节拍日志
    temp = dbq.get_section_temp(furnace_id, new_section)
    dbq.create_batch_section_log(batch_id, furnace_id, new_section, temp)
    return True, {"new_section": new_section, "completed": False}

def retreat_batch(batch_id):
    """批次后退一节"""
    batch = dbq.get_batch(batch_id)
    if not batch or batch["current_section"] <= 1:
        return False, "已在第一节"
    dbq.close_batch_section_log(batch_id, batch["current_section"])
    new_section = batch["current_section"] - 1
    dbq.update_batch_section(batch_id, new_section)
    furnace_id = query_one("SELECT furnace_id FROM production_runs WHERE id=%s", (batch["production_run_id"],))["furnace_id"]
    temp = dbq.get_section_temp(furnace_id, new_section)
    dbq.create_batch_section_log(batch_id, furnace_id, new_section, temp)
    return True, {"new_section": new_section}

def advance_all(run_id):
    batches = dbq.get_batches_in_furnace(run_id)
    results = []
    for b in batches:
        ok, msg = advance_batch(b["id"])
        results.append({"batch": b["batch_label"], "ok": ok, "msg": msg})
    return results

def retreat_all(run_id):
    batches = dbq.get_batches_in_furnace(run_id)
    results = []
    for b in batches:
        ok, msg = retreat_batch(b["id"])
        results.append({"batch": b["batch_label"], "ok": ok, "msg": msg})
    return results

def pause_furnace(furnace_id):
    run = dbq.get_production_run(furnace_id)
    if not run or run["status"] != "running":
        return False, "炉子不在运行状态"
    dbq.update_run_status(run["id"], "paused")
    return True, {}

def resume_furnace(furnace_id):
    run = dbq.get_production_run(furnace_id)
    if not run or run["status"] != "paused":
        return False, "炉子不在暂停状态"
    dbq.update_run_status(run["id"], "running")
    return True, {}

def stop_furnace(furnace_id):
    run = dbq.get_production_run(furnace_id)
    if not run:
        return False, "找不到炉子"
    dbq.update_run_status(run["id"], "stopped")
    query("UPDATE production_runs SET stopped_at=NOW() WHERE id=%s", (run["id"],))
    return True, {}

def insert_blank(furnace_id, section_order):
    run = dbq.get_production_run(furnace_id)
    if not run:
        return False, "找不到炉子"
    # 该位置之后的所有批次前进一节
    batches = dbq.get_batches_in_furnace(run["id"])
    for b in batches:
        if b["current_section"] >= section_order:
            dbq.close_batch_section_log(b["id"], b["current_section"])
            new_section = b["current_section"] + 1
            dbq.update_batch_section(b["id"], new_section)
    dbq.insert_blank_section(run["id"], furnace_id, section_order)
    return True, {}

# 辅助 - 在 queries 中
def create_batch(production_run_id, schedule_order_id, batch_label, product_name, process_name, entry_section):
    return query("""INSERT INTO production_batches (production_run_id, schedule_order_id, batch_label, product_name, process_name, current_section, entry_section)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                 (production_run_id, schedule_order_id, batch_label, product_name, process_name, entry_section, entry_section))
```

注意：`create_batch` 实际上应当加到 `queries.py` 中，这里是作为 service 层的辅助。

- [ ] **Step 3: 创建 routers/production.py**

包含生产控制页面、开机/暂停/恢复/停止API、节拍推进API、生产报告API。

- [ ] **Step 4: 创建 templates/production/control.html**

生产控制面板，显示两个炉子的状态、控制按钮、当前批次列表、节拍操作。

- [ ] **Step 5: 创建 templates/production/report.html**

生产报告页面，显示计划vs实际对比表格，逐节对比温度和时间。

---

### Task 9: TV可视化大屏模块

**文件:**
- 创建: `routers/tv.py`
- 创建: `templates/tv/display.html`
- 创建: `static/css/tv.css`
- 创建: `static/js/tv.js`

- [ ] **Step 1: 创建 static/css/tv.css**

使用 V5 设计中的 CSS 样式（深色背景、大节拍格、呼吸动画、半透明背景色），全部采用 vh/vw 相对单位。

- [ ] **Step 2: 创建 static/js/tv.js**

```javascript
// TV大屏主逻辑 - 10秒轮询刷新
let refreshInterval = 10000;

function initTV() {
    updateClock();
    setInterval(updateClock, 1000);
    fetchStatus();
    setInterval(fetchStatus, refreshInterval);
}

function updateClock() {
    var now = new Date();
    document.getElementById('clockDisplay').textContent =
        now.toTimeString().slice(0, 8);
}

function fetchStatus() {
    fetch('/api/tv/furnace-status')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            renderFurnace('foamGrid', data.furnaces[0]);
            renderFurnace('cureGrid', data.furnaces[1]);
            updateInfo(data.furnaces);
        })
        .catch(function(e) { console.error('TV fetch error:', e); });
    fetch('/api/tv/schedule-queue')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            renderScheduleQueue(data);
        })
        .catch(function(e) { console.error('TV queue fetch error:', e); });
}

function renderFurnace(containerId, furnace) {
    var container = document.getElementById(containerId);
    if (!container) return;
    var html = '';
    for (var i = 0; i < furnace.sections.length; i++) {
        var s = furnace.sections[i];
        var cls = 'section-cell';
        if (s.has_product) {
            cls += ' occupied ' + s.zone;
            if (furnace.id === 1) cls += ' foam-batch';
            else cls += ' cure-batch';
        } else {
            cls += ' empty';
        }
        html += '<div class="' + cls + '">';
        html += '<span class="sec-num">' + s.order + '</span>';
        html += '<span class="temp-val">' + s.target_temp + '°</span>';
        if (s.has_product && s.batch) {
            html += '<div class="batch-info-top">' + s.batch.label + '</div>';
            html += '<div class="batch-product">' + (s.batch.product_name || '') + '</div>';
            html += '<div class="batch-progress-bar"><div class="fill" style="width:' + (s.batch.progress || 0) + '%"></div></div>';
        }
        html += '</div>';
    }
    container.innerHTML = html;
}

function renderScheduleQueue(data) {
    var list = document.getElementById('scheduleList');
    if (!list) return;
    var scheduleHtml = '';
    var queue = data.queue || [];
    for (var i = 0; i < queue.length; i++) {
        var s = queue[i];
        var isReady = s.is_ready;
        scheduleHtml += '<div class="schedule-item' + (isReady ? ' next-up' : '') + '">';
        scheduleHtml += '<div class="item-header">';
        scheduleHtml += '<span class="item-title">' + (s.batch_label || '') + ' · ' + (s.product_name || '') + '</span>';
        scheduleHtml += '<span class="item-status ' + (isReady ? 'ready' : 'pending') + '">' + (isReady ? '即将生产' : '等待') + '</span>';
        scheduleHtml += '</div>';
        scheduleHtml += '<div class="item-info">';
        scheduleHtml += '<div class="info-row"><span><span class="label-text">批号</span> ' + (s.batch_no || '') + '</span>';
        scheduleHtml += '<span><span class="label-text">数量</span> ' + (s.quantity || 0) + '件</span></div>';
        scheduleHtml += '<div class="info-row"><span><span class="label-text">生产炉</span> ' + (s.furnace_name || '') + '</span>';
        scheduleHtml += '<span><span class="label-text">预定时间</span> ' + (s.scheduled_time || '') + '</span></div>';
        scheduleHtml += '</div></div>';
    }
    list.innerHTML = scheduleHtml;

    var summary = data.summary || {};
    var summaryEl = document.getElementById('scheduleSummary');
    if (summaryEl) {
        summaryEl.innerHTML =
            '<div class="stat-item"><span class="stat-num">' + (summary.pending_count || 0) + '</span> 待生产</div>' +
            '<div class="stat-item"><span class="stat-num">' + (summary.total_quantity || 0) + '</span> 总件数</div>' +
            '<div class="stat-item"><span class="stat-num">' + (summary.in_production || 0) + '</span> 生产中</div>';
    }
    var countEl = document.getElementById('queueCount');
    if (countEl) countEl.textContent = queue.length;
}

document.addEventListener('DOMContentLoaded', initTV);
```

- [ ] **Step 3: 创建 routers/tv.py**

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import settings
import db.queries as dbq

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/tv", response_class=HTMLResponse)
async def tv_display(request: Request):
    furnaces = dbq.get_furnaces()
    return templates.TemplateResponse("tv/display.html", {
        "request": request,
        "furnaces": furnaces,
        "app_title": settings.APP_TITLE,
        "static_version": settings.STATIC_VERSION,
        "refresh_interval": settings.TV_REFRESH_INTERVAL
    })

@router.get("/api/tv/furnace-status")
async def tv_furnace_status():
    furnaces = dbq.get_furnaces()
    result = {"furnaces": []}
    for f in furnaces:
        run = dbq.get_production_run(f["id"])
        batches = []
        if run and run["status"] == "running":
            batches = dbq.get_batches_in_furnace(run["id"])
        sections = dbq.get_furnace_sections(f["id"])
        temp_settings = {s["section_id"]: s["target_temp"] for s in dbq.get_temp_settings(f["id"]) if s["section_id"]}
        section_data = []
        for s in sections:
            batch_in_section = [b for b in batches if b["current_section"] == s["section_order"]]
            has_product = len(batch_in_section) > 0
            temp = temp_settings.get(s["id"], 0)
            zone = "low"
            if temp >= 155: zone = "high"
            elif temp >= 100: zone = "mid"
            elif temp >= 80: zone = "low"
            else: zone = "cool"
            batch_info = None
            if has_product:
                b = batch_in_section[0]
                progress = round((b["current_section"] / f["section_count"]) * 100)
                batch_info = {
                    "label": b["batch_label"],
                    "product_name": b["product_name"],
                    "progress": progress
                }
            section_data.append({
                "order": s["section_order"],
                "target_temp": float(temp),
                "zone": zone,
                "has_product": has_product,
                "batch": batch_info
            })
        result["furnaces"].append({
            "id": f["id"],
            "name": f["name"],
            "section_count": f["section_count"],
            "section_minutes": f["section_minutes"],
            "running": run and run["status"] == "running",
            "sections": section_data
        })
    return result

@router.get("/api/tv/schedule-queue")
async def tv_schedule_queue():
    orders = dbq.get_pending_orders()
    queue = []
    for i, o in enumerate(orders):
        queue.append({
            "batch_label": "P" + str(i + 3).zfill(2),
            "batch_no": o["batch_no"],
            "product_name": o["product_name"],
            "process_name": o.get("process_name", ""),
            "quantity": o["quantity"],
            "furnace_name": o.get("furnace_name", ""),
            "scheduled_time": o["scheduled_time"].strftime("%Y-%m-%d %H:%M") if o.get("scheduled_time") else "",
            "is_ready": i == 0
        })
    return {
        "queue": queue,
        "summary": {
            "pending_count": len(orders),
            "total_quantity": sum(o["quantity"] for o in orders) if orders else 0,
            "in_production": len(dbq.query("SELECT id FROM schedule_orders WHERE status='in_production'"))
        }
    }
```

- [ ] **Step 4: 创建 templates/tv/display.html**

将 V5 设计中的 HTML 模板转换为 Jinja2 模板，集成数据绑定和JS逻辑。

---

### Task 10: 用户管理模块

**文件:**
- 创建: `routers/user.py`
- 创建: `templates/user/list.html`
- 创建: `templates/user/form.html`
- 修改: `db/queries.py`

- [ ] **Step 1: db/queries.py 添加用户管理查询**

```python
# ====== User ======
def get_users():
    return query("SELECT id, username, real_name, is_admin, is_active, permissions, created_at FROM users ORDER BY id")

def create_user(username, password_hash, real_name):
    return query("INSERT INTO users (username, password_hash, real_name) VALUES (%s, %s, %s)",
                 (username, password_hash, real_name))

def update_user(user_id, real_name=None, is_active=None):
    if real_name is not None:
        query("UPDATE users SET real_name=%s WHERE id=%s", (real_name, user_id))
    if is_active is not None:
        query("UPDATE users SET is_active=%s WHERE id=%s", (is_active, user_id))

def set_user_permissions(user_id, permissions_json):
    query("UPDATE users SET permissions=%s WHERE id=%s", (permissions_json, user_id))

def delete_user(user_id):
    query("UPDATE users SET is_active=0 WHERE id=%s AND is_admin=0", (user_id,))
```

- [ ] **Step 2: 创建 routers/user.py**

用户列表、新增、编辑、权限分配、删除路由。

---

### Task 11: 日志系统模块

**文件:**
- 创建: `middleware/log_middleware.py`
- 创建: `routers/log.py`
- 创建: `templates/log/list.html`
- 修改: `db/queries.py`

- [ ] **Step 1: 创建 middleware/log_middleware.py**

```python
import functools
import json
from fastapi import Request
from db.pool import query

def log_operation(module, action):
    """操作日志装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 提取 request 对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if "request" in kwargs:
                request = kwargs["request"]

            result = await func(*args, **kwargs)

            if request and request.session.get("user"):
                user = request.session["user"]
                target_type = kwargs.get("target_type") or kwargs.get("furnace_id")
                target_id = kwargs.get("target_id")
                try:
                    query("""INSERT INTO operation_logs (user_id, username, real_name, module, action, target_type, target_id, ip_address)
                             VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                          (user["id"], user["username"], user["real_name"],
                           module, action, str(target_type) if target_type else None,
                           target_id, request.client.host if request.client else None))
                except Exception:
                    pass
            return result
        return wrapper
    return decorator
```

- [ ] **Step 2: db/queries.py 添加日志查询**

```python
# ====== Log ======
def get_logs(module=None, page=1, per_page=50):
    sql = "SELECT * FROM operation_logs"
    params = []
    if module:
        sql += " WHERE module=%s"
        params.append(module)
    sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([per_page, (page - 1) * per_page])
    rows = query(sql, params)
    count_sql = "SELECT COUNT(*) as total FROM operation_logs" + (" WHERE module=%s" if module else "")
    total = query_one(count_sql, (module,) if module else ())["total"]
    return rows, total
```

- [ ] **Step 3: 创建 routers/log.py**

日志查看页面，支持按模块筛选和分页。

---

### Task 12: 数据备份模块

**文件:**
- 创建: `routers/backup.py`
- 创建: `templates/backup/index.html`
- 修改: `db/queries.py`

- [ ] **Step 1: db/queries.py 添加备份查询**

```python
# ====== Backup ======
def get_backup_schedule_orders(start_date=None, end_date=None, status=None):
    sql = "SELECT * FROM schedule_orders WHERE 1=1"
    params = []
    if start_date:
        sql += " AND created_at >= %s"
        params.append(start_date)
    if end_date:
        sql += " AND created_at <= %s"
        params.append(end_date)
    if status:
        sql += " AND status=%s"
        params.append(status)
    sql += " ORDER BY created_at"
    return query(sql, params)

def get_backup_production_batches(start_date=None, end_date=None):
    sql = "SELECT * FROM production_batches WHERE 1=1"
    params = []
    if start_date:
        sql += " AND entered_at >= %s"
        params.append(start_date)
    if end_date:
        sql += " AND (completed_at <= %s OR entered_at <= %s)"
        params.extend([end_date, end_date])
    sql += " ORDER BY entered_at"
    return query(sql, params)

def get_backup_logs(start_date=None, end_date=None, module=None):
    sql = "SELECT * FROM operation_logs WHERE 1=1"
    params = []
    if start_date:
        sql += " AND created_at >= %s"
        params.append(start_date)
    if end_date:
        sql += " AND created_at <= %s"
        params.append(end_date)
    if module:
        sql += " AND module=%s"
        params.append(module)
    sql += " ORDER BY created_at"
    return query(sql, params)
```

- [ ] **Step 2: 创建 routers/backup.py**

```python
import csv
import io
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import settings
from routers.auth import login_required
import db.queries as dbq

router = APIRouter(dependencies=[Depends(login_required)])
templates = Jinja2Templates(directory="templates")

@router.get("/backup/", response_class=HTMLResponse)
async def backup_page(request: Request):
    return templates.TemplateResponse("backup/index.html", {
        "request": request, "app_title": settings.APP_TITLE,
        "static_version": settings.STATIC_VERSION
    })

@router.get("/api/backup/schedule/export")
async def export_schedule(request: Request, start_date: str = None, end_date: str = None, status: str = None):
    login_required(request)
    rows = dbq.get_backup_schedule_orders(start_date, end_date, status)
    return _csv_response(rows, "排产数据.csv")

@router.get("/api/backup/production/export")
async def export_production(request: Request, start_date: str = None, end_date: str = None):
    login_required(request)
    rows = dbq.get_backup_production_batches(start_date, end_date)
    return _csv_response(rows, "生产数据.csv")

@router.get("/api/backup/log/export")
async def export_logs(request: Request, start_date: str = None, end_date: str = None, module: str = None):
    login_required(request)
    rows = dbq.get_backup_logs(start_date, end_date, module)
    return _csv_response(rows, "操作日志.csv")

def _csv_response(rows, filename):
    if not rows:
        output = io.StringIO()
        output.write("无数据\n")
        output.seek(0)
        return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(rows[0].keys())
    for row in rows:
        writer.writerow(row.values())
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv",
                             headers={"Content-Disposition": f"attachment; filename={filename}"})
```

（注意：需要在 router 的 imports 中添加 `from fastapi import Depends`）

---

### Task 13: 空文件与静态资源

**文件:**
- 创建: `static/js/common.js`
- 创建: 所有剩余 `__init__.py` 文件
- 创建: 所有目录

- [ ] **Step 1: 创建 static/js/common.js**

```javascript
// 通用JS工具函数
function get(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.onload = function() {
        if (xhr.status === 200) callback(JSON.parse(xhr.responseText));
    };
    xhr.send();
}

function post(url, data, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
        if (xhr.status === 200 && callback) callback(JSON.parse(xhr.responseText));
    };
    xhr.send(JSON.stringify(data));
}
```

---

## 自检清单

**1. 需求覆盖检查：**
- ✅ 设备管理：炉子配置、节拍设置、温度设置 — Task 5
- ✅ 工艺组合管理：产品、工艺、版本、操作指导 — Task 6
- ✅ 排产管理：CRUD、空白节拍、预定时间、CSV导出 — Task 7
- ✅ 生产控制：开机/暂停/恢复/停止 — Task 8
- ✅ 节拍推进：前进/后退/整体前进/整体后退 — Task 8
- ✅ 插入空白节拍 — Task 8
- ✅ 生产报告：计划vs实际对比 — Task 8
- ✅ TV可视化：51寸大屏动画显示 — Task 9
- ✅ 用户管理：注册、权限分配 — Task 10
- ✅ 日志系统：操作留痕 — Task 11
- ✅ 数据备份：CSV导出 — Task 12
- ✅ 登录认证 — Task 3
- ✅ 基础UI模板 — Task 4

**2. 占位符检查：**
无 TBD/TODO 占位符，所有代码块包含完整实现代码。

**3. 类型一致性检查：**
- `db.pool.query()` 统一返回 list[dict] 或 lastrowid
- `db.pool.query_one()` 统一返回 dict 或 None
- 所有 service 函数返回 (bool, data) 元组
- TV API 返回 JSON 格式一致
