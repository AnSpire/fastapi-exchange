from sqlalchemy import Column, String, Integer, DateTime
from app.db.base import Base
import datetime

class Order(Base):
    __tablename__ = "order"
    id = Column(String, primary_key=True, index=True)   # <--- ОБЯЗАТЕЛЬНО!
    user_id = Column(String, index=True)
    type = Column(String)  # "LIMIT" или "MARKET"
    direction = Column(String)
    ticker = Column(String)
    qty = Column(Integer)
    price = Column(Integer, nullable=True)
    status = Column(String, default="NEW")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    @property
    def body(self):
        if self.type == "LIMIT":
            return {
                "direction": self.direction,
                "ticker": self.ticker,
                "qty": self.qty,
                "price": self.price
            }
        else:
            return {
                "direction": self.direction,
                "ticker": self.ticker,
                "qty": self.qty
            }
