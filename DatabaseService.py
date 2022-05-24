from Models import Event, User
from PostgresConnector import PostgresConnector


class DatabaseService():
    def __init__(self):
        self.connector=PostgresConnector()

    def getUsers(self) -> list:
        return self.connector.execute_query("SELECT * FROM users")
    def getUser(self, id: int) -> list:
        return self.connector.execute_query("SELECT * FROM users WHERE user_id = %s" % id)
    def addUser(self, user: User):
        return self.connector.execute_query("INSERT INTO users (name, password, email, nickname, birthdate, phone_number, food_restrictions, shirt_size) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (user.name, user.password, user.email, user.nickname, user.birthdate, user.phone_number, user.food_restrictions, user.shirt_size))
    def updateUser(self, user: User):
        return self.connector.execute_query("UPDATE users SET name = %s, password = %s, email = %s, nickname = %s, birthdate = %s, phone_number = %s, food_restrictions = %s, shirt_size = %s WHERE id = %s", (user.name, user.password, user.email, user.nickname, user.birthdate, user.phone_number, user.food_restrictions, user.shirt_size, user.id))
    def deleteUser(self, id: int):
        return self.connector.execute_query("DELETE FROM users WHERE id = %s", (id))
    def banUser(self, id: int):
        return self.connector.execute_query("UPDATE users SET banned = %s WHERE id = %s", (0, id))
    def unbanUser(self, id: int):
        return self.connector.execute_query("UPDATE users SET banned = %s WHERE id = %s", (1, id))
     
    def getEvents(self) -> list:
        return self.connector.execute_query("SELECT * FROM events")
    def getEvent(self, id: int) -> list:
        return self.connector.execute_query("SELECT * FROM events WHERE id = %s" % id)
    def addEvent(self, event: Event):
        return self.connector.execute_query("INSERT INTO events (name, description, date, time, location, status) VALUES (%s, %s, %s, %s, %s, %s)", (event.name, event.description, event.date, event.time, event.location, event.status))
    def updateEvent(self, event: Event):
        return self.connector.execute_query("UPDATE events SET name = %s, description = %s, date = %s, time = %s, location = %s, status = %s WHERE id = %s", (event.name, event.description, event.date, event.time, event.location, event.status, event.id))
    def deleteEvent(self, id: int):
        return self.connector.execute_query("DELETE FROM events WHERE id = %s", (id))
    