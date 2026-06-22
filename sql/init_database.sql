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

-- ============================================================
-- 初始数据
-- ============================================================

-- 炉子定义
INSERT IGNORE INTO furnaces (id, name, code, section_count, section_minutes, sort_order) VALUES
(1, '发泡炉', 'FOAM', 18, 16, 1),
(2, '固化炉', 'CURE', 52, 16, 2);

-- 发泡炉18节
INSERT IGNORE INTO furnace_sections (furnace_id, section_order, section_name)
SELECT 1, n, CONCAT('发泡炉第', n, '节') FROM (
    SELECT 1 AS n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5
    UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
    UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15
    UNION SELECT 16 UNION SELECT 17 UNION SELECT 18
) AS nums
WHERE NOT EXISTS (SELECT 1 FROM furnace_sections WHERE furnace_id = 1 AND section_order = nums.n);

-- 固化炉52节
INSERT IGNORE INTO furnace_sections (furnace_id, section_order, section_name)
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
) AS nums
WHERE NOT EXISTS (SELECT 1 FROM furnace_sections WHERE furnace_id = 2 AND section_order = nums.n);

-- 系统配置
INSERT IGNORE INTO system_config (config_key, config_value, description) VALUES
('tv_refresh_interval', '10', '电视大屏刷新间隔(秒)'),
('default_section_minutes', '16', '默认每节拍分钟数');

-- 默认生产运行记录（两个炉子的初始状态）
INSERT IGNORE INTO production_runs (furnace_id, status) VALUES (1, 'idle'), (2, 'idle');
