# app/services/matching.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.order import Order as OrderORM
from app.models.balance import Balance as BalanceORM
from app.models.transaction import Transaction as TransactionORM
from app.models.user import User as UserORM
from datetime import datetime
from fastapi import HTTPException

import uuid

async def update_balance(db: AsyncSession, user_id, ticker: str, delta: int):
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)
    result = await db.execute(
        select(BalanceORM)
        .where(BalanceORM.user_id == user_id, BalanceORM.ticker == ticker)
        .with_for_update()
    )
    balance = result.scalar_one_or_none()
    if balance is None:
        balance = BalanceORM(user_id=user_id, ticker=ticker, amount=0)
        db.add(balance)
        # Сразу зафиксировать через commit или flush,
        # чтобы другие транзакции увидели новую строку и не пытались добавить свою.
        await db.flush()
    balance.amount += delta
    if balance.amount < 0:
        raise HTTPException(status_code=400, detail="Недостаточно средств")
    return balance



async def match_order(order: OrderORM, db: AsyncSession):
    """
    Исполняет ордер (market/limit), обновляет заявки, балансы и создает сделки.
    """
    trades = []
    ticker = order.ticker
    qty_to_fill = order.qty - (order.filled or 0)
    user_id = order.user_id

    # 1. Определяем встречную сторону
    is_limit = order.price is not None

    if order.direction == "BUY":
        opposite = "SELL"
        order_by = OrderORM.price.asc()
        if is_limit:
            price_filter = OrderORM.price <= order.price
        else:
            price_filter = True
    else:
        opposite = "BUY"
        order_by = OrderORM.price.desc()
        if is_limit:
            price_filter = OrderORM.price >= order.price
        else:
            price_filter = True

    # 3. Находим подходящие встречные заявки
    candidates_query = select(OrderORM).where(
        and_(
            OrderORM.ticker == ticker,
            OrderORM.direction == opposite,
            OrderORM.status == "NEW",
            price_filter
        )
    ).order_by(order_by, OrderORM.timestamp.asc())
    candidates = (await db.execute(candidates_query)).scalars().all()

    # Проверка на наличие встречных для MARKET
    if order.type == "MARKET" and not candidates:
        raise HTTPException(
            status_code=400,
            detail="Нет встречных заявок для исполнения MARKET-ордера"
        )

    # Проверка баланса для BUY/SELL
    from app.services.balance_service import get_user_balances
    balances = await get_user_balances(db, user_id)

    if order.direction == "BUY":
        best_price = min(o.price for o in candidates) if order.type == "MARKET" else order.price
        sum_required = qty_to_fill * best_price
        if balances.get("RUB", 0) < sum_required:
            raise HTTPException(status_code=400, detail="Недостаточно средств для покупки")
    elif order.direction == "SELL":
        if balances.get(ticker, 0) < qty_to_fill:
            raise HTTPException(status_code=400, detail=f"Недостаточно {ticker} для продажи")

    for counter_order in candidates:
        if qty_to_fill <= 0:
            break
        counter_qty_avail = counter_order.qty - (counter_order.filled or 0)
        trade_qty = min(qty_to_fill, counter_qty_avail)
        trade_price = counter_order.price

        # 4. Обновляем встречную заявку
        counter_order.filled = (counter_order.filled or 0) + trade_qty
        if counter_order.filled == counter_order.qty:
            counter_order.status = "EXECUTED"
        else:
            counter_order.status = "PARTIALLY_EXECUTED"

        # 5. Обновляем текущий ордер
        order.filled = (order.filled or 0) + trade_qty

        # 6. Фиксируем сделку
        trade = TransactionORM(
            ticker=ticker,
            amount=trade_qty,
            price=trade_price,
            timestamp=datetime.utcnow()
        )
        db.add(trade)
        trades.append(trade)

        # 7. Обновляем балансы
        # Покупатель: +qty токена, -qty*price денег (примерно, зависит от тикера)
        # Продавец: -qty токена, +qty*price денег
        if order.direction == "BUY":
            # Покупатель (order.user_id) получает токен, отдаёт "деньги"
            await update_balance(db, order.user_id, ticker, trade_qty)
            await update_balance(db, order.user_id, "RUB", -trade_qty * trade_price)
            await update_balance(db, counter_order.user_id, ticker, -trade_qty)
            await update_balance(db, counter_order.user_id, "RUB", trade_qty * trade_price)
        else:
            # Продавец (order.user_id) отдаёт токен, получает "деньги"
            await update_balance(db, order.user_id, ticker, -trade_qty)
            await update_balance(db, order.user_id, "RUB", trade_qty * trade_price)
            await update_balance(db, counter_order.user_id, ticker, trade_qty)
            await update_balance(db, counter_order.user_id, "RUB", -trade_qty * trade_price)

        qty_to_fill -= trade_qty

    # 8. Устанавливаем финальный статус ордера
    if order.filled == order.qty:
        order.status = "EXECUTED"
    elif order.filled > 0:
        order.status = "PARTIALLY_EXECUTED"
    else:
        order.status = "NEW"

    await db.commit()
    return trades
