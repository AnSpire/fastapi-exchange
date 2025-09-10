from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order as OrderORM
from app.schemas.order import LimitOrderBody, MarketOrderBody, CreateOrderResponse
from app.dependencies import get_db
from app.core.security import get_current_user
from app.services.matching import match_order  # импортируем функцию
from sqlalchemy import select, and_
from app.services.balance_service import get_user_balances
import uuid
from datetime import datetime, timezone

router = APIRouter()
from app.schemas.order import LimitOrder, MarketOrder, OrderStatus

def order_to_schema(order: OrderORM):
    if order.type == "MARKET":
        return MarketOrder(
            id=str(order.id),
            status=OrderStatus(order.status),
            user_id=str(order.user_id),
            timestamp=order.timestamp,
            body={
                "direction": order.direction,
                "ticker": order.ticker,
                "qty": order.qty,
                # price НЕ добавляем!
            }
        )
    else:
        return LimitOrder(
            id=str(order.id),
            status=OrderStatus(order.status),
            user_id=str(order.user_id),
            timestamp=order.timestamp,
            filled=order.filled,
            body={
                "direction": order.direction,
                "ticker": order.ticker,
                "qty": order.qty,
                "price": order.price,  # только для LIMIT
            }
        )


@router.post(
    "/order",
    response_model=CreateOrderResponse,
    tags=["order"]
)
async def post_order(
    body: LimitOrderBody | MarketOrderBody,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
    user=Depends(get_current_user)
):
    # === ВСТАВЬ ВОТ ЗДЕСЬ ===

    balances = await get_user_balances(db, user.id)

    if body.direction == "BUY":
        price = getattr(body, "price", None)
        if price is None:
            # MARKET — ищем лучшую встречную заявку SELL
            counter_orders = (await db.execute(
                select(OrderORM).where(
                    and_(
                        OrderORM.ticker == body.ticker,
                        OrderORM.direction == "SELL",
                        OrderORM.status == "NEW"
                    )
                )
            )).scalars().all()
            if not counter_orders:
                raise HTTPException(status_code=400,
                                    detail="Нет встречных заявок для исполнения MARKET-ордерa (покупка)")
            price = min(o.price for o in counter_orders)
        sum_required = body.qty * price
        if balances.get("RUB", 0) < sum_required:
            raise HTTPException(status_code=400, detail="Недостаточно средств для покупки")

    elif body.direction == "SELL":
        if not hasattr(body, "price") or body.price is None:
            # MARKET — ищем лучшую встречную заявку BUY
            counter_orders = (await db.execute(
                select(OrderORM).where(
                    and_(
                        OrderORM.ticker == body.ticker,
                        OrderORM.direction == "BUY",
                        OrderORM.status == "NEW"
                    )
                )
            )).scalars().all()
            if not counter_orders:
                raise HTTPException(status_code=400,
                                    detail="Нет встречных заявок для исполнения MARKET-ордерa (продажа)")
        if balances.get(body.ticker, 0) < body.qty:
            raise HTTPException(status_code=400, detail=f"Недостаточно {body.ticker} для продажи")

    # ========================
    # 1. Создаем объект ордера
    order_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    is_limit = hasattr(body, "price") and body.price is not None

    order = OrderORM(
        id=order_id,
        user_id=user.id,
        ticker=body.ticker,
        direction=body.direction,
        qty=body.qty,
        price=body.price if is_limit else None,
        type="LIMIT" if is_limit else "MARKET",
        status="NEW",
        filled=0,
        timestamp=now
    )

    db.add(order)
    await db.flush()  # Получаем id и подготавливаем к matching

    # 2. Matching engine — исполнение сделки и обновление стакана/балансов
    await match_order(order, db)

    # 3. Отправляем ответ
    return CreateOrderResponse(success=True, order_id=order_id)


from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order as OrderORM
from app.schemas.order import LimitOrder, MarketOrder
from app.dependencies import get_db
from app.core.security import get_current_user


@router.get(
    "/order",
    response_model=list[LimitOrder | MarketOrder],
    tags=["order"]
)
async def list_orders(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
    user=Depends(get_current_user)
):
    # Возвращаем ВСЕ ордера пользователя
    result = await db.execute(
        select(OrderORM).where(OrderORM.user_id == user.id)
    )
    orders = result.scalars().all()
    return [order_to_schema(o) for o in orders]

@router.get(
    "/order/{order_id}",
    response_model=LimitOrder | MarketOrder,
    tags=["order"]
)
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
    user=Depends(get_current_user)
):
    result = await db.execute(
        select(OrderORM).where(OrderORM.id == uuid.UUID(order_id), OrderORM.user_id == user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_to_schema(order)
from fastapi import status

@router.delete(
    "/order/{order_id}",
    tags=["order"]
)
async def delete_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
    user=Depends(get_current_user)
):
    # 1. Находим ордер по id и пользователю
    result = await db.execute(
        select(OrderORM).where(
            OrderORM.id == uuid.UUID(order_id),
            OrderORM.user_id == user.id
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # 2. Проверяем, что ордер можно отменить
    if order.type != "LIMIT" or order.status != "NEW":
        raise HTTPException(status_code=400, detail="Order cannot be cancelled")
    # 3. Ставим статус CANCELLED вместо удаления
    order.status = "CANCELLED"
    await db.commit()
    return {"success": True}
