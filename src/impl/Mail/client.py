from http import HTTPStatus
from typing import Any
from generated_src.lleida_hack_mail_api_client.api.health import health_check
from generated_src.lleida_hack_mail_api_client.api.mail import (
    mail_create,
    mail_send_by_id,
)
from generated_src.lleida_hack_mail_api_client.api.template import template_get_by_name
from generated_src.lleida_hack_mail_api_client.models.mail_create import MailCreate
from src.error.MailClientException import MailClientException
from src.impl.Mail.internall_templates import InternalTemplate
from src.utils.Base.BaseClient import BaseClient
from src.configuration.Configuration import Configuration


def initialized(func):

    def wrapper(*args, **kwargs):
        try:
            args[0].check_health()
        except Exception:
            pass
        if args[0]._initialized:
            return func(*args, **kwargs)
        print("MailClient not initialized")
        raise MailClientException("MailClient is not available")

    return wrapper


class MailClient(BaseClient):
    name = "mail_client"
    _internall_templates = {}
    _initialized = False

    def __init__(self) -> Any:
        super().__init__(Configuration.clients.mail_client.url, None)
        try:
            self.check_health()
            self._get_internall_templates()
            self._initialized = True
        except Exception:
            self._initialized = False
            print("MailClient not initialized")
            # raise MailClientException('MailClient is not available')

    def check_health(self):
        r = health_check.sync_detailed(client=self.client)
        if not r.status_code == HTTPStatus.OK:
            raise Exception(
                "Seems the Mail Backend is not up so maybe consider changing the client url in your config or maybe start the service"
            )
        return True

    @initialized
    def create_mail(self, mail: MailCreate):
        r = mail_create.sync(client=self.client, body=mail)
        if r is None:
            raise Exception(f"error creating {mail}")
        return r

    @initialized
    def send_mail_by_id(self, id: int):
        r = mail_send_by_id.sync_detailed(id, client=self.client)
        return r

    def get_template_by_name(self, name):
        return template_get_by_name.sync(name, client=self.client)

    def _get_internall_templates(self):
        for _ in InternalTemplate:
            r = self.get_template_by_name(_.value)
            if r is None:
                raise Exception(
                    f"error obtaining template with name:{_.value}")
            self._internall_templates[_] = r

    @initialized
    def get_internall_template_id(self, it: InternalTemplate):
        return self._internall_templates[it].id
