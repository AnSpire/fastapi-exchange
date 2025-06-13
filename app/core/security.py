from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import NewUser, UserResponse
from app.services.user_service import create_user
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.models.user import User
from sqlalchemy import select


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


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
   auth = request.headers.get("Authorization")
   if not auth or not auth.startswith("TOKEN "):
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided")
   api_key = auth.removeprefix("TOKEN ").strip()
   result = await db.execute(select(User).where(User.api_key == api_key))
   user = result.scalar_one_or_none()
   if not user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
   return user


async def get_admin_user(request: Request, db: AsyncSession = Depends(get_db)):
   auth = request.headers.get("Authorization")
   if not auth or not auth.startswith("TOKEN "):
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided")
   api_key = auth.removeprefix("TOKEN ").strip()
   result = await db.execute(select(User).where(User.api_key == api_key))
   user = result.scalar_one_or_none()
   if not user or user.role != "ADMIN":
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
   return user
