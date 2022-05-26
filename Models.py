from datetime import date
from pydantic import BaseModel
from dataclasses import dataclass

@dataclass
class Event():
    id: int
    name: str
    date: date
    users: list
    location: str
    sponsors: list
    archived: bool
    description: str
    status: int
    def __init__(self,event_id:int,name:str,date:date,location:str,description:str,status:int,sponsors:list=[]):
        self.id=id
        self.name=name
        self.date=date
        self.users=[]
        self.location=location
        self.sponsors=sponsors
        self.archived=False
        self.description=description
        self.status=status

# @dataclass
class User(BaseModel):
    id: int
    name: str
    nickname: str
    password: str
    birthdate: date
    food_restrictions: str
    email: str
    telephone: str
    address: str
    shirtSize: str

    def __init__(self,name:str,nickname:str,password:str,birthdate:date,food_restrictions:str,email:str,telephone:str,address:str,shirtSize:str,user_id:int=None):
        self.id=user_id
        self.name=name
        self.nickname=nickname
        self.password=password
        self.birthdate=birthdate
        self.food_restrictions=food_restrictions
        self.email=email
        self.telephone=telephone
        self.address=address
        self.shirt_size=shirtSize

# @dataclass
# class LleidaHacker(User):
#     role: str
#     nif: str
#     student: bool
#     active: bool
#     image: str
#     groups: list
#     github: str
#     def __init__(self,name:str,nickname:str,password:str,birthdate:date,food_restrictions:str,email:str,telephone:str,address:str,shirtSize:str,user_id:int=None,role:str="",nif:str="",student:bool=False,active:bool=False,image:str="",groups:list=[],github:str=""):
#         super().__init__(name,nickname,password,birthdate,food_restrictions,email,telephone,address,shirtSize,user_id)
#         self.role=role
#         self.nif=nif
#         self.student=student
#         self.active=active
#         self.image=image
#         #principal group on the first position
#         self.groups=groups
#         self.github=github

# @dataclass
# class Company(User):
#     logo: str
#     description: str
#     def __init__(self, name: str, nickname: str, password: str, birthdate: date, food_restrictions: str, email: str, telephone: str, address: str, shirtSize: str, user_id: int = None, logo: str = "", description: str = ""):
#         super().__init__(name, nickname, password, birthdate, food_restrictions, email, telephone, address, shirtSize, user_id)
#         self.logo=logo
#         self.description=description

# @dataclass
# class Hacker(User):
#     banned: bool
#     github: str
#     linkdin: str
#     def __init__(self, name: str, nickname: str, password: str, birthdate: date, food_restrictions: str, email: str, telephone: str, address: str, shirtSize: str, user_id: int = None, banned: bool = False, github: str = "", linkdin: str = ""):
#         super().__init__(name, nickname, password, birthdate, food_restrictions, email, telephone, address, shirtSize, user_id)
#         self.banned=banned
#         self.github=github
#         self.linkdin=linkdin

@dataclass
class Group():
    id: int
    name: str
    description: str
    members: list
    leader: int
    def __init__(self, name: str, description: str, members: list, leader: int, group_id: int = None):
        self.id=group_id
        self.name=name
        self.description=description
        self.members=members
        self.leader=leader

@dataclass
class EventGroup():
    id: int
    name: str
    leader: int
    users: list
    def __init__(self, name:str, leader:int, users:list, id:int = None ) -> None:
        self.name=""
        self.users=[]
        self.leader=0
        self.name=""