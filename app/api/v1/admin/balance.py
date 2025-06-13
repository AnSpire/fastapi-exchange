from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.balance import Balance
from app.models.user import User
from app.schemas.balance import BalanceChangeBody
from app.dependencies import get_db
from app.core.security import get_admin_user
router = APIRouter()

@router.post("/balance/deposit")
async def deposit_balance(
    body: BalanceChangeBody,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_admin_user)
):
    # Найти или создать баланс
    result = await db.execute(
        select(Balance).where(Balance.user_id == body.user_id, Balance.ticker == body.ticker)
    )
    bal = result.scalar_one_or_none()
    if bal is None:
        bal = Balance(user_id=body.user_id, ticker=body.ticker, amount=0)
        db.add(bal)
    bal.amount += body.amount
    await db.commit()
    return {"success": True}

@router.post("/balance/withdraw")
async def withdraw_balance(
    body: BalanceChangeBody,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_admin_user)
):
    result = await db.execute(
        select(Balance).where(Balance.user_id == body.user_id, Balance.ticker == body.ticker)
    )
    bal = result.scalar_one_or_none()
    if not bal or bal.amount < body.amount:
        raise HTTPException(status_code=400, detail="Not enough balance")
    bal.amount -= body.amount
    await db.commit()
    return {"success": True}
