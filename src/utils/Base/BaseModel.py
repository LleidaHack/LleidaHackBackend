from sqlalchemy.orm import DeclarativeBase


class BaseModel(DeclarativeBase):
    __allow_unmapped__ = True
    pass
