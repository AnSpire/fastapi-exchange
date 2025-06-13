from fastapi import APIRouter, Path, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.transaction import Transaction as TransactionORM
from app.schemas.transaction import Transaction
from app.dependencies import get_db
from typing import List

router = APIRouter()

@router.get("/transactions/{ticker}", response_model=List[Transaction])
async def get_transactions(
    ticker: str = Path(...),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    # Выборка последних сделок по тикеру, сортировка по времени (от новых к старым)
    result = await db.execute(
        select(TransactionORM).where(TransactionORM.ticker == ticker)
        .order_by(TransactionORM.timestamp.desc())
        .limit(limit)
    )
    transactions = result.scalars().all()
    return transactions
