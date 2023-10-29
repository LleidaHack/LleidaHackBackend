from ast import List
from models.User import User
from models.Medal import Medal
from models.Event import Event
#get all users
#iterate for users
    # for each user get its data and analyze if will recive medal
    # send medal

# condition= $user.creation_dat < 1 
    #Events={evntid:((name, winner?))}
def meets(medal: Medal, user: User, events: List):
    fields=[f for f in medal.condition.split(' ') if f[0]=='$']
    vals=[getattr(user, f[1+len('user'):]) for f in fields]
    cond=medal.condition.format(dict(zip(fields,vals)))
    return eval(cond)
