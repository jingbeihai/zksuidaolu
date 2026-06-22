# 中科恒泰隧道炉排产与生产可视化系统 — 架构设计文档

> **适用对象：** 全栈开发工程师
> **技术栈：** Python FastAPI + Jinja2 + MySQL 8 + 纯前端可视化
> **日期：** 2026-06-17

---

## 1. 系统概述

### 1.1 项目背景

隧道炉排产与生产可视化系统，管理两段炉子的生产全过程：

- **发泡炉**：18 节，每节 16 分钟
- **固化炉**：52 节，每节 16 分钟

包含：设备管理 → 工艺组合管理 → 排产管理 → 生产控制 → 可视化大屏 → 生产报告 的完整闭环。

### 1.2 核心业务流程

```
工艺组合管理 ──→ 排产管理 ──→ 生产控制 ──→ 生产报告
     ↑                ↑              ↑
  (设置产品工艺)  (选择工艺+批号)   (节拍推进)
     │                │              │
     └────────────────┴──────────────┘
                      ↓
              TV可视化大屏 ←── 实时数据推送
```

### 1.3 运行环境

- **服务器**：工控机（Windows 10/11），离线运行
- **浏览器**：PC端操作界面 + 51寸电视大屏（Kiosk模式全屏显示）
- **Python 3.10+**，使用 `uvicorn` 自启动

---

## 2. 技术选型

| 层次 | 技术 | 说明 |
|------|------|------|
| **后端框架** | FastAPI | 异步高性能，自动API文档 |
| **ORM/数据库** | PyMySQL + 连接池 | 参照现有项目模式，原始SQL |
| **模板引擎** | Jinja2 | 服务端渲染PC管理界面 |
| **前端** | 纯 HTML/CSS/JS | 无需前端框架，离线可用 |
| **TV可视化** | DOM动画 + CSS3 + Canvas | 10秒轮询刷新 |
| **认证** | bcrypt + 签名Session | SessionMiddleware |
| **日志** | RotatingFileHandler | 按模块分类记录 |
| **导出** | CSV (Python csv模块) | 数据备份与报告导出 |
| **配置** | .env + python-dotenv | 数据库连接、密钥等 |

### 2.1 技术选型理由

- **FastAPI 而非 Flask**：相比参考项目使用的 FastAPI 更现代化，天然支持异步，自带 Swagger 文档方便调试
- **纯前端**：离线工控机无需联网CDN，所有资源本地加载；无需 Vue/React 减少体积和复杂度
- **原始 SQL**：参考现有项目模式，保持一致性；业务逻辑复杂，ORM 反而增加理解成本
- **轮询而非 WebSocket**：工控机环境下轮询更稳定可靠，10秒间隔对服务器几乎无压力

---

## 3. 系统架构

### 3.1 总体架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Middleware 层                              │  │
│  │  SessionMiddleware | AuthGuard | LoggingMiddleware          │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐ │
│  │ 设备管理  │ │ 工艺管理  │ │ 排产管理  │ │ 生产控制  │ │用户管理│ │
│  │  Router   │ │  Router  │ │  Router  │ │  Router  │ │ Router │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────────────┐    │
│  │ 日志系统  │ │ 数据备份  │ │   TV可视化（独立前端页面）      │    │
│  │  Router   │ │  Router  │ │   /tv  → 大屏展示页面          │    │
│  └──────────┘ └──────────┘ └──────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                  Database Layer                             │  │
│  │        PyMySQL 连接池 (LifoQueue, max 8)                   │  │
│  └────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────┤
│                       MySQL Database 8.0                         │
│                    host:101.43.84.176:3306/zksuidaolu2            │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 模块划分

#### 模块一：设备管理 (`routers/device.py`)
- 功能：设置两段炉的节拍数，每节拍的独立温度，或阶段升温区间
- 页面：`templates/device/` — 设备列表、节拍配置、温度设置

#### 模块二：工艺组合管理 (`routers/process.py`)
- 功能：产品名称、工艺名称、工艺版本号、操作指导等
- 页面：`templates/process/` — 产品列表、工艺卡片、版本管理

#### 模块三：排产管理 (`routers/schedule.py`)
- 功能：选择工艺组合，输入数量、批号、空白节拍数、预定时间；排产单导出CSV
- 页面：`templates/schedule/` — 排产表单、排产列表、甘特图

#### 模块四：生产控制 (`routers/production.py`)
- 功能：开机/暂停/恢复/停止，插入空白节拍；节拍推进（前/后/整体前/整体后）；生产报告
- 页面：`templates/production/` — 控制面板、节拍操作、报告查看

#### 模块五：可视化大屏 (`routers/tv.py`)
- 功能：51寸电视大屏动画显示批次位置、温度、批号
- 页面：`templates/tv/` — 大屏HTML

#### 模块六：用户管理 (`routers/user.py`)
- 功能：用户名/真实姓名注册，模块权限勾选
- 页面：`templates/user/` — 用户列表、权限分配

#### 模块七：日志系统 (`routers/log.py`)
- 功能：所有模块的操作记录留痕
- 页面：`templates/log/` — 日志查看、筛选

#### 模块八：数据备份 (`routers/backup.py`)
- 功能：排产/生产/日志数据筛选和下载CSV
- 页面：`templates/backup/` — 备份管理

---

## 4. 数据库设计

### 4.1 整体 E-R 关系

```
users ──→ operation_logs
  │
  ├── (权限控制所有模块)
  
furnaces ──→ furnace_sections ──→ temperature_settings

products ──→ process_versions ──→ process_steps

schedule_orders ──→ schedule_order_items

production_runs ──→ production_batches ──→ batch_section_logs

production_reports
```

### 4.2 表结构详细设计

#### 4.2.1 设备管理

##### `furnaces` — 炉子定义表

```sql
CREATE TABLE furnaces (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL COMMENT '炉子名称: 发泡炉/固化炉',
    code VARCHAR(20) NOT NULL UNIQUE COMMENT '编码: FOAM/CURE',
    section_count INT NOT NULL COMMENT '节拍数量: 18/52',
    section_minutes INT NOT NULL DEFAULT 16 COMMENT '每节分钟数',
    sort_order INT NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO furnaces (name, code, section_count, section_minutes, sort_order) VALUES
('发泡炉', 'FOAM', 18, 16, 1),
('固化炉', 'CURE', 52, 16, 2);
```

##### `furnace_sections` — 节拍定义表

```sql
CREATE TABLE furnace_sections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    furnace_id INT NOT NULL,
    section_order INT NOT NULL COMMENT '节拍序号: 1-18 或 1-52',
    section_name VARCHAR(50) DEFAULT NULL COMMENT '节拍名称: 预热区/高温区等',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    FOREIGN KEY (furnace_id) REFERENCES furnaces(id),
    UNIQUE KEY uk_furnace_section (furnace_id, section_order)
);
```

##### `temperature_settings` — 温度设置表

```sql
CREATE TABLE temperature_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    furnace_id INT NOT NULL,
    -- 支持独立节拍设置
    section_id INT DEFAULT NULL COMMENT 'NULL表示使用区间设置',
    target_temp DECIMAL(6,1) NOT NULL COMMENT '目标温度',
    -- 支持区间设置（阶段升温）
    zone_start INT DEFAULT NULL COMMENT '区间起始节拍序号',
    zone_end INT DEFAULT NULL COMMENT '区间结束节拍序号',
    zone_name VARCHAR(50) DEFAULT NULL COMMENT '区间名称: 预热区/高温区',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (furnace_id) REFERENCES furnaces(id),
    FOREIGN KEY (section_id) REFERENCES furnace_sections(id)
);
```

> **设计说明**：temperature_settings 支持两种模式：
> 1. **独立模式** — 为每个节拍设置独立温度（section_id 不为 NULL）
> 2. **区间模式** — 设置一段区间的统一温度（zone_start/zone_end 不为 NULL）

#### 4.2.2 工艺组合管理

##### `products` — 产品表

```sql
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '产品名称',
    code VARCHAR(50) NOT NULL UNIQUE COMMENT '产品编码',
    description TEXT DEFAULT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

##### `processes` — 工艺组合表

```sql
CREATE TABLE processes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    process_name VARCHAR(100) NOT NULL COMMENT '工艺名称',
    version_no VARCHAR(20) NOT NULL COMMENT '版本号: V1.0, V2.0',
    is_current TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否为当前版本',
    status ENUM('draft', 'published', 'archived') NOT NULL DEFAULT 'draft',
    created_by INT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    UNIQUE KEY uk_product_version (product_id, process_name, version_no)
);
```

##### `process_steps` — 工艺步骤/操作指导表

```sql
CREATE TABLE process_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    process_id INT NOT NULL,
    step_order INT NOT NULL COMMENT '步骤序号',
    section_start INT NOT NULL COMMENT '起始节拍',
    section_end INT NOT NULL COMMENT '结束节拍',
    target_temp DECIMAL(6,1) NOT NULL COMMENT '目标温度',
    operation_guide TEXT DEFAULT NULL COMMENT '操作指导',
    key_phenomena TEXT DEFAULT NULL COMMENT '关键现象',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (process_id) REFERENCES processes(id),
    UNIQUE KEY uk_process_step (process_id, step_order)
);
```

#### 4.2.3 排产管理

##### `schedule_orders` — 排产单主表

```sql
CREATE TABLE schedule_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(50) NOT NULL UNIQUE COMMENT '排产单号',
    process_id INT NOT NULL COMMENT '关联工艺组合',
    product_id INT NOT NULL,
    batch_no VARCHAR(100) NOT NULL COMMENT '批号',
    quantity INT NOT NULL COMMENT '数量',
    blank_sections INT NOT NULL DEFAULT 0 COMMENT '空白节拍数',
    scheduled_time DATETIME NOT NULL COMMENT '预定排产时间',
    assigned_furnace_id INT DEFAULT NULL COMMENT '指定生产炉子',
    status ENUM('pending', 'in_production', 'completed', 'cancelled') NOT NULL DEFAULT 'pending',
    notes TEXT DEFAULT NULL COMMENT '备注',
    created_by INT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (process_id) REFERENCES processes(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (assigned_furnace_id) REFERENCES furnaces(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

##### `schedule_order_items` — 排产单明细表（批次拆分）

```sql
CREATE TABLE schedule_order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    schedule_order_id INT NOT NULL,
    batch_label VARCHAR(50) NOT NULL COMMENT '批次标签: P01, P02...',
    batch_seq INT NOT NULL COMMENT '批次序号',
    quantity INT NOT NULL COMMENT '本批次数量',
    entry_section INT DEFAULT NULL COMMENT '入炉节拍序号',
    status ENUM('pending', 'in_furnace', 'completed') NOT NULL DEFAULT 'pending',
    FOREIGN KEY (schedule_order_id) REFERENCES schedule_orders(id)
);
```

#### 4.2.4 生产控制

##### `production_runs` — 生产运行记录

```sql
CREATE TABLE production_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    furnace_id INT NOT NULL COMMENT '哪个炉在生产',
    status ENUM('idle', 'running', 'paused', 'stopped') NOT NULL DEFAULT 'idle',
    current_order_id INT DEFAULT NULL COMMENT '当前执行的排产单',
    current_section INT DEFAULT 1 COMMENT '当前推进到第几节',
    started_at DATETIME DEFAULT NULL,
    paused_at DATETIME DEFAULT NULL,
    stopped_at DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (furnace_id) REFERENCES furnaces(id),
    FOREIGN KEY (current_order_id) REFERENCES schedule_orders(id)
);

INSERT INTO production_runs (furnace_id, status) VALUES 
(1, 'idle'), (2, 'idle');
```

##### `production_batches` — 批次在炉记录

```sql
CREATE TABLE production_batches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    production_run_id INT NOT NULL,
    schedule_order_id INT NOT NULL,
    schedule_order_item_id INT DEFAULT NULL,
    batch_label VARCHAR(50) NOT NULL COMMENT 'P01, P02...',
    product_name VARCHAR(100) NOT NULL,
    process_name VARCHAR(100) NOT NULL,
    current_section INT NOT NULL DEFAULT 1 COMMENT '当前所在节拍',
    entry_section INT NOT NULL COMMENT '入炉节拍',
    status ENUM('in_furnace', 'completed') NOT NULL DEFAULT 'in_furnace',
    entered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME DEFAULT NULL,
    FOREIGN KEY (production_run_id) REFERENCES production_runs(id),
    FOREIGN KEY (schedule_order_id) REFERENCES schedule_orders(id)
);
```

##### `batch_section_logs` — 批次节拍日志（实际生产数据）

```sql
CREATE TABLE batch_section_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT NOT NULL,
    furnace_id INT NOT NULL,
    section_order INT NOT NULL COMMENT '节拍序号',
    target_temp DECIMAL(6,1) NOT NULL COMMENT '目标温度',
    actual_temp DECIMAL(6,1) DEFAULT NULL COMMENT '实际温度（实时采集）',
    entered_at DATETIME NOT NULL COMMENT '进入时间',
    exited_at DATETIME DEFAULT NULL COMMENT '离开时间',
    actual_duration_min INT DEFAULT NULL COMMENT '实际停留分钟',
    FOREIGN KEY (batch_id) REFERENCES production_batches(id),
    FOREIGN KEY (furnace_id) REFERENCES furnaces(id)
);
```

##### `blank_section_logs` — 空白节拍记录

```sql
CREATE TABLE blank_section_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    production_run_id INT NOT NULL,
    furnace_id INT NOT NULL,
    section_order INT NOT NULL COMMENT '节拍序号',
    inserted_at DATETIME NOT NULL,
    removed_at DATETIME DEFAULT NULL,
    FOREIGN KEY (production_run_id) REFERENCES production_runs(id),
    FOREIGN KEY (furnace_id) REFERENCES furnaces(id)
);
```

#### 4.2.5 生产报告

##### `production_reports` — 生产报告表

```sql
CREATE TABLE production_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    schedule_order_id INT NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    batch_no VARCHAR(100) NOT NULL,
    batch_label VARCHAR(50) NOT NULL,
    furnace_name VARCHAR(50) NOT NULL COMMENT '发泡炉/固化炉',
    planned_sections INT NOT NULL COMMENT '计划节拍数',
    actual_sections INT NOT NULL COMMENT '实际节拍数',
    planned_duration_min INT NOT NULL COMMENT '计划时长',
    actual_duration_min INT NOT NULL COMMENT '实际时长',
    entry_time DATETIME NOT NULL COMMENT '入炉时间',
    exit_time DATETIME NOT NULL COMMENT '出炉时间',
    avg_temp DECIMAL(6,1) DEFAULT NULL COMMENT '平均温度',
    max_temp DECIMAL(6,1) DEFAULT NULL COMMENT '最高温度',
    min_temp DECIMAL(6,1) DEFAULT NULL COMMENT '最低温度',
    status ENUM('completed', 'partial', 'abnormal') NOT NULL DEFAULT 'completed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_order_id) REFERENCES schedule_orders(id)
);
```

##### `report_compare_data` — 报告对比数据

```sql
CREATE TABLE report_compare_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    report_id INT NOT NULL,
    section_order INT NOT NULL,
    planned_temp DECIMAL(6,1) NOT NULL COMMENT '计划温度',
    actual_temp DECIMAL(6,1) DEFAULT NULL COMMENT '实际温度',
    planned_duration INT NOT NULL COMMENT '计划停留(分钟)',
    actual_duration INT DEFAULT NULL COMMENT '实际停留(分钟)',
    temp_diff DECIMAL(6,1) GENERATED ALWAYS AS (actual_temp - planned_temp) STORED,
    duration_diff INT GENERATED ALWAYS AS (actual_duration - planned_duration) STORED,
    FOREIGN KEY (report_id) REFERENCES production_reports(id)
);
```

#### 4.2.6 用户管理

##### `users` — 用户表

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    real_name VARCHAR(100) NOT NULL COMMENT '真实姓名',
    is_admin TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    permissions JSON DEFAULT NULL COMMENT '权限配置: {"device":1,"process":1,"schedule":0,...}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 默认管理员
INSERT INTO users (username, password_hash, real_name, is_admin, permissions) VALUES
('admin', '$2b$12$...', '系统管理员', 1, '{}');
```

#### 4.2.7 日志系统

##### `operation_logs` — 操作日志表

```sql
CREATE TABLE operation_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    username VARCHAR(50) NOT NULL,
    real_name VARCHAR(100) NOT NULL,
    module VARCHAR(50) NOT NULL COMMENT '模块: device/process/schedule/production/user/log/backup',
    action VARCHAR(50) NOT NULL COMMENT '操作: create/update/delete/start/stop/export',
    target_type VARCHAR(50) DEFAULT NULL COMMENT '对象类型',
    target_id INT DEFAULT NULL COMMENT '对象ID',
    target_label VARCHAR(200) DEFAULT NULL COMMENT '对象描述',
    detail TEXT DEFAULT NULL COMMENT '详细信息(JSON)',
    ip_address VARCHAR(45) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_module (module),
    INDEX idx_user (user_id),
    INDEX idx_created (created_at)
);
```

#### 4.2.8 系统配置

##### `system_config` — 系统配置表

```sql
CREATE TABLE system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description VARCHAR(200) DEFAULT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO system_config (config_key, config_value, description) VALUES
('tv_refresh_interval', '10', '电视大屏刷新间隔(秒)'),
('auto_advance_enabled', '1', '是否自动推进节拍'),
('default_section_minutes', '16', '默认每节拍分钟数');
```

### 4.3 数据库初始化脚本

完整的建库建表脚本将保存在 `sql/init_database.sql` 中。

---

## 5. 目录结构

```
zk-tunnel-furnace/
├── main.py                  # FastAPI 入口
├── .env                     # 环境配置
├── .env.example             # 配置模板
├── requirements.txt         # Python 依赖
├── settings.py              # 全局配置
├── logging_config.py        # 日志配置
│
├── db/
│   ├── __init__.py
│   ├── pool.py              # 数据库连接池
│   └── queries/             # 按模块拆分SQL查询
│       ├── device_queries.py
│       ├── process_queries.py
│       ├── schedule_queries.py
│       ├── production_queries.py
│       ├── user_queries.py
│       └── log_queries.py
│
├── routers/
│   ├── __init__.py
│   ├── auth.py              # 登录/登出路由
│   ├── device.py            # 设备管理
│   ├── process.py           # 工艺组合管理
│   ├── schedule.py          # 排产管理
│   ├── production.py        # 生产控制
│   ├── tv.py                # TV可视化大屏
│   ├── user.py              # 用户管理
│   ├── log.py               # 日志系统
│   └── backup.py            # 数据备份
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py      # 认证逻辑
│   ├── production_service.py # 生产控制核心逻辑
│   └── report_service.py    # 报告生成逻辑
│
├── middleware/
│   ├── __init__.py
│   ├── auth_middleware.py    # 权限守卫
│   └── log_middleware.py     # 操作日志记录
│
├── static/
│   ├── css/
│   │   ├── flat.css         # PC端界面样式
│   │   ├── tv.css           # TV大屏样式
│   │   └── tv-temp.css      # 温度动画样式
│   ├── js/
│   │   ├── tv.js            # TV大屏主逻辑
│   │   ├── tv-animation.js  # 节拍推进动画
│   │   ├── production.js    # 生产控制交互
│   │   └── common.js        # 通用函数
│   └── img/                 # 静态图片
│
├── templates/
│   ├── base.html            # PC端基础模板
│   ├── login.html           # 登录页
│   ├── nav.html             # 导航栏
│   ├── device/
│   │   ├── list.html        # 设备列表
│   │   └── temp_settings.html # 温度设置
│   ├── process/
│   │   ├── product_list.html
│   │   ├── process_list.html
│   │   └── process_edit.html
│   ├── schedule/
│   │   ├── list.html
│   │   └── form.html
│   ├── production/
│   │   ├── control.html     # 控制面板
│   │   ├── section_ops.html # 节拍操作
│   │   └── report.html      # 生产报告
│   ├── tv/
│   │   └── display.html     # 电视大屏
│   ├── user/
│   │   ├── list.html
│   │   └── form.html
│   ├── log/
│   │   └── list.html
│   └── backup/
│       └── index.html
│
├── sql/
│   └── init_database.sql    # 数据库初始化脚本
│
├── logs/                    # 日志文件目录
│
└── docs/
    └── superpowers/
        ├── specs/           # 设计文档
        └── plans/           # 实施计划
```

---

## 6. API 路由设计

### 6.1 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/login` | 登录页面/提交 |
| GET | `/logout` | 退出登录 |

### 6.2 设备管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/device/` | 设备管理首页 |
| POST | `/api/device/furnace/{id}/temp` | 设置炉子温度方案 |
| GET | `/api/device/furnace/{id}/temp` | 获取温度方案 |
| POST | `/api/device/furnace/{id}/sections` | 设置节拍数 |

### 6.3 工艺管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/process/` | 工艺组合首页 |
| POST | `/api/process/product` | 新增产品 |
| POST | `/api/process/process` | 新增工艺组合 |
| POST | `/api/process/process/{id}/step` | 添加工艺步骤 |
| GET | `/api/process/process/{id}` | 获取工艺详情 |
| POST | `/api/process/process/{id}/publish` | 发布版本 |

### 6.4 排产管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/schedule/` | 排产管理首页 |
| POST | `/api/schedule/order` | 新增排产单 |
| GET | `/api/schedule/orders` | 排产单列表 |
| POST | `/api/schedule/order/{id}/cancel` | 取消排产单 |
| GET | `/api/schedule/order/{id}/export` | 导出排产单CSV |

### 6.5 生产控制

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/production/` | 生产控制首页 |
| POST | `/api/production/run/{furnace_id}/start` | 开机 |
| POST | `/api/production/run/{furnace_id}/pause` | 暂停 |
| POST | `/api/production/run/{furnace_id}/resume` | 恢复 |
| POST | `/api/production/run/{furnace_id}/stop` | 停止 |
| POST | `/api/production/batch/{id}/advance` | 批次前进一节 |
| POST | `/api/production/batch/{id}/retreat` | 批次后退一节 |
| POST | `/api/production/batch/advance-all` | 所有批次前进一节 |
| POST | `/api/production/batch/retreat-all` | 所有批次后退一节 |
| POST | `/api/production/blank-section/insert` | 插入空白节拍 |
| GET | `/api/production/report/{order_id}` | 查看生产报告 |

### 6.6 TV可视化

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/tv` | TV大屏主页 |
| GET | `/api/tv/furnace-status` | 获取炉子实时状态 |
| GET | `/api/tv/schedule-queue` | 获取待生产队列 |

### 6.7 用户管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/user/` | 用户管理首页 |
| POST | `/api/user` | 新增用户 |
| PUT | `/api/user/{id}` | 编辑用户 |
| POST | `/api/user/{id}/permissions` | 设置权限 |

### 6.8 日志

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/log/` | 日志查看页面 |
| GET | `/api/logs` | 日志列表（分页筛选） |

### 6.9 数据备份

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/backup/` | 备份管理页面 |
| GET | `/api/backup/schedule/export` | 导出排产数据CSV |
| GET | `/api/backup/production/export` | 导出生产数据CSV |
| GET | `/api/backup/log/export` | 导出日志CSV |

---

## 7. TV 可视化大屏数据流

```
┌──────────────────────┐    10秒轮询      ┌──────────────────────┐
│    TV 大屏浏览器      │ ──────────────→  │  FastAPI /api/tv/*   │
│  (51寸 1920×1080)    │ ←──────────────  │                      │
│                      │    JSON响应       │  查询数据库实时状态    │
│  DOM渲染:             │                  │                      │
│  • 发泡炉18节拍网格   │                  │  ┌────────────────┐  │
│  • 固化炉52节拍网格   │                  │  │ production_    │  │
│  • 批次位置+动画      │                  │  │ batches 表     │  │
│  • 温度显示           │                  │  │ schedule_      │  │
│  • 排产队列           │                  │  │ orders 表      │  │
│  • 时钟              │                  │  └────────────────┘  │
└──────────────────────┘                  └──────────────────────┘
```

### 7.1 API 响应格式示例

**GET /api/tv/furnace-status**

```json
{
  "furnaces": [
    {
      "id": 1,
      "name": "发泡炉",
      "section_count": 18,
      "running": true,
      "sections": [
        {
          "order": 1,
          "target_temp": 85.0,
          "has_product": false,
          "batch": null
        },
        {
          "order": 6,
          "target_temp": 140.0,
          "has_product": true,
          "batch": {
            "label": "P01",
            "product_name": "三元材料A型",
            "progress": 60
          }
        }
      ]
    },
    {
      "id": 2,
      "name": "固化炉",
      "section_count": 52,
      "section_minutes": 16,
      "running": true,
      "sections": [...]
    }
  ]
}
```

**GET /api/tv/schedule-queue**

```json
{
  "queue": [
    {
      "order_no": "P20260617-001",
      "batch_label": "P03",
      "product_name": "三元材料C型",
      "quantity": 500,
      "furnace_name": "发泡炉",
      "scheduled_time": "2026-06-17T14:45:00",
      "status": "ready"
    }
  ],
  "summary": {
    "pending_count": 6,
    "total_quantity": 3950,
    "in_production": 2
  }
}
```

---

## 8. 生产控制核心逻辑

### 8.1 节拍推进算法

```
批次前进一节:
  1. 验证批次 current_section < furnace_section_count
  2. 记录当前节拍完成时间到 batch_section_logs
  3. 更新生产批次 current_section + 1
  4. 创建新节拍的 batch_section_logs 记录
  5. 如果 current_section == furnace_section_count → 状态标记为 completed
  6. 记录操作日志

批次后退一节:
  1. 验证批次 current_section > 1
  2. 删除当前节拍的 batch_section_logs (未完成记录)
  3. 更新生产批次 current_section - 1
  4. 如果回退到空白节拍位置，恢复上一节拍
  5. 记录操作日志

整体前进/后退:
  1. 获取所有正在该炉生产的批次
  2. 按 current_section 排序
  3. 逐个执行前进/后退操作
```

### 8.2 开机流程

```
生产控制 → 开机:
  1. 检查炉子状态是否为 idle
  2. 从排产队列取下一个 pending 状态的排产单
  3. 创建 production_batches 记录
  4. 更新生产运行状态为 running
  5. 更新排产单状态为 in_production
  6. TV大屏自动刷新显示新批次
```

### 8.3 插入空白节拍

```
插入空白节拍:
  1. 指定插入位置 section_order
  2. 该位置之后所有批次 current_section + 1
  3. 创建 blank_section_logs 记录
  4. 空白节拍在TV上显示为灰色
  5. furnace_section_count 临时 +1 (或标记为特殊空白)
```

### 8.4 生产报告生成

```
生产完成 → 生成报告:
  1. 对比 schedule_order (计划) 和 batch_section_logs (实际)
  2. 计算每个节拍的：温度偏差、时长偏差
  3. 统计：平均温度、最高/最低温度、总时长
  4. 生成 report_compare_data 逐节对比
  5. 页面展示对比表格和曲线图
```

---

## 9. 权限设计

### 9.1 权限列表

| 模块 | 权限标识 | 说明 |
|------|---------|------|
| 设备管理 | `device` | 查看/编辑设备配置 |
| 工艺组合 | `process` | 管理产品和工艺 |
| 排产管理 | `schedule` | 排产单CRUD和导出 |
| 生产控制 | `production` | 开机/暂停/节拍操作 |
| 用户管理 | `user` | 用户CRUD和权限分配 |
| 日志系统 | `log` | 查看操作日志 |
| 数据备份 | `backup` | 导出备份数据 |
| TV大屏 | `tv` | 仅查看（无需权限） |

### 9.2 权限存储

用户权限以 JSON 格式存储在 `users.permissions` 字段中：

```json
{
  "device": 1,
  "process": 1,
  "schedule": 1,
  "production": 0,
  "user": 0,
  "log": 1,
  "backup": 0
}
```

其中 `1` 表示有权限，`0` 表示无权限。管理员（`is_admin=1`）忽略权限检查。

---

## 10. 日志系统设计

### 10.1 日志记录规则

每次用户执行关键操作时触发日志记录：

| 模块 | 记录场景 |
|------|---------|
| 设备管理 | 创建/修改/删除炉子配置、温度设置 |
| 工艺管理 | 创建/修改/发布/归档产品工艺 |
| 排产管理 | 创建/取消/导出排产单 |
| 生产控制 | 开机/暂停/恢复/停止/节拍推进/插入空白 |
| 用户管理 | 创建/修改/删除用户、修改权限 |
| 数据备份 | 导出CSV |
| 系统 | 登录/登出 |

### 10.2 日志记录中间件

使用 FastAPI Middleware 或装饰器模式实现自动日志记录：

```python
# 示例：装饰器模式
@log_operation(module='schedule', action='create')
def create_schedule_order(...):
    ...
```

---

## 11. 安全设计

- **密码存储**：bcrypt 哈希，不存储明文
- **会话管理**：签名 Cookie 会话（itsdangerous），8小时过期
- **权限校验**：每个路由入口做权限守卫检查
- **SQL注入防护**：所有参数化查询（cursor.execute 使用 %s 占位符）
- **XSS防护**：Jinja2 默认自动转义
- **离线部署**：无需公网访问，工控机本地运行

---

## 12. 数据库表关系总结

```
furnaces (1) ──→ furnace_sections (N)
furnaces (1) ──→ temperature_settings (N)
furnaces (1) ──→ production_runs (N)

products (1) ──→ processes (N)
processes (1) ──→ process_steps (N)

processes (1) ──→ schedule_orders (N)
schedule_orders (1) ──→ schedule_order_items (N)

schedule_orders (1) ──→ production_batches (N)
production_runs (1) ──→ production_batches (N)
production_batches (1) ──→ batch_section_logs (N)
production_runs (1) ──→ blank_section_logs (N)

schedule_orders (1) ──→ production_reports (1)
production_reports (1) ──→ report_compare_data (N)

users (1) ──→ operation_logs (N)
users (1) ──→ schedule_orders (N)
```
