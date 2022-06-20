from fastapi import Depends, APIRouter
from fastapi import UploadFile, File

# from database import get_db
from security import oauth_schema
import services.utils as utils_service 
import services.email as email_service 


router = APIRouter(
    prefix="/utils",
    tags=["Utils"],
)


@router.post("/uploadImage")
async def uploadFile(image:UploadFile = File(...), token:str = Depends(oauth_schema)):
    id = utils_service.writeFile(image)
    return {"success": True, "id": id}

async def send_email(to:str, backgroundTask:BackgroundTask):
    backgroundTask.add_task(email_service.send_email, to)