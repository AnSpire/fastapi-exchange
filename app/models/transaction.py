from sqlalchemy import Column, String, Integer, DateTime
from app.db.base import Base
import datetime

class Transaction(Base):
    __tablename__ = "transaction"

    id = Column(String, primary_key=True, index=True)  # UUID строкой
    ticker = Column(String, index=True)
    amount = Column(Integer)
    price = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
