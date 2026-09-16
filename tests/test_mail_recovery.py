def test_mail_client_recovers_after_service_becomes_available(app, monkeypatch):
    from http import HTTPStatus
    from types import SimpleNamespace
    from src.impl.Mail.client import MailClient, health_check, template_get_by_name, mail_create
    from src.impl.Mail.internall_templates import InternalTemplate

    status = {"code": HTTPStatus.SERVICE_UNAVAILABLE}
    monkeypatch.setattr(health_check, "sync_detailed", lambda **kwargs: SimpleNamespace(status_code=status["code"]))
    monkeypatch.setattr(template_get_by_name, "sync", lambda *args, **kwargs: SimpleNamespace(id=7))
    monkeypatch.setattr(mail_create, "sync", lambda **kwargs: SimpleNamespace(id=42))
    mail = object.__new__(MailClient)
    MailClient.__init__(mail)
    assert mail._initialized is False
    status["code"] = HTTPStatus.OK
    assert mail.get_internall_template_id(InternalTemplate.USER_CREATED) == 7
    assert mail._initialized is True
