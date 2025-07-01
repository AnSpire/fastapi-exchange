from pydantic import BaseModel
from typing import Literal

class Ok(BaseModel):
    success: Literal[True] = True
