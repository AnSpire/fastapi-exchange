from sqlalchemy import Column, String, Integer, ForeignKey
from app.db.base import Base

class Balance(Base):
    __tablename__ = "balance"
    user_id = Column(String, ForeignKey("user.id"), primary_key=True)
    ticker = Column(String, primary_key=True)
    amount = Column(Integer, nullable=False, default=0)
