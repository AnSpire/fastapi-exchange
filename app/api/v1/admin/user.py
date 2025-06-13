from uuid import UUID
from fastapi import APIRouter, Path, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User as UserORM
from app.schemas.user import User  # Pydantic-схема
from app.dependencies import get_db
from app.core.security import get_admin_user

router = APIRouter()

@router.delete(
    "/user/{user_id}",
    response_model=User,
    tags=["admin", "user"]
)
async def delete_user(
    user_id: UUID = Path(..., title="User Id", description="UUID пользователя"),
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
    admin=Depends(get_admin_user)
):
    user = await db.get(UserORM, str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return user
