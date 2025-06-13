import uuid
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User

async def create_user(db: AsyncSession, name: str):
    result = await db.execute(select(User).where(User.name == name))
    if result.scalar_one_or_none():
        raise ValueError("User already exists")

    user = User(
        id=str(uuid.uuid4()),
        name=name,
        role="USER",
        api_key=secrets.token_hex(32)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
