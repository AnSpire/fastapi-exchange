from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.order import LimitOrderBody, MarketOrderBody, CreateOrderResponse
from app.services.order_service import create_order
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.order import LimitOrder, MarketOrder
from app.services.order_service import get_user_orders
from app.core.security import get_current_user
from app.dependencies import get_db
from typing import List, Union
router = APIRouter()



@router.get("/order", response_model=List[Union[LimitOrder, MarketOrder]])
async def list_orders(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    return await get_user_orders(db, user.id)

@router.post("/order", response_model=CreateOrderResponse)
async def post_order(
    body: Union[LimitOrderBody, MarketOrderBody],
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    order_id = await create_order(db, user.id, body)
    return {"success": True, "order_id": order_id}
from fastapi import APIRouter, Path, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order
from app.schemas.order import LimitOrder, MarketOrder  # твои pydantic схемы для ответа
from app.core.security import get_current_user
from app.dependencies import get_db

router = APIRouter()

@router.get("/order/{order_id}", response_model=LimitOrder)  # или Union[LimitOrder, MarketOrder]
async def get_order_by_id(
    order_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    order = await db.get(Order, order_id)
    if not order or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    # Если надо — вернуть нужную схему (Limit/Market)
    return order

@router.delete("/order/{order_id}")
async def cancel_order_by_id(
    order_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    order = await db.get(Order, order_id)
    if not order or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in ("NEW",):  # только новые можно отменить
        raise HTTPException(status_code=400, detail="Cannot cancel this order")
    order.status = "CANCELLED"
    await db.commit()
    return {"success": True}
