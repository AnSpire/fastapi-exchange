from pydantic import BaseModel, Field

class Ok(BaseModel):
    success: bool = Field(True, Literal=True)
