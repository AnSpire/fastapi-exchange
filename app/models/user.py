# app/models/user.py
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, String
from app.db.base import Base

class User(Base):
    __tablename__ = "user"
    id = Column(String, primary_key=True, index=True)  # UUID
    name = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False, default="USER")  # USER/ADMIN
    api_key = Column(String, unique=True, index=True, nullable=False)
class NewUser(BaseModel):
    name: str
    model_config = ConfigDict(extra="forbid")
