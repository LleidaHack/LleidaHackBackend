from fastapi import APIRouter

# from services.mail import send_registration_confirmation_email
from generated_src.lleida_hack_mail_api_client.models.mail_create import MailCreate
from src.impl.LleidaHacker.schema import (
    LleidaHackerCreate,
    LleidaHackerGet,
    LleidaHackerGetAll,
    LleidaHackerUpdate,
)
from src.impl.LleidaHacker.service import LleidaHackerService
from src.impl.Mail.client import MailClient
from src.impl.Mail.internall_templates import InternalTemplate
from src.utils.jwt_bearer import jwt_dependency
from src.utils.token import AccesToken, BaseToken, RefreshToken, VerificationToken

router = APIRouter(
    prefix='/lleidahacker',
    tags=['LleidaHacker'],
)

lleidahacker_service = LleidaHackerService()
mail_client = MailClient()


@router.post('/signup')
def signup(payload: LleidaHackerCreate):
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
            subject='Your User Hacker was created',
            fields=f'{new_lleidahacker.name},{verification_token}',
        )
    )
    mail_client.send_mail_by_id(mail.id)
    return {
        'success': True,
        'user_id': new_lleidahacker.id,
        'access_token': access_token,
        'refresh_token': refresh_token,
    }


@router.get('/all', response_model=list[LleidaHackerGet])
def get_all(data: BaseToken | None = jwt_dependency):
    return lleidahacker_service.get_all()


@router.get('/{user_id}', response_model=LleidaHackerGetAll | LleidaHackerGet)
def get(user_id: int, data: BaseToken | None = jwt_dependency):
    return lleidahacker_service.get_lleidahacker(user_id, data)


# @router.post("/")
# def add_lleidahacker(payload: LleidaHacker,
#                            response: Response,
#                            str=jwt_dependency):
#     new_lleidahacker = lleidahacker_service.add_lleidahacker(payload, db)
#     return {"success": True, "user_id": new_lleidahacker.id}


@router.delete('/{user_id}')
def delete(user_id: int, data: BaseToken = jwt_dependency):
    lleidahacker_service.delete_lleidahacker(user_id, data)
    return {'success': True, 'deleted_id': user_id}


@router.put('/{user_id}')
def update(
    user_id: int, payload: LleidaHackerUpdate, token: BaseToken = jwt_dependency
):
    lleidahacker, updated = lleidahacker_service.update_lleidahacker(
        user_id, payload, token
    )
    return {'success': True, 'updated_id': user_id, 'updated': updated}


@router.post('/{user_id}/accept')
def accept(user_id: int, token: BaseToken = jwt_dependency):
    lleidahacker_service.accept_lleidahacker(user_id, token)
    return {'success': True, 'updated_id': user_id}


@router.post('/{user_id}/reject')
def reject(user_id: int, token: BaseToken = jwt_dependency):
    lleidahacker_service.reject_lleidahacker(user_id, token)
    return {'success': True, 'updated_id': user_id}


@router.post('/{user_id}/activate')
def activate(user_id: int, token: BaseToken = jwt_dependency):
    lleidahacker_service.activate_lleidahacker(user_id, token)
    return {'success': True, 'updated_id': user_id}


@router.post('/{user_id}/deactivate')
def deactivate(user_id: int, token: BaseToken = jwt_dependency):
    lleidahacker_service.deactivate_lleidahacker(user_id, token)
    return {'success': True, 'updated_id': user_id}
