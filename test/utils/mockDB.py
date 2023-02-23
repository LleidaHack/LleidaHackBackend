#A mock for the database
import pytest
from datetime import date
from models.User import User

@pytest.fixture(scope='function')
def db_session(sqlite_session):
    yield sqlite_session

# Create a user
def create_user_model():
    return User(name="testuser",
                     nickname="useruser",
                     password="123_aAaS321",
                     # hash from password "123_aAaS321"
                     birthdate=date(2021, 6, 11),
                     food_restrictions="Peix",
                     email="testuser@test.com",
                     telephone="624444444",
                     address="asd",
                     shirt_size="xxxl",
                     type='hacker',
                     image_id="")