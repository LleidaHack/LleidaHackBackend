from datetime import date
from pydantic import BaseModel
from dataclasses import dataclass

class Event(BaseModel):
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
@dataclass
class User():
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

class LleidaHacker(User):
    role: str
    nif: str
    student: bool
    active: bool
    image: str
    groups: list
    github: str
    def __init__(self):
        super().__init__()
        self.role=""
        self.nif=""
        self.student=True
        self.active=True
        self.image=""
        #principal group on the first position
        self.groups=[]
        self.github=""

class Company(User):
    logo: str
    description: str
    def __init__(self):
        super().__init__()
        self.logo=""
        self.description=""

class Hacker(User):
    banned: bool
    github: str
    linkdin: str
    def __init__(self):
        super().__init__()
        self.banned=False
        self.github=""
        self.linkdin=""

class Group(BaseModel):
    id: int
    name: str
    description: str
    members: list
    leader: int
    def __init__(self):
        self.id=0
        self.name=""
        self.description=""
        self.members=[]
        self.leader=0

class EventGroup(BaseModel):
    id: int
    name: str
    leader: int
    users: list
    def __init__(self) -> None:
        self.name=""
        self.users=[]
        self.leader=0
        self.name=""