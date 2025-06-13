from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.instrument import Instrument as InstrumentORM
from app.schemas.instrument import Instrument as InstrumentSchema
from app.dependencies import get_db
from sqlalchemy.future import select

router = APIRouter()

@router.get("/instrument", response_model=list[InstrumentSchema], tags=["public"])
async def list_instruments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InstrumentORM))
    instruments = result.scalars().all()
    return instruments
