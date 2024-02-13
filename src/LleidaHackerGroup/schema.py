from pydantic import BaseModel
from typing import Optional

class LleidaHackerGroup(BaseModel):
    name: str
    description: str

    # leader: int
    class Config:
        orm_mode = True


class LleidaHackerGroupUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    # leader: Optional[int]
