# app/models/transaction.py
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import datetime
import uuid

class Transaction(Base):
    __tablename__ = "transaction"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticker = Column(String(10), index=True)
    amount = Column(Integer)
    price = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
