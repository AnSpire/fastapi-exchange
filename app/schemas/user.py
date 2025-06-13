from pydantic import BaseModel, ConfigDict, Field
from pydantic import UUID4
from enum import Enum

class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class NewUser(BaseModel):
    name: str = Field(..., min_length=3)
    model_config = ConfigDict(extra="forbid")

class User(BaseModel):
    id: UUID4 = Field(..., description="User UUID (uuid4)")
    name: str
    role: UserRole
    api_key: str
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    user: User
