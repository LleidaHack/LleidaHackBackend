from datetime import date


class Event:
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

class User:
    def __init__(self):
        self.id=0
        self.name=""
        self.nickname=""
        self.password=""
        self.birthdate=0
        self.food_restrictions=[]
        self.email=""
        self.telephone=""
        self.address=""
        self.shirtSize=""

class LleidaHacker(User):
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
    def __init__(self):
        super().__init__()
        self.logo=""
        self.description=""

class Hacker(User):
    def __init__(self):
        super().__init__()
        self.banned=False
        self.github=""
        self.linkdin=""

class Group:
    def __init__(self) -> None:
        self.users=[]
        self.leader=0
        self.name=""