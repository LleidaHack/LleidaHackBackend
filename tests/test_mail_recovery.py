def test_mail_client_recovers_after_service_becomes_available(app, monkeypatch):
    from http import HTTPStatus
    from types import SimpleNamespace

    from src.impl.Mail.client import (
        MailClient,
        health_check,
        mail_create,
        template_get_by_name,
    )
    from src.impl.Mail.internall_templates import InternalTemplate

    status = {"code": HTTPStatus.SERVICE_UNAVAILABLE}
    monkeypatch.setattr(
        health_check,
        "sync_detailed",
        lambda **kwargs: SimpleNamespace(status_code=status["code"]),
    )
    monkeypatch.setattr(
        template_get_by_name, "sync", lambda *args, **kwargs: SimpleNamespace(id=7)
    )
    monkeypatch.setattr(mail_create, "sync", lambda **kwargs: SimpleNamespace(id=42))
    mail = object.__new__(MailClient)
    MailClient.__init__(mail)
    assert mail._initialized is False
    status["code"] = HTTPStatus.OK
    assert mail.get_internall_template_id(InternalTemplate.USER_CREATED) == 7
    assert mail._initialized is True


def _ready_mail_client(monkeypatch):
    from http import HTTPStatus
    from types import SimpleNamespace

    from src.impl.Mail.client import MailClient, health_check, template_get_by_name

    monkeypatch.setattr(
        health_check,
        "sync_detailed",
        lambda **kwargs: SimpleNamespace(status_code=HTTPStatus.OK),
    )
    monkeypatch.setattr(
        template_get_by_name, "sync", lambda *args, **kwargs: SimpleNamespace(id=7)
    )
    mail = object.__new__(MailClient)
    MailClient.__init__(mail)
    return mail


def test_mail_client_retries_stale_keepalive_connection(app, monkeypatch):
    from types import SimpleNamespace

    import httpx

    from src.impl.Mail.client import mail_create

    calls = []

    def flaky_create(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise httpx.RemoteProtocolError(
                "Server disconnected without sending a response."
            )
        return SimpleNamespace(id=42)

    monkeypatch.setattr(mail_create, "sync", flaky_create)
    mail = _ready_mail_client(monkeypatch)
    assert (
        mail.create_mail(SimpleNamespace(receiver_mail="a@b.c", subject="s")).id == 42
    )
    assert len(calls) == 2


def test_mail_client_maps_transport_errors_to_unavailable(app, monkeypatch):
    import httpx
    import pytest

    from src.error.MailClientException import MailClientException
    from src.impl.Mail.client import mail_send_by_id

    def refused(*args, **kwargs):
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(mail_send_by_id, "sync_detailed", refused)
    mail = _ready_mail_client(monkeypatch)
    with pytest.raises(MailClientException):
        mail.send_mail_by_id(5)
