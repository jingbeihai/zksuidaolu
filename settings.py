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
SESSION_MAX_AGE = 8 * 3600

TV_REFRESH_INTERVAL = 10
