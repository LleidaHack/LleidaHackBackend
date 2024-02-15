from pydantic import BaseModel
from typing import Optional

class LleidaHackerGroupCreate(BaseModel):
    name: str
    description: str

    # leader: int
    class Config:
        orm_mode = True

class LleidaHackerGroupGet(BaseModel):
    name: str
    description: str

class LleidaHackerGroupGetAll(BaseModel):
    pass

class LleidaHackerGroupUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    # leader: Optional[int]
