from pydantic import BaseModel, Field
from typing import List

class Instrument(BaseModel):
    name: str
    ticker: str = Field(..., pattern="^[A-Z]{2,10}$")

