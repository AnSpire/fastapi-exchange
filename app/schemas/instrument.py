from pydantic import BaseModel, Field, ConfigDict
import re

class Instrument(BaseModel):
    name: str
    ticker: str = Field(..., pattern="^[A-Z]{2,10}$")
    model_config = ConfigDict(from_attributes=True)
