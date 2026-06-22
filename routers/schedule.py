"""排产管理路由"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from templates import templates
from routers.auth import login_required
from services.auth_service import check_permission
import db.queries as dbq

router = APIRouter(dependencies=[Depends(login_required)])

@router.get("/schedule/", response_class=HTMLResponse)
async def schedule_list(request: Request):
    user = login_required(request)
    if not check_permission(user, "schedule"):
        return templates.TemplateResponse("base.html", {
            "request": request, "error": "无权限访问该模块"
        })
    orders = dbq.get_orders()
    return templates.TemplateResponse("schedule/list.html", {
        "request": request, "orders": orders
    })

@router.get("/schedule/create/", response_class=HTMLResponse)
async def schedule_create_page(request: Request):
    user = login_required(request)
    if not check_permission(user, "schedule"):
        return templates.TemplateResponse("base.html", {
            "request": request, "error": "无权限访问该模块"
        })
    products = dbq.get_products()
    furnaces = dbq.get_furnaces()
    return templates.TemplateResponse("schedule/create.html", {
        "request": request, "products": products, "furnaces": furnaces
    })

# ========== API ==========

@router.get("/api/schedule/orders")
async def api_get_orders(request: Request):
    login_required(request)
    status = request.query_params.get("status")
    if status:
        orders = dbq.get_orders(status)
    else:
        orders = dbq.get_orders()
    return {"orders": orders}

@router.get("/api/schedule/product/{product_id}/processes")
async def api_get_processes(product_id: int, request: Request):
    login_required(request)
    processes = dbq.get_processes(product_id)
    # 只返回已发布的工艺
    processes = [p for p in processes if p["status"] == "published"]
    return {"processes": processes}

@router.post("/api/schedule/order/create")
async def api_create_order(request: Request):
    user = login_required(request)
    if not check_permission(user, "schedule"):
        return {"success": False, "message": "无权限"}
    data = await request.json()
    try:
        order_no = dbq.generate_order_no()
        order_id = dbq.create_order(
            order_no=order_no,
            process_id=data["process_id"],
            product_id=data["product_id"],
            batch_no=data["batch_no"],
            quantity=data["quantity"],
            blank_sections=data.get("blank_sections", 0),
            scheduled_time=data["scheduled_time"],
            assigned_furnace_id=data.get("furnace_id"),
            created_by=user["id"]
        )
        return {"success": True, "order_no": order_no, "order_id": order_id}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/schedule/order/{order_id}/cancel")
async def api_cancel_order(order_id: int, request: Request):
    login_required(request)
    try:
        dbq.cancel_order(order_id)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/schedule/order/generate-batch")
async def api_generate_batch(request: Request):
    """生成批号预览（不保存）"""
    data = await request.json()
    # 格式: P + 产品code + 日期 + 序号
    import datetime
    prefix = "B" + datetime.datetime.now().strftime("%m%d") + "-"
    return {"batch_no": prefix + "001"}
