from src.utils.Base.BaseSchema import BaseSchema


class ContactMail(BaseSchema):
    name: str
    title: str
    email: str
    message: str
