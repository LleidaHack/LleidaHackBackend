import logging
from functools import wraps
from http import HTTPStatus
from threading import RLock
from typing import Any

from generated_src.lleida_hack_mail_api_client.api.health import health_check
from generated_src.lleida_hack_mail_api_client.api.mail import (
    mail_create,
    mail_send_by_id,
)
from generated_src.lleida_hack_mail_api_client.api.template import template_get_by_name
from generated_src.lleida_hack_mail_api_client.models.mail_create import MailCreate

from src.configuration.Settings import settings
from src.error.MailClientException import MailClientException
from src.impl.Mail.internall_templates import InternalTemplate
from src.utils.Base.BaseClient import BaseClient

logger = logging.getLogger(__name__)


def initialized(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self.ensure_initialized()
        return func(self, *args, **kwargs)

    return wrapper


class MailClient(BaseClient):
    name = "mail_client"
    _initialized = False

    def __init__(self) -> Any:
        super().__init__(settings.clients.mail_client.url, None)
        self._initialization_lock = RLock()
        self._internall_templates = {}
        self._initialized = False
        try:
            self.ensure_initialized()
        except MailClientException:
            logger.warning(
                "MailClient is not available; initialization will be retried"
            )

    def ensure_initialized(self):
        with self._initialization_lock:
            try:
                self.check_health()
                if not self._initialized:
                    self._get_internall_templates()
                    self._initialized = True
            # Preserve the documented service-boundary fallback.
            except Exception:  # noqa: BLE001
                self._initialized = False
                raise MailClientException("MailClient is not available") from None

    def check_health(self):
        r = health_check.sync_detailed(client=self.client)
        if not r.status_code == HTTPStatus.OK:
            raise MailClientException(
                "Seems the Mail Backend is not up so maybe consider changing the client url in your config or maybe start the service"
            )
        return True

    def test_health(self):
        return settings.clients.mail_client.url, health_check.sync_detailed(
            client=self.client
        ).status_code

    @initialized
    def create_mail(self, mail: MailCreate):
        r = mail_create.sync(client=self.client, body=mail)
        if r is None:
            raise MailClientException(f"error creating {mail}")
        try:
            mail_id = getattr(r, "id", None)
            logger.info(
                "Mail created id=%s receiver=%s subject=%s",
                mail_id,
                mail.receiver_mail,
                mail.subject,
            )
        # Preserve the documented service-boundary fallback.
        except Exception:  # noqa: BLE001
            logger.debug("Mail created (unable to log details)")
        return r

    @initialized
    def send_mail_by_id(self, id: int):
        logger.info("Sending mail id=%s", id)
        r = mail_send_by_id.sync_detailed(id, client=self.client)
        status = getattr(r, "status_code", None)
        try:
            logger.info("Mail send result id=%s status=%s", id, status)
        # Preserve the documented service-boundary fallback.
        except Exception:  # noqa: BLE001
            logger.debug("Mail send completed id=%s", id)
        return r

    def get_template_by_name(self, name):
        return template_get_by_name.sync(name, client=self.client)

    def _get_internall_templates(self):
        templates = {}
        for _ in InternalTemplate:
            r = self.get_template_by_name(_.value)
            if r is None:
                raise MailClientException(
                    f"error obtaining template with name:{_.value}"
                )
            templates[_] = r
        self._internall_templates = templates

    @initialized
    def get_internall_template_id(self, it: InternalTemplate):
        return self._internall_templates[it].id
