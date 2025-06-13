# app/api/v1/admin/instrument.py
from app.schemas.instrument import Instrument
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.instrument import Instrument as InstrumentModel
from app.dependencies import get_db
from app.core.security import get_admin_user
router = APIRouter()

@router.post("", response_model=dict)
async def add_instrument(
    instrument: Instrument,
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(get_admin_user)
):
    # Проверить, есть ли тикер
    exists = await db.get(InstrumentModel, instrument.ticker)
    if exists:
        raise HTTPException(400, detail="Instrument already exists")
    db.add(InstrumentModel(ticker=instrument.ticker, name=instrument.name))
    await db.commit()
    return {"success": True}






@router.delete("/{ticker}", response_model=dict)
async def delete_instrument(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(get_admin_user)
):
    instrument = await db.get(InstrumentModel, ticker)
    if not instrument:
        raise HTTPException(404, detail="Instrument not found")
    await db.delete(instrument)
    await db.commit()
    return {"success": True}
