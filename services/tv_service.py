"""TV 大屏数据组装"""
from datetime import datetime

import db.queries as dbq

FURNACE_FOAM_ID = 1
FURNACE_CURE_ID = 2


def _temp_int(furnace_id, section_order):
    temp = dbq.get_section_temp(furnace_id, section_order)
    if temp is None:
        return None
    return int(float(temp))


def _derive_run_status(runs):
    if any(r and r.get("status") == "running" for r in runs):
        return "running"
    if any(r and r.get("status") == "paused" for r in runs):
        return "paused"
    return "idle"


def _section_progress(entered_at, section_minutes, run):
    """当前节拍生产进度 0–100，暂停时冻结在 paused_at"""
    if not entered_at or not section_minutes:
        return 0.0
    end = datetime.now()
    if run and run.get("status") == "paused" and run.get("paused_at"):
        end = run["paused_at"]
    elapsed = (end - entered_at).total_seconds()
    total = section_minutes * 60
    if total <= 0:
        return 0.0
    return round(min(100.0, max(0.0, elapsed / total * 100)), 1)


def build_tv_data():
    furnaces = {f["id"]: f for f in dbq.get_furnaces()}
    foam = furnaces.get(FURNACE_FOAM_ID)
    cure = furnaces.get(FURNACE_CURE_ID)
    foam_count = foam["section_count"] if foam else 18
    cure_count = cure["section_count"] if cure else 52
    section_mins = {fid: f.get("section_minutes") or 16 for fid, f in furnaces.items()}

    runs_by_fid = {
        FURNACE_FOAM_ID: dbq.get_production_run(FURNACE_FOAM_ID),
        FURNACE_CURE_ID: dbq.get_production_run(FURNACE_CURE_ID),
    }

    logs_by_section = {}
    for log in dbq.get_active_section_logs():
        logs_by_section[(log["furnace_id"], log["section_order"])] = log

    batches_by_section = {}
    for b in dbq.get_all_active_batches():
        fid = b["current_furnace_id"]
        sec = b["current_section"]
        if not fid or not sec:
            continue
        mins = section_mins.get(fid, 16)
        log = logs_by_section.get((fid, sec))
        entered_at = log["entered_at"] if log else None
        progress = _section_progress(entered_at, mins, runs_by_fid.get(fid))
        batches_by_section[(fid, sec)] = {
            "label": b["batch_label"],
            "product": b["product_name"],
            "process": b["process_name"],
            "temp": _temp_int(fid, sec),
            "progress": progress,
            "entered_at": entered_at.isoformat() if entered_at else None,
            "section_minutes": mins,
        }

    blank_sections = set()
    for fid in (FURNACE_FOAM_ID, FURNACE_CURE_ID):
        run = runs_by_fid.get(fid)
        if not run:
            continue
        for bl in dbq.get_blank_sections(run["id"]):
            blank_sections.add((fid, bl["section_order"]))

    cells = []
    total = foam_count + cure_count
    for g in range(1, total + 1):
        if g <= foam_count:
            fid, sec, zone = FURNACE_FOAM_ID, g, "foam"
        else:
            fid, sec, zone = FURNACE_CURE_ID, g - foam_count, "cure"

        batch = batches_by_section.get((fid, sec))
        is_blank = (fid, sec) in blank_sections and not batch
        cells.append({
            "order": g,
            "zone": zone,
            "temp": _temp_int(fid, sec),
            "blank": is_blank,
            "batch": batch,
        })

    schedules = []
    for o in dbq.get_tv_schedule_orders():
        in_f = int(o.get("in_furnace") or 0)
        done = int(o.get("completed") or 0)
        qty = int(o["quantity"])
        waiting = max(qty - in_f - done, 0)
        st = o.get("scheduled_time")
        schedules.append({
            "product": o["product_name"],
            "order": o["order_no"],
            "batch": o["batch_no"],
            "total": qty,
            "waiting": waiting,
            "in_furnace": in_f,
            "time": st.strftime("%m/%d %H:%M") if st else "",
        })

    runs = list(runs_by_fid.values())
    section_minutes = (foam or cure or {}).get("section_minutes", 16)

    return {
        "status": _derive_run_status(runs),
        "section_minutes": section_minutes,
        "foam_count": foam_count,
        "cells": cells,
        "schedules": schedules,
        "server_time": datetime.now().isoformat(timespec="seconds"),
    }
