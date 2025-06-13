from pydantic import BaseModel, Field
from uuid import UUID

class Body_deposit_api_v1_admin_balance_deposit_post(BaseModel):
    user_id: UUID
    ticker: str = Field(..., pattern="^[A-Z]{2,10}$")
    amount: int = Field(..., gt=0)

class Body_withdraw_api_v1_admin_balance_withdraw_post(BaseModel):
    user_id: UUID
    ticker: str = Field(..., pattern="^[A-Z]{2,10}$")
    amount: int = Field(..., gt=0)

