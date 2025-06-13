from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.instrument import Instrument
from app.services.instrument_service import list_instruments
from app.dependencies import get_db

router = APIRouter()

@router.get("/instrument", response_model=list[Instrument])
async def get_instruments(db: AsyncSession = Depends(get_db)):
    return await list_instruments(db)
