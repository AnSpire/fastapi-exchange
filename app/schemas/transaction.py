from pydantic import BaseModel
from datetime import datetime

class Transaction(BaseModel):
    ticker: str
    amount: int
    price: int
    timestamp: datetime
