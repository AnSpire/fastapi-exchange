from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.balance import Balance

async def get_user_balances(db: AsyncSession, user_id: str):
    result = await db.execute(select(Balance).where(Balance.user_id == user_id))
    balances = result.scalars().all()
    return {bal.ticker: bal.amount for bal in balances}
