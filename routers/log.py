from fastapi import APIRouter

router = APIRouter()

@router.get("/log/")
async def log_page():
    return {"message": "log module placeholder"}
