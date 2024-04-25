"""Contains all the data models used in inputs/outputs"""

from .http_validation_error import HTTPValidationError
from .mail_create import MailCreate
from .mail_get import MailGet
from .mail_update import MailUpdate
from .template_create import TemplateCreate
from .template_get import TemplateGet
from .template_get_all import TemplateGetAll
from .template_update import TemplateUpdate
from .validation_error import ValidationError

__all__ = (
    "HTTPValidationError",
    "MailCreate",
    "MailGet",
    "MailUpdate",
    "TemplateCreate",
    "TemplateGet",
    "TemplateGetAll",
    "TemplateUpdate",
    "ValidationError",
)
