from config import Configuration
from fastapi import FastAPI
from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema,ConnectionConfig
from pydantic import EmailStr, BaseModel
from typing import List

class EmailSchema(BaseModel):
    email: List[EmailStr]


# conf = ConnectionConfig(
#     MAIL_USERNAME = Configuration.get('MAIL', 'MAIL_USERNAME'),
#     MAIL_PASSWORD = Configuration.get('MAIL', 'MAIL_PASSWORD'),
#     MAIL_FROM = Configuration.get('MAIL', 'MAIL_FROM'),
#     MAIL_PORT = int(Configuration.get('MAIL', 'MAIL_PORT')),
#     MAIL_SERVER = Configuration.get('MAIL', 'MAIL_SERVER'),
#     MAIL_FROM_NAME = Configuration.get('MAIL', 'MAIL_FROM_NAME'),
#     MAIL_TLS = True,
#     MAIL_SSL = False,
#     USE_CREDENTIALS = True,
#     VALIDATE_CERTS = True
# )

app = FastAPI()


html = """<p>Hi this test mail, thanks for using Fastapi-mail</p> """


async def simple_send(email: EmailSchema) -> JSONResponse:
    pass
    # message = MessageSchema(
    #     subject="Fastapi-Mail module",
    #     recipients=email.dict().get("email"),  # List of recipients, as many as you can pass 
    #     body=html,
    #     subtype="html"
    # )

    # fm = FastMail(conf)
    # await fm.send_message(message)
    # return JSONResponse(status_code=200, content={"message": "email has been sent"})