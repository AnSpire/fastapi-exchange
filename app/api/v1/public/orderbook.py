from fastapi import APIRouter, Path, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.instrument import Instrument as InstrumentORM
from app.models.order import Order as OrderORM
from app.schemas.order import L2OrderBook, Level
from app.dependencies import get_db

router = APIRouter()

@router.get(
    "/orderbook/{ticker}",
    response_model=L2OrderBook,
    tags=["public"]
)
async def get_orderbook(
    ticker: str = Path(..., pattern="^[A-Z]{2,10}$", title="Ticker"),
    limit: int = Query(10, ge=1, le=25),
    db: AsyncSession = Depends(get_db)
):
    # Проверяем, есть ли инструмент
    instrument = await db.get(InstrumentORM, ticker)
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")

    # Выбираем bids (BUY) — по убыванию цены
    bids_result = await db.execute(
        select(OrderORM).where(
            and_(
                OrderORM.ticker == ticker,
                OrderORM.direction == "BUY",
                OrderORM.status == "NEW"
            )
        ).order_by(OrderORM.price.desc()).limit(limit)
    )
    # Выбираем asks (SELL) — по возрастанию цены
    asks_result = await db.execute(
        select(OrderORM).where(
            and_(
                OrderORM.ticker == ticker,
                OrderORM.direction == "SELL",
                OrderORM.status == "NEW"
            )
        ).order_by(OrderORM.price.asc()).limit(limit)
    )

    bid_levels = [
        Level(price=order.price, qty=order.qty)
        for order in bids_result.scalars().all()
        if order.price is not None
    ]
    ask_levels = [
        Level(price=order.price, qty=order.qty)
        for order in asks_result.scalars().all()
        if order.price is not None
    ]

    return L2OrderBook(bid_levels=bid_levels, ask_levels=ask_levels)
