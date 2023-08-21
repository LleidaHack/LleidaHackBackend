from datetime import date
from sqlalchemy import Column, DateTime, Integer, String
from database import Base
# from passlib import hash


class User(Base):
    __tablename__ = 'user'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    nickname: str = Column(String)
    password: str = Column(String)
    birthdate: date = Column(DateTime)
    food_restrictions: str = Column(String)
    email: str = Column(String, unique=True)
    telephone: str = Column(String)
    address: str = Column(String)
    shirt_size: str = Column(String)
    type: str = Column(String)
    image: str = Column(String)
    is_image_url: bool = Column(Integer, default=False)

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": type,
    }

    # def verify_password(self, password):
    # return hash.verify(password, self.password)
