"""认证与权限服务"""
import bcrypt
import settings

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
        try:
            perm = json.loads(perm)
        except (json.JSONDecodeError, TypeError):
            return False
    return perm.get(module, False) == 1
