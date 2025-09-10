from uuid import UUID
from fastapi import APIRouter, Path, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User as UserORM
from app.schemas.user import User  # Pydantic-схема
from app.dependencies import get_db
from app.core.security import get_admin_user
from sqlalchemy import update
from app.models.order import Order
import uuid
router = APIRouter()
from sqlalchemy import update, delete
from app.models.order import Order as OrderORM

@router.delete("/user/{user_id}", response_model=User, tags=["admin","user"])
async def delete_user(
    user_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_admin_user)
):
    user = await db.get(UserORM, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    # 1) Отменяем все активные ордера
    await db.execute(
        update(OrderORM)
        .where(
            OrderORM.user_id == user.id,
            OrderORM.status.in_(["NEW", "PARTIALLY_EXECUTED"])
        )
        .values(status="CANCELLED")
    )
    # 2) Удаляем ВСЕ ордера этого пользователя, чтобы не осталось ссылок
    await db.execute(
        delete(OrderORM)
        .where(OrderORM.user_id == user.id)
    )

    # 3) Теперь можно удалить самого пользователя
    await db.delete(user)
    await db.commit()
    return user
