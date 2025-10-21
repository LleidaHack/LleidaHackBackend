from typing import List, Optional, Union

from fastapi import APIRouter, Depends

# from services.mail import send_registration_confirmation_email
from generated_src.lleida_hack_mail_api_client.models.mail_create import MailCreate
from src.error import AuthenticationException
from src.impl.LleidaHacker.schema import LleidaHackerCreate
from src.impl.LleidaHacker.schema import LleidaHackerGet
from src.impl.LleidaHacker.schema import LleidaHackerGetAll
from src.impl.LleidaHacker.schema import LleidaHackerUpdate
from src.impl.LleidaHacker.service import LleidaHackerService
from src.impl.Mail.client import MailClient
from src.impl.Mail.internall_templates import InternalTemplate
from src.utils.UserType import UserType
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import AccesToken, BaseToken, RefreshToken, VerificationToken

router = APIRouter(
    prefix="/lleidahacker",
    tags=["LleidaHacker"],
)

lleidahacker_service = LleidaHackerService()
mail_client = MailClient()

@router.post("/signup")
def signup(payload: LleidaHackerCreate, token: BaseToken = Depends(JWTBearer())):
   if not token.check([UserType.LLEIDAHACKER]):
       raise AuthenticationException("Not authorized")

   new_lleidahacker = lleidahacker_service.add_lleidahacker(payload)
   access_token = AccesToken(new_lleidahacker).user_set()
   refresh_token = RefreshToken(new_lleidahacker).user_set()
   verification_token = VerificationToken(new_lleidahacker).user_set()

   mail = mail_client.create_mail(
       MailCreate(
           template_id=mail_client.get_internall_template_id(
               InternalTemplate.USER_CREATED
           ),
           receiver_id=str(new_lleidahacker.id),
           receiver_mail=new_lleidahacker.email,
           subject="Your User Hacker was created",
           fields=f"{new_lleidahacker.name},{verification_token}",
       )
   )
   mail_client.send_mail_by_id(mail.id)
   return {
       "success": True,
       "user_id": new_lleidahacker.id,
       "access_token": access_token,
       "refresh_token": refresh_token,
   }


@router.get("/all", response_model=List[LleidaHackerGet])
def get_all(str: Optional[BaseToken] = Depends(JWTBearer())):
    return lleidahacker_service.get_all()


@router.get("/{userId}", response_model=Union[LleidaHackerGetAll, LleidaHackerGet])
def get(userId: int, data: Optional[BaseToken] = Depends(JWTBearer())):
    return lleidahacker_service.get_lleidahacker(userId, data)


# @router.post("/")
# def add_lleidahacker(payload: LleidaHacker,
#                            response: Response,
#                            str=Depends(JWTBearer())):
#     new_lleidahacker = lleidahacker_service.add_lleidahacker(payload, db)
#     return {"success": True, "user_id": new_lleidahacker.id}


@router.delete("/{userId}")
def delete(userId: int, data: BaseToken = Depends(JWTBearer())):
    lleidahacker_service.delete_lleidahacker(userId, data)
    return {"success": True, "deleted_id": userId}


@router.put("/{userId}")
def update(
    userId: int, payload: LleidaHackerUpdate, token: BaseToken = Depends(JWTBearer())
):
    _, updated = lleidahacker_service.update_lleidahacker(userId, payload, token)
    return {"success": True, "updated_id": userId, "updated": updated}


@router.post("/{userId}/accept")
def accept(userId: int, token: BaseToken = Depends(JWTBearer())):
    lleidahacker_service.accept_lleidahacker(userId, token)
    return {"success": True, "updated_id": userId}


@router.post("/{userId}/reject")
def reject(userId: int, token: BaseToken = Depends(JWTBearer())):
    lleidahacker_service.reject_lleidahacker(userId, token)
    return {"success": True, "updated_id": userId}


@router.post("/{userId}/activate")
def activate(userId: int, token: BaseToken = Depends(JWTBearer())):
    lleidahacker_service.activate_lleidahacker(userId, token)
    return {"success": True, "updated_id": userId}


@router.post("/{userId}/deactivate")
def deactivate(userId: int, token: BaseToken = Depends(JWTBearer())):
    lleidahacker_service.deactivate_lleidahacker(userId, token)
    return {"success": True, "updated_id": userId}
