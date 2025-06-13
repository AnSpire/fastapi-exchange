# app/models/instrument.py
from sqlalchemy import Column, String
from app.db.base import Base

class Instrument(Base):
    __tablename__ = "instrument"
    ticker = Column(String(10), primary_key=True, index=True)  # 2-10 символов, все caps
    name = Column(String, nullable=False)
