from fastapi import APIRouter, Path, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User as UserORM
from app.schemas.user import User  # Импорт схемы
from app.dependencies import get_db
from app.core.security import get_admin_user

router = APIRouter()

@router.delete("/user/{user_id}", response_model=User)
async def delete_user(
    user_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_admin_user)
):
    user = await db.get(UserORM, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return user
