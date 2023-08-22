from fastapi import Depends, APIRouter
from fastapi import UploadFile, File

# from database import get_db
from security import oauth_schema
import services.utils as utils_service
import services.mail as email_service

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from database import get_db
router = APIRouter(
    prefix="/utils",
    tags=["Utils"],
)

@router.post("/send-email")
async def send_email(email: str, template: str, db: Session = Depends(get_db)):
    try:
        email_service.send_email(email, template)
        return {"success": True, "message": "Email sent successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}
