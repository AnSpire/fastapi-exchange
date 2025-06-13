from typing import Dict
from pydantic import BaseModel
BalanceResponse = Dict[str, int]


class BalanceChangeBody(BaseModel):
    user_id: str
    ticker: str
    amount: int
