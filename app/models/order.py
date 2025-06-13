from sqlalchemy import Column, String, Integer, DateTime
from app.db.base import Base
import datetime

class Order(Base):
    __tablename__ = "order"
    id = Column(String(36), primary_key=True, index=True)   # UUID4 строкой
    user_id = Column(String(36), index=True)                # UUID4 строкой
    type = Column(String)                                   # "LIMIT" или "MARKET"
    direction = Column(String)                              # "BUY" или "SELL"
    ticker = Column(String)
    qty = Column(Integer)
    price = Column(Integer, nullable=True)                  # nullable только для MARKET
    status = Column(String, default="NEW")                  # enum значений
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
