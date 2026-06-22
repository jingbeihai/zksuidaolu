from fastapi import APIRouter

router = APIRouter()

@router.get("/user/")
async def user_page():
    return {"message": "user module placeholder"}
