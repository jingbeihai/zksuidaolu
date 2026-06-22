"""登录认证路由"""
import json
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from templates import templates
from services.auth_service import verify_password
from db.queries import get_user_by_username

router = APIRouter()

def get_current_user(request: Request):
    return request.session.get("user")

def login_required(request: Request):
    user = get_current_user(request)
    if not user:
        raise RedirectResponse(url="/login", status_code=302)
    return user

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = get_user_by_username(username)
    if not user or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse("login.html", {
            "request": request, "error": "用户名或密码错误"
        })
    # 解析权限 JSON
    perms = user["permissions"]
    if isinstance(perms, str):
        try:
            perms = json.loads(perms)
        except (json.JSONDecodeError, TypeError):
            perms = {}
    if not isinstance(perms, dict):
        perms = {}
    request.session["user"] = {
        "id": user["id"],
        "username": user["username"],
        "real_name": user["real_name"],
        "is_admin": bool(user["is_admin"]),
        "permissions": perms
    }
    return RedirectResponse(url="/schedule/", status_code=302)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)
