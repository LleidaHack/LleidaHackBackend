from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db
from app.models import UserConfig
from app.schemas import SchemaUser
from app.database import SessionLocal

client = TestClient(app)


def test_update_user_config():
    # Create a test user config
    user_config = UserConfig(userId=1, someField="value")

    # Mock the database session
    def mock_get_db():
        yield SessionLocal()

    app.dependency_overrides[get_db] = mock_get_db
    
    # Make a request to update the user config
    response = client.put("/userConfig/1", json=user_config.dict())

    # Assert the response status code
    assert response.status_code == 200

    # Assert the response data
    assert response.json() == {"message": "User config updated successfully"}

    # Verify the changes in the database
    db = SessionLocal()
    updated_user_config = db.query(UserConfig).filter(UserConfig.userId == 1).first()
    assert updated_user_config.someField == "value"
