from Models import Event, Group, User
from fastapi import FastAPI



app = FastAPI()

@app.get("/users")
def getUsers():
    pass

@app.get("/user/{userId}")
def getUser(userId:int):
    pass

@app.post("/user")
def addUser(payload:User):
    pass

@app.post("/user/{userId}/remove")
def removeUser(userId:int):
    pass

@app.post("/user/{userId}/ban")
def banUser(userId:int):
    pass





@app.get("/events")
def getEvents():
    pass

@app.get("/event/{eventId}")
def getEvent(eventId:int):
    pass

@app.post("/event")
def addEvent(payload:Event):
    pass

@app.get("/event/{eventId}/users")
def getEventUsers(eventId:int):
    pass

@app.post("/event/{eventId}/add/{userId}")
def addUserEvent(eventId:int, userId:int):
    pass

@app.post("/event/{eventId}/remove")
def removeEvent(eventId:int):
    pass




@app.get("/groups")
def getGroups():
    pass

@app.post("/group")
def addGroup(payload:Group):
    pass

@app.get("/group/{groupId}")
def getGroup(groupId:int):
    pass

@app.post("/group/{groupId}/remove")
def removeGroup(groupId:int):
    pass

