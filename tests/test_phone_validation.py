import pytest
from pydantic import ValidationError

from src.impl.User.schema import UserCreate


@pytest.mark.parametrize(
    "telephone",
    [
        "600123456",
        "+34600123456",
        "+447700900123",
        "+358401234567",
        "+12025550123",
        "+1234567",
        "+123456789012345",
        " +44 7700 900123 ",
    ],
)
def test_phone_accepts_supported_formats(telephone, signup_payload):
    payload = UserCreate.model_validate({**signup_payload, "telephone": telephone})
    assert payload.telephone == "".join(telephone.split())


@pytest.mark.parametrize(
    "telephone",
    [
        "",
        "12345678",
        "1234567890",
        "+0123456789",
        "+123456",
        "+1234567890123456",
        "/34600123456",
        "++447700900123",
        "+44abc900123",
        "+44-7700900123",
        "600123456\nextra",
        "６００１２３４５６",
    ],
)
def test_phone_rejects_invalid_formats(telephone, signup_payload):
    with pytest.raises(ValidationError):
        UserCreate.model_validate({**signup_payload, "telephone": telephone})


def test_signup_accepts_and_stores_international_phone(client, engine, signup_payload):
    from sqlalchemy.orm import Session

    from src.impl.User.model import User

    response = client.post(
        "/v1/hacker/signup",
        json={
            **signup_payload,
            "telephone": " +44 7700 900123 ",
        },
    )
    assert response.status_code == 200, response.text
    with Session(engine) as session:
        user = session.get(User, response.json()["user_id"])
        assert user.telephone == "+447700900123"
