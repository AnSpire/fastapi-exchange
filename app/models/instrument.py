from sqlalchemy import Column, String
from app.db.base import Base

class Instrument(Base):
    __tablename__ = "instrument"
    ticker = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
