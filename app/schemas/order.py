from pydantic import BaseModel, ConfigDict, Field, UUID4, constr
from enum import Enum
from typing import Literal, Union, List
from datetime import datetime

class OrderStatus(str, Enum):
    NEW = "NEW"
    EXECUTED = "EXECUTED"
    PARTIALLY_EXECUTED = "PARTIALLY_EXECUTED"
    CANCELLED = "CANCELLED"

class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class LimitOrderBody(BaseModel):
    direction: Direction
    ticker: str = Field(..., pattern="^[A-Z]{2,10}$")
    qty: int = Field(..., ge=1)
    price: int = Field(..., gt=0)
    model_config = ConfigDict(extra="forbid")

class MarketOrderBody(BaseModel):
    direction: Direction
    ticker: str = Field(..., pattern="^[A-Z]{2,10}$")
    qty: int = Field(..., ge=1)
    model_config = ConfigDict(extra="forbid")

class LimitOrder(BaseModel):
    id: UUID4
    status: OrderStatus
    user_id: UUID4
    timestamp: datetime
    body: LimitOrderBody
    filled: int = 0
    model_config = ConfigDict(from_attributes=True)

class MarketOrder(BaseModel):
    id: UUID4
    status: OrderStatus
    user_id: UUID4
    timestamp: datetime
    body: MarketOrderBody
    model_config = ConfigDict(from_attributes=True)

class CreateOrderResponse(BaseModel):
    success: Literal[True] = True
    order_id: UUID4
class Level(BaseModel):
    price: int
    qty: int

class L2OrderBook(BaseModel):
    bid_levels: List[Level]
    ask_levels: List[Level]

OrderModel = Union[LimitOrder, MarketOrder]
