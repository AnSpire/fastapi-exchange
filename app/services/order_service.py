import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order
async def create_order(db, user_id: str, data):
    order_id = str(uuid.uuid4())
    order_type = "LIMIT" if hasattr(data, "price") else "MARKET"
    order = Order(
        id=order_id,
        user_id=user_id,
        type=order_type,
        direction=data.direction,
        ticker=data.ticker,
        qty=data.qty,
        price=getattr(data, "price", None)
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order_id


async def get_user_orders(db: AsyncSession, user_id: str):
    result = await db.execute(select(Order).where(Order.user_id == user_id))
    return result.scalars().all()
