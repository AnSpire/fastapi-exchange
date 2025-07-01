# app/models/user.py
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid

class User(Base):
    __tablename__ = "user"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False, default="USER")  # только USER/ADMIN
    api_key = Column(String, unique=True, index=True, nullable=False)
