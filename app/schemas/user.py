# app/schemas/user.py
from pydantic import BaseModel, ConfigDict

class NewUser(BaseModel):
    name: str
    model_config = ConfigDict(extra="forbid")  # чтобы не принималось ничего лишнего

class User(BaseModel):
    id: str  # UUID4
    name: str
    role: str
    api_key: str

    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    user: User
