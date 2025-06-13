from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.instrument import Instrument

async def list_instruments(db: AsyncSession):
    result = await db.execute(select(Instrument))
    return result.scalars().all()
