from uuid import UUID
from fastapi import APIRouter, Path, Depends, HTTPException, Query, status, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order as OrderORM
from app.schemas.order import (
    LimitOrderBody, MarketOrderBody, CreateOrderResponse,
    LimitOrder, MarketOrder, OrderStatus, OrderModel
)
from app.services.order_service import create_order, get_user_orders
from app.core.security import get_current_user
from app.dependencies import get_db
from typing import List, Union

router = APIRouter()
from app.schemas.order import LimitOrder, MarketOrder, LimitOrderBody, MarketOrderBody, OrderStatus, Direction
from uuid import UUID

def orm_to_pydantic_order(order_orm):
    # тут предполагается, что order_orm.type - либо "LIMIT", либо "MARKET"
    base_kwargs = {
        "id": UUID(order_orm.id),
        "status": OrderStatus(order_orm.status),
        "user_id": UUID(order_orm.user_id),
        "timestamp": order_orm.timestamp,
    }
    if order_orm.type == "LIMIT":
        return LimitOrder(
            **base_kwargs,
            body=LimitOrderBody(
                direction=Direction(order_orm.direction),
                ticker=order_orm.ticker,
                qty=order_orm.qty,
                price=order_orm.price
            ),
            filled=getattr(order_orm, "filled", 0)
        )
    else:  # MARKET
        return MarketOrder(
            **base_kwargs,
            body=MarketOrderBody(
                direction=Direction(order_orm.direction),
                ticker=order_orm.ticker,
                qty=order_orm.qty
            )
        )

@router.post(
    "/order",
    response_model=CreateOrderResponse,
    tags=["order"]
)
async def post_order(
    body: Union[LimitOrderBody, MarketOrderBody],
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
    user=Depends(get_current_user)

):
    order_id = await create_order(db, user.id, body)
    return {"success": True, "order_id": order_id}

@router.get("/order", response_model=List[OrderModel])
async def list_orders(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
    user=Depends(get_current_user)
):
    result = await db.execute(
        select(OrderORM).where(OrderORM.user_id == str(user.id))
    )
    orm_orders = result.scalars().all()
    return [orm_to_pydantic_order(order) for order in orm_orders]



@router.get("/order/{order_id}", response_model=OrderModel)
async def get_order_by_id(
    order_id: UUID = Path(..., title="Order Id"),
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
    user=Depends(get_current_user)
):
    order = await db.get(OrderORM, str(order_id))
    if not order or order.user_id != str(user.id):
        raise HTTPException(status_code=404, detail="Order not found")
    return orm_to_pydantic_order(order)


from app.schemas.ok import Ok  # Ok: BaseModel с success: True

@router.delete(
    "/order/{order_id}",
    response_model=Ok,
    tags=["order"]
)
async def cancel_order_by_id(
    order_id: UUID = Path(..., title="Order Id"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    order = await db.get(OrderORM, str(order_id))
    if not order or order.user_id != str(user.id):
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.NEW:
        raise HTTPException(status_code=400, detail="Cannot cancel this order")
    order.status = OrderStatus.CANCELLED
    await db.commit()
    return {"success": True}
