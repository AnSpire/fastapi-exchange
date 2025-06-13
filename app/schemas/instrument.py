from pydantic import BaseModel, ConfigDict

class Instrument(BaseModel):
    name: str
    ticker: str

    model_config = ConfigDict(from_attributes=True)
