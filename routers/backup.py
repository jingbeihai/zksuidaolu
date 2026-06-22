from fastapi import APIRouter

router = APIRouter()

@router.get("/backup/")
async def backup_page():
    return {"message": "backup module placeholder"}
