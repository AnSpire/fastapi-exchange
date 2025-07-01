# app/models/order.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import datetime
import uuid

class Order(Base):
    __tablename__ = "order"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), index=True)
    type = Column(String)        # "LIMIT" или "MARKET"
    direction = Column(String)   # "BUY" или "SELL"
    ticker = Column(String(10))
    qty = Column(Integer)
    price = Column(Integer, nullable=True)  # nullable только для MARKET
    status = Column(String, default="NEW")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
