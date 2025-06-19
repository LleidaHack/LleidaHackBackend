from src.impl.User.schema import UserCreate, UserGet, UserGetAll, UserUpdate


class MentorCreate(UserCreate):
    pass


class MentorGet(UserGet):
    pass


class MentorGetAll(MentorGet, UserGetAll):
    pass


class MentorUpdate(UserUpdate):
    pass
