#User model test
import pytest
from datetime import date
from services import user
from utils.mockDB import create_user_model


def test_create(db_session):
    # create test data
    test_user = create_user_model()
    # call the function
    result = user.create(db_session, test_user)
    # assert result
    assert result.name == "testuser"
    assert result.email == "testuser@test.com"
    #assert result.password == "$2b$12$uLGi5FJOvoQWdZ2ORG8HcuxDFCx1Jlvz2PEbFcRCzn6AT35/.JmzG"
    assert result.birthdate == date(2021, 6, 11)
    assert result.food_restrictions == "Peix"
    assert result.telephone == "624444444"
    assert result.address == "asd"
    assert result.shirt_size == "xxxl"
    assert result.type == 'hacker'
    assert result.image_id == ""


def test_get_by_id(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.get_by_id(db_session, test_user.id)
    # assert result
    assert result.name == "testuser"
    assert result.email == "testuser@test.com"
    #assert result.password == "$2b$12$uLGi5FJOvoQWdZ2ORG8HcuxDFCx1Jlvz2PEbFcRCzn6AT35/.JmzG"
    assert result.birthdate == date(2021, 6, 11)
    assert result.food_restrictions == "Peix"
    assert result.telephone == "624444444"
    assert result.address == "asd"
    assert result.shirt_size == "xxxl"
    assert result.type == 'hacker'
    assert result.image_id == ""


def test_delete(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.delete(db_session, test_user.id)
    # assert result
    assert result == 1


def test_update(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # change data
    test_user.name = "testuser2"
    # call the function
    result = user.update(db_session, test_user.id, test_user)
    # assert result
    assert result.name == "testuser2"
    assert result.email == "testuser@test.com"
    #assert result.password == "$2b$12$uLGi5FJOvoQWdZ2ORG8HcuxDFCx1Jlvz2PEbFcRCzn6AT35/.JmzG"
    assert result.birthdate == date(2021, 6, 11)
    assert result.food_restrictions == "Peix"
    assert result.telephone == "624444444"
    assert result.address == "asd"
    assert result.shirt_size == "xxxl"
    assert result.type == 'hacker'
    assert result.image_id == ""


def test_get_by_email(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.get_by_email(db_session, test_user.email)
    # assert result
    assert result.name == "testuser"
    assert result.email == "testuser@test.com"
    #assert result.password == "$2b$12$uLGi5FJOvoQWdZ2ORG8HcuxDFCx1Jlvz2PEbFcRCzn6AT35/.JmzG"
    assert result.birthdate == date(2021, 6, 11)
    assert result.food_restrictions == "Peix"
    assert result.telephone == "624444444"
    assert result.address == "asd"
    assert result.shirt_size == "xxxl"
    assert result.type == 'hacker'
    assert result.image_id == ""


def test_get_by_name(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.get_by_name(db_session, test_user.name)
    # assert result
    assert result.name == "testuser"
    assert result.email == "testuser@test.com"
    #assert result.password == "$2b$12$uLGi5FJOvoQWdZ2ORG8HcuxDFCx1Jlvz2PEbFcRCzn6AT35/.JmzG"
    assert result.birthdate == date(2021, 6, 11)
    assert result.food_restrictions == "Peix"
    assert result.telephone == "624444444"
    assert result.address == "asd"
    assert result.shirt_size == "xxxl"
    assert result.type == 'hacker'
    assert result.image_id == ""


def test_get_by_nickname(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.get_by_nickname(db_session, test_user.nickname)
    # assert result
    assert result.name == "testuser"
    assert result.email == "testuser@test.com"
    #assert result.password == "$2b$12$uLGi5FJOvoQWdZ2ORG8HcuxDFCx1Jlvz2PEbFcRCzn6AT35/.JmzG"
    assert result.birthdate == date(2021, 6, 11)
    assert result.food_restrictions == "Peix"
    assert result.telephone == "624444444"
    assert result.address == "asd"
    assert result.shirt_size == "xxxl"
    assert result.type == 'hacker'
    assert result.image_id == ""


def test_get_by_type(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.get_by_type(db_session, test_user.type)
    # assert result
    assert result.name == "testuser"
    assert result.email == "testuser@test.com"
    #assert result.password == "$2b$12$uLGi5FJOvoQWdZ2ORG8HcuxDFCx1Jlvz2PEbFcRCzn6AT35/.JmzG"
    assert result.birthdate == date(2021, 6, 11)
    assert result.food_restrictions == "Peix"
    assert result.telephone == "624444444"
    assert result.address == "asd"
    assert result.shirt_size == "xxxl"
    assert result.type == 'hacker'
    assert result.image_id == ""


def test_get_by_shirt_size(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.get_by_shirt_size(db_session, test_user.shirt_size)
    # assert result
    assert result.name == "testuser"


def test_get_by_food_restrictions(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.get_by_food_restrictions(db_session,
                                           test_user.food_restrictions)
    # assert result
    assert result.name == "testuser"


def test_get_by_telephone(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.get_by_telephone(db_session, test_user.telephone)
    # assert result
    assert result.name == "testuser"


def test_get_by_address(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.get_by_address(db_session, test_user.address)
    # assert result
    assert result.name == "testuser"


def test_get_by_birthdate(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.get_by_birthdate(db_session, test_user.birthdate)
    # assert result
    assert result.name == "testuser"


def test_get_by_image_id(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.get_by_image_id(db_session, test_user.image_id)
    # assert result
    assert result.name == "testuser"


def test_get_by_email(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.get_by_email(db_session, test_user.email)
    # assert result
    assert result.name == "testuser"


def test_get_by_password(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.get_by_password(db_session, test_user.password)
    # assert result
    assert result.name == "testuser"


def test_get_by_id(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.get_by_id(db_session, test_user.id)
    # assert result
    assert result.name == "testuser"


def test_get_all(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.get_all(db_session)
    # assert result
    assert result[0].name == "testuser"


def test_update(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.update(db_session, test_user.id, name="testuser2")
    # assert result
    assert result.name == "testuser2"
    assert result.email == "testuser@test.com"


def test_delete(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.delete(db_session, test_user.id)
    # assert result
    assert result == True


def test_delete_by_name(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.delete_by_name(db_session, test_user.name)
    # assert result
    assert result == True


def test_delete_by_email(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.delete_by_email(db_session, test_user.email)
    # assert result
    assert result == True


def test_delete_by_password(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.delete_by_password(db_session, test_user.password)
    # assert result
    assert result == True


def test_delete_by_birthdate(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.delete_by_birthdate(db_session, test_user.birthdate)
    # assert result
    assert result == True


def test_delete_by_address(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.delete_by_address(db_session, test_user.address)
    # assert result
    assert result == True


def test_delete_by_telephone(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.delete_by_telephone(db_session, test_user.telephone)
    # assert result
    assert result == True


def test_delete_by_image_id(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.delete_by_image_id(db_session, test_user.image_id)
    # assert result
    assert result == True


def test_delete_by_id(db_session):
    # create test data
    test_user = create_user_model()
    db_session.add(test_user)
    db_session.commit()
    # call the function
    result = user.delete_by_id(db_session, test_user.id)
    # assert result
    assert result == True
