"""生产控制路由"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from templates import templates
from routers.auth import login_required
from services.auth_service import check_permission
import db.queries as dbq
from operator import itemgetter
import logging

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(login_required)])

# 炉子ID常量
FURNACE_FOAM_ID = 1   # 发泡炉 (18节)
FURNACE_CURE_ID = 2   # 固化炉 (52节)

@router.get("/production/", response_class=HTMLResponse)
async def production_page(request: Request):
    user = login_required(request)
    if not check_permission(user, "production"):
        return templates.TemplateResponse("base.html", {
            "request": request, "error": "无权限访问该模块"
        })
    furnaces = dbq.get_furnaces()
    furnace_data = []
    for f in furnaces:
        run = dbq.get_production_run(f["id"])
        sections = dbq.get_furnace_sections(f["id"])
        batches = dbq.get_batches_in_furnace(f["id"])
        blanks = []
        if run:
            blanks = dbq.get_blank_sections(run["id"])
        pending_orders = dbq.get_pending_orders(f["id"])
        furnace_data.append({
            "furnace": f,
            "run": run,
            "sections": sections,
            "batches": batches,
            "blanks": blanks,
            "pending_orders": pending_orders
        })
    return templates.TemplateResponse("production/list.html", {
        "request": request, "furnace_data": furnace_data
    })

# ========== API ==========

@router.get("/api/production/furnace/{furnace_id}")
async def api_get_furnace_status(furnace_id: int, request: Request):
    login_required(request)
    furnace = dbq.get_furnace(furnace_id)
    run = dbq.get_production_run(furnace_id)
    sections = dbq.get_furnace_sections(furnace_id)
    batches = dbq.get_batches_in_furnace(furnace_id)
    blanks = []
    if run:
        blanks = dbq.get_blank_sections(run["id"])
    pending = dbq.get_pending_orders(furnace_id)
    return {
        "furnace": furnace,
        "run": run,
        "sections": sections,
        "batches": batches,
        "blanks": blanks,
        "pending_orders": pending
    }

@router.post("/api/production/start/{furnace_id}")
async def api_start_production(furnace_id: int, request: Request):
    user = login_required(request)
    data = await request.json()
    order_id = data.get("order_id")
    if not order_id:
        return {"success": False, "message": "请选择排产单"}

    furnace = dbq.get_furnace(furnace_id)
    if not furnace:
        return {"success": False, "message": "炉子不存在"}

    run = dbq.get_production_run(furnace_id)
    if run and run["status"] != "idle" and run["status"] != "stopped":
        return {"success": False, "message": "炉子当前状态不允许开机"}

    order = dbq.query_one("SELECT * FROM schedule_orders WHERE id=%s", (order_id,))
    if not order or order["status"] != "pending":
        return {"success": False, "message": "排产单状态异常"}

    proc = dbq.get_process(order["process_id"])
    product = dbq.query_one("SELECT * FROM products WHERE id=%s", (order["product_id"],))

    try:
        if run:
            dbq.query("UPDATE production_runs SET status='running', current_section=1, started_at=NOW() WHERE id=%s", (run["id"],))
            run_id = run["id"]
        else:
            run = dbq.create_production_run(furnace_id)
            run_id = run["id"]

        entry_section = 1
        batch_id = dbq.create_batch(run_id, order["id"], order["batch_no"],
                                     product["name"] if product else order["batch_no"],
                                     proc["process_name"] if proc else "",
                                     entry_section, furnace_id)

        temp = dbq.get_section_temp(furnace_id, entry_section)
        dbq.create_batch_section_log(batch_id, furnace_id, entry_section, temp)

        dbq.update_order_status(order["id"], "in_production")
        dbq.query("UPDATE production_runs SET current_order_id=%s WHERE id=%s", (order["id"], run_id))

        return {"success": True, "run_id": run_id, "batch_id": batch_id}
    except Exception as e:
        logger.exception("开机失败")
        return {"success": False, "message": str(e)}

@router.post("/api/production/{furnace_id}/pause")
async def api_pause(furnace_id: int, request: Request):
    login_required(request)
    run = dbq.get_production_run(furnace_id)
    if not run:
        return {"success": False, "message": "没有正在运行的炉次"}
    dbq.update_run_status(run["id"], "paused")
    dbq.query("UPDATE production_runs SET paused_at=NOW() WHERE id=%s", (run["id"],))
    return {"success": True}

@router.post("/api/production/{furnace_id}/resume")
async def api_resume(furnace_id: int, request: Request):
    login_required(request)
    run = dbq.get_production_run(furnace_id)
    if not run:
        return {"success": False, "message": "没有暂停的炉次"}
    dbq.update_run_status(run["id"], "running")
    return {"success": True}

@router.post("/api/production/{furnace_id}/stop")
async def api_stop(furnace_id: int, request: Request):
    login_required(request)
    run = dbq.get_production_run(furnace_id)
    if not run:
        return {"success": False, "message": "没有正在运行的炉次"}
    batches = dbq.get_batches_in_furnace(furnace_id)

    furnace = dbq.get_furnace(furnace_id)
    for b in batches:
        order = dbq.query_one("SELECT * FROM schedule_orders WHERE id=%s", (b["schedule_order_id"],))
        dbq.complete_batch(b["id"])
        if order:
            dbq.update_order_status(order["id"], "completed")

    dbq.update_run_status(run["id"], "stopped")
    dbq.query("UPDATE production_runs SET stopped_at=NOW() WHERE id=%s", (run["id"],))
    return {"success": True}

@router.post("/api/production/{furnace_id}/advance")
async def api_advance_batch(furnace_id: int, request: Request):
    """批次前进一节。发泡炉(18节)→固化炉(52节)串联。"""
    login_required(request)
    data = await request.json()
    batch_id = data.get("batch_id")
    all_batches = data.get("all", False)

    furnace = dbq.get_furnace(furnace_id)
    if not furnace:
        return {"success": False, "message": "炉子不存在"}

    run = dbq.get_production_run(furnace_id)
    if not run or run["status"] != "running":
        return {"success": False, "message": "炉子未运行"}

    if all_batches:
        _advance_all_batches(furnace_id, furnace)
        return {"success": True}

    batch = dbq.get_batch(batch_id)
    if not batch:
        return {"success": False, "message": "批次不存在"}

    new_section = batch["current_section"] + 1
    if new_section > furnace["section_count"]:
        result = _handle_batch_exit(batch, furnace_id, furnace["section_count"])
        return {"success": True, "message": result["message"]}

    dbq.close_batch_section_log(batch["id"], batch["current_section"])
    dbq.update_batch_section(batch["id"], new_section)
    temp = dbq.get_section_temp(furnace_id, new_section)
    dbq.create_batch_section_log(batch["id"], furnace_id, new_section, temp)
    return {"success": True, "new_section": new_section}

@router.post("/api/production/{furnace_id}/retreat")
async def api_retreat_batch(furnace_id: int, request: Request):
    """批次后退一节。支持跨炉后退(固化→发泡)。"""
    login_required(request)
    data = await request.json()
    batch_id = data.get("batch_id")
    all_batches = data.get("all", False)

    furnace = dbq.get_furnace(furnace_id)
    run = dbq.get_production_run(furnace_id)
    if not run or run["status"] != "running":
        return {"success": False, "message": "炉子未运行"}

    if all_batches:
        batches = dbq.get_batches_in_furnace(furnace_id)
        batches_sorted = sorted(batches, key=itemgetter("current_section"), reverse=True)
        for b in batches_sorted:
            _retreat_single_batch(b, furnace_id)
        return {"success": True}

    batch = dbq.get_batch(batch_id)
    if not batch:
        return {"success": False, "message": "批次不存在"}
    _retreat_single_batch(batch, furnace_id)
    return {"success": True}


# ========== 内部辅助函数 ==========

def _handle_batch_exit(batch, current_furnace_id, section_count):
    """批次退出当前炉时的处理逻辑"""
    dbq.close_batch_section_log(batch["id"], section_count)

    if current_furnace_id == FURNACE_FOAM_ID:
        # 发泡炉→固化炉转移
        dbq.update_batch_furnace(batch["id"], FURNACE_CURE_ID, 1)
        temp = dbq.get_section_temp(FURNACE_CURE_ID, 1)
        dbq.create_batch_section_log(batch["id"], FURNACE_CURE_ID, 1, temp)
        return {"message": "批次已转入固化炉"}
    else:
        # 固化炉→出炉完成
        dbq.complete_batch(batch["id"])
        order = dbq.query_one("SELECT * FROM schedule_orders WHERE id=%s", (batch["schedule_order_id"],))
        if order:
            dbq.update_order_status(order["id"], "completed")
        return {"message": "批次已出炉完成"}

def _retreat_single_batch(batch, current_furnace_id):
    if batch["current_section"] <= 1:
        if current_furnace_id == FURNACE_CURE_ID:
            # 固化炉第1节后退→转回发泡炉末节
            target_section = 18  # 发泡炉总节数
            dbq.close_batch_section_log(batch["id"], batch["current_section"])
            dbq.update_batch_furnace(batch["id"], FURNACE_FOAM_ID, target_section)
            temp = dbq.get_section_temp(FURNACE_FOAM_ID, target_section)
            dbq.create_batch_section_log(batch["id"], FURNACE_FOAM_ID, target_section, temp)
        return

    new_section = batch["current_section"] - 1
    dbq.close_batch_section_log(batch["id"], batch["current_section"])
    dbq.update_batch_section(batch["id"], new_section)
    temp = dbq.get_section_temp(current_furnace_id, new_section)
    dbq.create_batch_section_log(batch["id"], current_furnace_id, new_section, temp)

def _advance_all_batches(furnace_id, furnace):
    batches = dbq.get_batches_in_furnace(furnace_id)
    batches_sorted = sorted(batches, key=itemgetter("current_section"), reverse=True)
    for b in batches_sorted:
        new_section = b["current_section"] + 1
        if new_section > furnace["section_count"]:
            _handle_batch_exit(b, furnace_id, furnace["section_count"])
        else:
            dbq.close_batch_section_log(b["id"], b["current_section"])
            dbq.update_batch_section(b["id"], new_section)
            temp = dbq.get_section_temp(furnace_id, new_section)
            dbq.create_batch_section_log(b["id"], furnace_id, new_section, temp)
