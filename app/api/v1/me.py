from app.schemas.user import UserResponse
from app.core.security import get_current_user
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_me(user=Depends(get_current_user)):
    print(user, type(user))
    return {"user": user}


