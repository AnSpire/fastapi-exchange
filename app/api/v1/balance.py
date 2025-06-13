from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.balance_service import get_user_balances
from app.core.security import get_current_user
from app.dependencies import get_db
from fastapi import Header
router = APIRouter()

@router.get("/balance", response_model=Dict[str, int])
async def balance(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
    user=Depends(get_current_user)
):
    return await get_user_balances(db, user.id)
