"""数据库查询函数"""
import logging
from db.pool import query, query_one

logger = logging.getLogger(__name__)

# ==============================
# Auth / User
# ==============================
def get_user_by_username(username):
    return query_one("SELECT * FROM users WHERE username = %s AND is_active = 1", (username,))

def get_user_by_id(user_id):
    return query_one("SELECT * FROM users WHERE id = %s", (user_id,))

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

# ==============================
# Device / Furnace
# ==============================
def get_furnaces():
    return query("SELECT * FROM furnaces WHERE is_active = 1 ORDER BY sort_order")

def get_furnace(furnace_id):
    return query_one("SELECT * FROM furnaces WHERE id = %s", (furnace_id,))

def get_furnace_sections(furnace_id):
    return query("SELECT * FROM furnace_sections WHERE furnace_id = %s AND is_active = 1 ORDER BY section_order", (furnace_id,))

def get_temp_settings(furnace_id):
    return query("SELECT * FROM temperature_settings WHERE furnace_id = %s AND is_active = 1", (furnace_id,))

def save_temp_settings(furnace_id, settings_list):
    query("UPDATE temperature_settings SET is_active = 0 WHERE furnace_id = %s", (furnace_id,))
    sections = get_furnace_sections(furnace_id)
    section_map = {s["section_order"]: s["id"] for s in sections}
    for s in settings_list:
        sid = s.get("section_id")
        zone_start = s.get("zone_start")
        zone_end = s.get("zone_end")
        # 区间模式：展开为每个节拍的独立记录
        if zone_start and zone_end and not sid:
            for order in range(int(zone_start), int(zone_end) + 1):
                actual_sid = section_map.get(order)
                if actual_sid:
                    query("""INSERT INTO temperature_settings (furnace_id, section_id, target_temp, zone_start, zone_end, zone_name)
                             VALUES (%s, %s, %s, %s, %s, %s)""",
                          (furnace_id, actual_sid, s.get("target_temp"),
                           zone_start, zone_end, s.get("zone_name")))
        else:
            query("""INSERT INTO temperature_settings (furnace_id, section_id, target_temp, zone_start, zone_end, zone_name)
                     VALUES (%s, %s, %s, %s, %s, %s)""",
                  (furnace_id, sid, s.get("target_temp"),
                   s.get("zone_start"), s.get("zone_end"), s.get("zone_name")))

def update_furnace_config(furnace_id, section_count, section_minutes):
    query("UPDATE furnaces SET section_count=%s, section_minutes=%s WHERE id=%s",
          (section_count, section_minutes, furnace_id))

# ==============================
# Process / Product
# ==============================
def get_products():
    return query("SELECT * FROM products WHERE is_active = 1 ORDER BY name")

def create_product(name, code, description=""):
    return query("INSERT INTO products (name, code, description) VALUES (%s, %s, %s)",
                 (name, code, description))

def get_processes(product_id=None):
    if product_id:
        return query("SELECT p.*, pr.name as product_name FROM processes p JOIN products pr ON p.product_id=pr.id WHERE p.product_id=%s AND p.status != 'archived' ORDER BY p.created_at DESC", (product_id,))
    return query("SELECT p.*, pr.name as product_name FROM processes p JOIN products pr ON p.product_id=pr.id WHERE p.status != 'archived' ORDER BY p.created_at DESC")

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

# ==============================
# Schedule Orders
# ==============================
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

def get_tv_schedule_orders():
    """TV 右侧待生产排产单：pending + in_production，含在炉/已完成批次数"""
    return query("""SELECT o.*, p.name AS product_name, ps.process_name,
                    (SELECT COUNT(*) FROM production_batches b
                     WHERE b.schedule_order_id=o.id AND b.status='in_furnace') AS in_furnace,
                    (SELECT COUNT(*) FROM production_batches b
                     WHERE b.schedule_order_id=o.id AND b.status='completed') AS completed
                    FROM schedule_orders o
                    JOIN products p ON o.product_id=p.id
                    JOIN processes ps ON o.process_id=ps.id
                    WHERE o.status IN ('pending', 'in_production')
                    ORDER BY o.scheduled_time ASC""")

def generate_order_no():
    import datetime
    prefix = datetime.datetime.now().strftime("P%Y%m%d-")
    row = query_one("SELECT COUNT(*) as cnt FROM schedule_orders WHERE order_no LIKE %s", (prefix + "%",))
    return prefix + str(row["cnt"] + 1).zfill(3)

# ==============================
# Production / Batch
# ==============================
def get_production_run(furnace_id):
    return query_one("SELECT * FROM production_runs WHERE furnace_id=%s", (furnace_id,))

def update_run_status(run_id, status):
    query("UPDATE production_runs SET status=%s WHERE id=%s", (status, run_id))

def get_batches_in_furnace(furnace_id):
    """按 current_furnace_id 查询在炉批次"""
    return query("SELECT * FROM production_batches WHERE current_furnace_id=%s AND status='in_furnace' ORDER BY current_section", (furnace_id,))

def get_all_active_batches():
    """获取所有在炉批次"""
    return query("SELECT * FROM production_batches WHERE status='in_furnace' ORDER BY current_furnace_id, current_section")

def get_batch(batch_id):
    return query_one("SELECT * FROM production_batches WHERE id=%s", (batch_id,))

def update_batch_section(batch_id, new_section):
    query("UPDATE production_batches SET current_section=%s WHERE id=%s", (new_section, batch_id))

def update_batch_furnace(batch_id, furnace_id, section=1):
    """批次转移到另一炉子"""
    query("UPDATE production_batches SET current_furnace_id=%s, current_section=%s WHERE id=%s", (furnace_id, section, batch_id))

def complete_batch(batch_id):
    query("UPDATE production_batches SET status='completed', completed_at=NOW() WHERE id=%s", (batch_id,))

def create_batch(production_run_id, schedule_order_id, batch_label, product_name, process_name, entry_section, furnace_id):
    return query("""INSERT INTO production_batches (production_run_id, schedule_order_id, batch_label, product_name, process_name, current_section, current_furnace_id, entry_section)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                 (production_run_id, schedule_order_id, batch_label, product_name, process_name, entry_section, furnace_id, entry_section))

def get_active_section_logs():
    """在炉批次当前节拍的进入时间"""
    return query("""SELECT l.batch_id, l.furnace_id, l.section_order, l.entered_at
                    FROM batch_section_logs l
                    INNER JOIN production_batches b ON l.batch_id = b.id
                    WHERE b.status = 'in_furnace'
                      AND l.exited_at IS NULL
                      AND l.furnace_id = b.current_furnace_id
                      AND l.section_order = b.current_section""")

def create_batch_section_log(batch_id, furnace_id, section_order, target_temp):
    return query("INSERT INTO batch_section_logs (batch_id, furnace_id, section_order, target_temp, entered_at) VALUES (%s,%s,%s,%s,NOW())",
                 (batch_id, furnace_id, section_order, target_temp))

def close_batch_section_log(batch_id, section_order):
    query("""UPDATE batch_section_logs SET exited_at=NOW(), actual_duration_min=TIMESTAMPDIFF(MINUTE, entered_at, NOW())
             WHERE batch_id=%s AND section_order=%s AND exited_at IS NULL""",
          (batch_id, section_order))

def insert_blank_section(run_id, furnace_id, section_order):
    return query("INSERT INTO blank_section_logs (production_run_id, furnace_id, section_order, inserted_at) VALUES (%s,%s,%s,NOW())",
                 (run_id, furnace_id, section_order))

def get_section_temp(furnace_id, section_order):
    row = query_one("""SELECT target_temp FROM temperature_settings
                       WHERE furnace_id=%s AND is_active=1
                       AND (section_id IN (SELECT id FROM furnace_sections WHERE furnace_id=%s AND section_order=%s)
                            OR (zone_start<=%s AND zone_end>=%s))
                       LIMIT 1""",
                     (furnace_id, furnace_id, section_order, section_order, section_order))
    return row["target_temp"] if row else 0

def create_production_run(furnace_id):
    query("INSERT INTO production_runs (furnace_id, status, started_at) VALUES (%s, 'running', NOW())", (furnace_id,))
    return query_one("SELECT * FROM production_runs WHERE furnace_id=%s ORDER BY id DESC LIMIT 1", (furnace_id,))

def get_blank_sections(run_id):
    return query("SELECT * FROM blank_section_logs WHERE production_run_id=%s AND removed_at IS NULL ORDER BY section_order", (run_id,))

def remove_blank_section(run_id, section_order):
    query("UPDATE blank_section_logs SET removed_at=NOW() WHERE production_run_id=%s AND section_order=%s AND removed_at IS NULL",
          (run_id, section_order))

def update_order_status(order_id, status):
    query("UPDATE schedule_orders SET status=%s WHERE id=%s", (status, order_id))

def create_production_report(schedule_order_id, product_name, batch_no, batch_label, furnace_name,
                              planned_sections, actual_sections, planned_duration_min, actual_duration_min,
                              entry_time, exit_time, avg_temp=None, max_temp=None, min_temp=None):
    return query("""INSERT INTO production_reports (schedule_order_id, product_name, batch_no, batch_label, furnace_name,
                     planned_sections, actual_sections, planned_duration_min, actual_duration_min,
                     entry_time, exit_time, avg_temp, max_temp, min_temp)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                 (schedule_order_id, product_name, batch_no, batch_label, furnace_name,
                  planned_sections, actual_sections, planned_duration_min, actual_duration_min,
                  entry_time, exit_time, avg_temp, max_temp, min_temp))

# ==============================
# Reports
# ==============================
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

# ==============================
# Logs
# ==============================
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

# ==============================
# Backup / Export
# ==============================
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
