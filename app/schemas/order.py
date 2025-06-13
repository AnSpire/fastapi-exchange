# app/schemas/order.py

from pydantic import BaseModel, ConfigDict
from typing import Literal, Union
from datetime import datetime

class LimitOrderBody(BaseModel):
    direction: Literal["BUY", "SELL"]
    ticker: str
    qty: int
    price: int
    model_config = ConfigDict(extra="forbid")

class MarketOrderBody(BaseModel):
    direction: Literal["BUY", "SELL"]
    ticker: str
    qty: int
    model_config = ConfigDict(extra="forbid")

class LimitOrder(BaseModel):
    id: str
    status: str
    user_id: str
    timestamp: datetime
    body: LimitOrderBody
    filled: int = 0
    model_config = ConfigDict(from_attributes=True)

class MarketOrder(BaseModel):
    id: str
    status: str
    user_id: str
    timestamp: datetime
    body: MarketOrderBody
    model_config = ConfigDict(from_attributes=True)

class CreateOrderResponse(BaseModel):
    success: bool
    order_id: str


from typing import List

class Level(BaseModel):
    price: int
    qty: int

class L2OrderBook(BaseModel):
    bid_levels: List[Level]
    ask_levels: List[Level]


OrderBody = Union[LimitOrderBody, MarketOrderBody]
