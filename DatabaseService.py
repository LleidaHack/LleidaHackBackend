from Models import Event, User
from PostgresConnector import PostgresConnector
from PostgresTables import PostgresTable


class DatabaseService():
    def __init__(self):
        self.connector=PostgresConnector()

    def getUsers(self) -> list:
        return self.connector.select("SELECT * FROM llhk_user")
    def getUser(self, id: int) -> list:
        return self.connector.select("SELECT * FROM llhk_user WHERE user_id = %s" % id)
    def addUser(self, user: User):
        self.connector.insert(PostgresTable.get_table("llhk_user").get_insert(), (user.name, user.password, user.email, user.nickname, user.birthdate, user.telephone, user.food_restrictions, user.shirt_size))
        # return self.connector.select("INSERT INTO llhk_user (name, password, email, nickname, birthday, phone_number, food_restrictions, shirt_size) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (user.name, user.password, user.email, user.nickname, user.birthdate, user.telephone, user.food_restrictions, user.shirt_size))
    def updateUser(self, user: User):
        return self.connector.select("UPDATE llhk_user SET name = %s, password = %s, email = %s, nickname = %s, birthdate = %s, phone_number = %s, food_restrictions = %s, shirt_size = %s WHERE id = %s", (user.name, user.password, user.email, user.nickname, user.birthdate, user.telephone, user.food_restrictions, user.shirt_size, user.id))
    def deleteUser(self, id: int):
        return self.connector.select("DELETE FROM llhk_user WHERE id = %s", (id))
    def banUser(self, id: int):
        return self.connector.select("UPDATE llhk_user SET banned = %s WHERE id = %s", (0, id))
    def unbanUser(self, id: int):
        return self.connector.select("UPDATE llhk_user SET banned = %s WHERE id = %s", (1, id))
     
    def getEvents(self) -> list:
        return self.connector.select("SELECT * FROM events")
    def getEvent(self, id: int) -> list:
        return self.connector.select("SELECT * FROM events WHERE id = %s" % id)
    def addEvent(self, event: Event):
        return self.connector.select("INSERT INTO events (name, description, date, time, location, status) VALUES (%s, %s, %s, %s, %s, %s)", (event.name, event.description, event.date, event.time, event.location, event.status))
    def updateEvent(self, event: Event):
        return self.connector.select("UPDATE events SET name = %s, description = %s, date = %s, time = %s, location = %s, status = %s WHERE id = %s", (event.name, event.description, event.date, event.time, event.location, event.status, event.id))
    def deleteEvent(self, id: int):
        return self.connector.select("DELETE FROM events WHERE id = %s", (id))
    