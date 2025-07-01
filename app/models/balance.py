# app/models/balance.py
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid

class Balance(Base):
    __tablename__ = "balance"
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), primary_key=True)
    ticker = Column(String(10), primary_key=True)
    amount = Column(Integer, nullable=False, default=0)
