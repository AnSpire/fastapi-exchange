from fastapi import Header

from app.schemas.instrument import Instrument
from fastapi import APIRouter, Path, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.instrument import Instrument as InstrumentORM
from app.schemas.ok import Ok
from app.dependencies import get_db
from app.core.security import get_admin_user
from app.schemas.ok import Ok

router = APIRouter()

@router.post("", response_model=Ok, tags=["admin", "instrument"])
async def create_instrument(
    body: Instrument,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
    admin=Depends(get_admin_user)
):
    existing = await db.get(InstrumentORM, body.ticker)
    if existing:
        raise HTTPException(status_code=400, detail="Instrument already exists")

    instrument = InstrumentORM(ticker=body.ticker, name=body.name)
    db.add(instrument)
    await db.commit()
    return {"success": True}

@router.delete("/{ticker}", response_model=Ok, tags=["admin", "instrument"])
async def delete_instrument(
    ticker: str = Path(..., pattern="^[A-Z]{2,10}$"),
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
    admin=Depends(get_admin_user)
):
    instrument = await db.get(InstrumentORM, ticker)
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    await db.delete(instrument)
    await db.commit()
    return {"success": True}

