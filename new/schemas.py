from lib2to3.pytree import Base
from pydantic import BaseModel

class CreateJobRequest(BaseModel):
    title:str
    description:str
