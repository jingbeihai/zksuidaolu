"""设备管理路由"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from templates import templates
from routers.auth import login_required
from services.auth_service import check_permission
import db.queries as dbq

router = APIRouter(dependencies=[Depends(login_required)])

@router.get("/device/", response_class=HTMLResponse)
async def device_list(request: Request):
    user = login_required(request)
    if not check_permission(user, "device"):
        return templates.TemplateResponse("base.html", {
            "request": request, "error": "无权限访问该模块"
        })
    furnaces = dbq.get_furnaces()
    for f in furnaces:
        f["sections"] = dbq.get_furnace_sections(f["id"])
        f["temp_settings"] = dbq.get_temp_settings(f["id"])
    return templates.TemplateResponse("device/list.html", {
        "request": request, "furnaces": furnaces
    })

@router.get("/api/device/furnace/{furnace_id}/temp")
async def get_temp(furnace_id: int, request: Request):
    login_required(request)
    settings_list = dbq.get_temp_settings(furnace_id)
    sections = dbq.get_furnace_sections(furnace_id)
    return {"sections": sections, "settings": settings_list}

@router.post("/api/device/furnace/{furnace_id}/temp")
async def save_temp(furnace_id: int, request: Request):
    user = login_required(request)
    data = await request.json()
    dbq.save_temp_settings(furnace_id, data.get("settings", []))
    return {"success": True, "message": "温度设置已保存"}
