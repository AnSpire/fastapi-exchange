from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Union
from pydantic import UUID4
from enum import Enum
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
    ticker: str
    qty: int = Field(..., ge=1)
    price: int = Field(..., gt=0)  # exclusiveMinimum=0

    model_config = ConfigDict(extra="forbid")

class MarketOrderBody(BaseModel):
    direction: Direction
    ticker: str
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
from pydantic import BaseModel, Field


class CreateOrderResponse(BaseModel):
    success: bool = Field(True, Literal=True)
    order_id: UUID4

OrderModel = Union[LimitOrder, MarketOrder]

class Level(BaseModel):
    price: int
    qty: int

class L2OrderBook(BaseModel):
    bid_levels: list[Level]
    ask_levels: list[Level]
