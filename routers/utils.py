from fastapi import Depends, APIRouter
from fastapi import UploadFile, File

# from database import get_db
from security import oauth_schema
import services.utils as utils_service
import services.mail as email_service

router = APIRouter(
    prefix="/utils",
    tags=["Utils"],
)


# @router.post("/uploadImage")
# async def uploadFile(image: UploadFile = File(...),
#                      token: str = Depends(oauth_schema)):
#     id = await utils_service.uploadFile(image)
#     return {"success": True, "id": id}


# @router.get("/getImage/{image_id}")
# async def get_image(image_id: str):
#     return await utils_service.getFile(image_id)


@router.post("/sendMail/{to}")
async def send_mail(to: str):
    # async def send_mail(to:str, backgroundTask:BackgroundTask):
    # backgroundTask.add_task(email_service.send_mail, to)
    email_service.send_mail(to)
