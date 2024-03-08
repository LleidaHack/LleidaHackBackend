from pydantic import ConfigDict, BaseModel


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
