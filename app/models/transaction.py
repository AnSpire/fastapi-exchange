from sqlalchemy import Column, String, Integer, DateTime
from app.db.base import Base

class Transaction(Base):
    __tablename__ = "transaction"
    id = Column(String, primary_key=True)
    ticker = Column(String)
    amount = Column(Integer)
    price = Column(Integer)
    timestamp = Column(DateTime)
