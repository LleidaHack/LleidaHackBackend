from src.impl.User.schema import UserCreate, UserGet, UserGetAll, UserUpdate
from src.utils.Base.BaseSchema import BaseSchema


class MentorCreate(UserCreate):
    pass


class MentorGet(UserGet):
    pass


class MentorGetAll(MentorGet, UserGetAll):
    pass


class MentorUpdate(UserUpdate):
    pass
