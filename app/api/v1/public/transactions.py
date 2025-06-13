from fastapi import APIRouter, Path, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.transaction import Transaction as TransactionORM
from app.models.instrument import Instrument as InstrumentORM
from app.schemas.transaction import Transaction
from app.dependencies import get_db

router = APIRouter()

@router.get(
    "/transactions/{ticker}",
    response_model=list[Transaction],
    tags=["public"]
)
async def get_transaction_history(
    ticker: str = Path(..., pattern="^[A-Z]{2,10}$"),
    limit: int = Query(10, ge=1, le=100),

    db: AsyncSession = Depends(get_db)
):
    # Проверка существования тикера
    instrument = await db.get(InstrumentORM, ticker)
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")

    result = await db.execute(
        select(TransactionORM).where(TransactionORM.ticker == ticker)
        .order_by(TransactionORM.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()
