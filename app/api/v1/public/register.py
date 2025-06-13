from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.user import NewUser, User as UserSchema
from app.models.user import User as UserORM
from app.dependencies import get_db
import uuid

router = APIRouter()

@router.post("/register", response_model=UserSchema, tags=["public"])
async def register_user(
    new_user: NewUser, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserORM).where(UserORM.name == new_user.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = UserORM(
        id=str(uuid.uuid4()),
        name=new_user.name,
        role="USER",
        api_key=f"key-{uuid.uuid4()}"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserSchema(
        id=user.id,
        name=user.name,
        role=user.role,
        api_key=user.api_key
    )
