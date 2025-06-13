from fastapi import APIRouter, Path, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.schemas.order import L2OrderBook, Level
from app.models.instrument import Instrument
from app.models.order import Order
from app.dependencies import get_db
from typing import List

router = APIRouter()

@router.get("/orderbook/{ticker}", response_model=L2OrderBook)
async def get_orderbook(
    ticker: str = Path(...),
    limit: int = Query(10, ge=1, le=25),
    db: AsyncSession = Depends(get_db)
):
    instrument = await db.get(Instrument, ticker)
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")

    bids_result = await db.execute(
        select(Order).where(
            and_(
                Order.ticker == ticker,
                Order.direction == "BUY",
                Order.status == "NEW"
            )
        ).order_by(Order.price.desc()).limit(limit)
    )
    asks_result = await db.execute(
        select(Order).where(
            and_(
                Order.ticker == ticker,
                Order.direction == "SELL",
                Order.status == "NEW"
            )
        ).order_by(Order.price.asc()).limit(limit)
    )

    bids = [Level(price=order.price, qty=order.qty) for order, in bids_result.all()]
    asks = [Level(price=order.price, qty=order.qty) for order, in asks_result.all()]

    return L2OrderBook(bid_levels=bids, ask_levels=asks)
