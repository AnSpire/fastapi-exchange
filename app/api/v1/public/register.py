from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import NewUser, UserResponse
from app.services.user_service import create_user
from app.dependencies import get_db

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(
    new_user: NewUser, db: AsyncSession = Depends(get_db)
):
    try:
        user = await create_user(db, new_user.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"user": user}
