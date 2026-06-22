"""TV可视化大屏路由"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from templates import templates
from services.tv_service import build_tv_data

router = APIRouter()


@router.get("/tv", response_class=HTMLResponse)
async def tv_page(request: Request):
    return templates.TemplateResponse("tv.html", {"request": request})


@router.get("/api/tv/data")
async def tv_data():
    return JSONResponse(build_tv_data())
