from pydantic import BaseModel, Field, ConfigDict, UUID4

class Body_deposit_api_v1_admin_balance_deposit_post(BaseModel):
    user_id: UUID4
    ticker: str = Field(..., pattern="^[A-Z]{2,10}$")
    amount: int = Field(..., gt=0)
    model_config = ConfigDict(extra="forbid")

class Body_withdraw_api_v1_admin_balance_withdraw_post(BaseModel):
    user_id: UUID4
    ticker: str = Field(..., pattern="^[A-Z]{2,10}$")
    amount: int = Field(..., gt=0)
    model_config = ConfigDict(extra="forbid")
