from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.models.balance import Balance
from app.core.security import get_admin_user
from app.dependencies import get_db
from app.schemas.ok import Ok
from pydantic import BaseModel, Field
from app.schemas.balance import Body_deposit_api_v1_admin_balance_deposit_post, Body_withdraw_api_v1_admin_balance_withdraw_post
# Схемы строго по openapi.json!


router = APIRouter()

@router.post("/balance/deposit", response_model=Ok)
async def deposit_balance(
    body: Body_deposit_api_v1_admin_balance_deposit_post,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
    admin=Depends(get_admin_user)
):
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

@router.post("/balance/withdraw", response_model=Ok)
async def withdraw_balance(
    body: Body_withdraw_api_v1_admin_balance_withdraw_post,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
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
