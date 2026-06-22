"""工艺组合管理路由"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from templates import templates
from routers.auth import login_required
from services.auth_service import check_permission
import db.queries as dbq
import json

router = APIRouter(dependencies=[Depends(login_required)])

@router.get("/process/", response_class=HTMLResponse)
async def process_list(request: Request):
    user = login_required(request)
    if not check_permission(user, "process"):
        return templates.TemplateResponse("base.html", {
            "request": request, "error": "无权限访问该模块"
        })
    products = dbq.get_products()
    processes = dbq.get_processes()
    process_map = {}
    for p in processes:
        process_map.setdefault(p["product_id"], []).append(p)
    return templates.TemplateResponse("process/list.html", {
        "request": request, "products": products, "process_map": process_map
    })

@router.get("/process/create/", response_class=HTMLResponse)
async def process_create_page(request: Request):
    user = login_required(request)
    if not check_permission(user, "process"):
        return templates.TemplateResponse("base.html", {
            "request": request, "error": "无权限访问该模块"
        })
    return templates.TemplateResponse("process/create.html", {"request": request})

# ========== 产品管理 ==========

@router.post("/api/process/create-combo")
async def create_product_process_combo(request: Request):
    """一键创建产品 + 工艺 + 初始操作指导"""
    user = login_required(request)
    data = await request.json()
    try:
        # 1. 创建产品（名称 + 自动编号）
        import datetime
        code_prefix = datetime.datetime.now().strftime("P%m%d")
        row = dbq.query_one("SELECT COUNT(*) as cnt FROM products WHERE code LIKE %s", (code_prefix + "%",))
        prod_code = code_prefix + str((row["cnt"] if row else 0) + 1).zfill(3)
        prod_id = dbq.create_product(data["product_name"], prod_code, "")
        # 2. 创建工艺
        proc_id = dbq.create_process(prod_id, data["process_name"],
                                     data["version_no"], user["id"])
        # 3. 保存操作指导作为步骤1
        guide = data.get("operation_guide", "")
        if guide:
            dbq.query("INSERT INTO process_steps (process_id, step_order, section_start, section_end, target_temp, operation_guide) VALUES (%s, 1, 0, 0, 0, %s)",
                      (proc_id, guide))
        return {"success": True, "product_id": prod_id, "process_id": proc_id}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/process/product/create")
async def create_product(request: Request):
    login_required(request)
    data = await request.json()
    try:
        dbq.create_product(data["name"], data["code"], data.get("description", ""))
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/process/product/delete/{product_id}")
async def delete_product(product_id: int, request: Request):
    login_required(request)
    try:
        dbq.query("UPDATE products SET is_active=0 WHERE id=%s", (product_id,))
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ========== 工艺管理 ==========

@router.get("/api/process/{process_id}")
async def get_process_detail(process_id: int, request: Request):
    login_required(request)
    proc = dbq.get_process(process_id)
    if not proc:
        return {"error": "工艺不存在"}
    steps = dbq.get_process_steps(process_id)
    proc["steps"] = steps
    return proc

@router.post("/api/process/create")
async def create_process(request: Request):
    user = login_required(request)
    data = await request.json()
    try:
        dbq.create_process(data["product_id"], data["process_name"],
                           data["version_no"], user["id"])
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/process/{process_id}/save-steps")
async def save_steps(process_id: int, request: Request):
    login_required(request)
    data = await request.json()
    dbq.save_process_steps(process_id, data.get("steps", []))
    return {"success": True}

@router.post("/api/process/{process_id}/publish")
async def publish_process(process_id: int, request: Request):
    login_required(request)
    try:
        steps = dbq.get_process_steps(process_id)
        if not steps:
            return {"success": False, "message": "请先添加工艺步骤"}
        dbq.publish_process(process_id)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/process/{process_id}/unpublish")
async def unpublish_process(process_id: int, request: Request):
    login_required(request)
    try:
        dbq.query("UPDATE processes SET status='draft' WHERE id=%s", (process_id,))
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/process/{process_id}/delete")
async def delete_process(process_id: int, request: Request):
    login_required(request)
    try:
        # 先清空步骤（解除外键约束）
        dbq.query("DELETE FROM process_steps WHERE process_id=%s", (process_id,))
        # 取消关联的排产单
        dbq.query("UPDATE schedule_orders SET status='cancelled' WHERE process_id=%s AND status='pending'", (process_id,))
        # 删除工艺
        dbq.query("DELETE FROM processes WHERE id=%s", (process_id,))
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}
