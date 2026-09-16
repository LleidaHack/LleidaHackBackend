import asyncio
import base64
import os
import uuid
from unittest.mock import patch

import httpx
from starlette.responses import Response

from src.configuration.Settings import RateLimitSettings
from src.utils.Middleware.RateLimiter import RateLimitingMiddleware


def middleware(**overrides):
    async def endpoint(scope, receive, send):
        await Response("ok")(scope, receive, send)
    config = RateLimitSettings(
        redis_url=os.environ["RATE_LIMIT__REDIS_URL"],
        prefix=os.environ["RATE_LIMIT__PREFIX"] + ":" + uuid.uuid4().hex,
        **overrides,
    )
    return RateLimitingMiddleware(endpoint, config, "test-secret")


def test_shared_atomic_quota_and_expiry():
    async def check():
        first = middleware()
        second = middleware()
        second.config.prefix = first.config.prefix
        try:
            results = await asyncio.gather(*[
                (first if n % 2 else second).consume("test", "same", 5, 60)
                for n in range(30)
            ])
            assert results.count(0) == 5
            key = first.key("test", "same")
            assert 0 < await first.redis.ttl(key) <= 60
            await first.redis.pexpire(key, 1)
            await asyncio.sleep(.02)
            assert await second.consume("test", "same", 5, 60) == 0
            assert "same" not in key
        finally:
            await first.redis.aclose()
            await second.redis.aclose()
    asyncio.run(check())


def test_ip_limit_ignores_forwarded_headers_and_returns_retry():
    async def check():
        app = middleware(requests_per_minute=2)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                assert (await client.get("/")).status_code == 200
                assert (await client.get("/")).status_code == 200
                response = await client.get("/", headers={"X-Forwarded-For": "192.0.2.99"})
                assert response.status_code == 429
                assert 1 <= int(response.headers["Retry-After"]) <= 60
                assert response.headers["Cache-Control"] == "no-store"
        finally:
            await app.redis.aclose()
    asyncio.run(check())


def test_account_limit_shared_across_ips_and_normalized():
    async def check():
        app = middleware(login_per_account=2)
        try:
            for index, email in enumerate(["Person@Example.test", "person@example.test", "PERSON@example.test"]):
                transport = httpx.ASGITransport(app=app, client=(f"192.0.2.{index}", 123))
                async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                    auth = base64.b64encode(f"{email}:wrong".encode()).decode()
                    response = await client.get("/v1/auth/login/", headers={"Authorization": f"Basic {auth}"})
                    assert response.status_code == (429 if index == 2 else 200)
        finally:
            await app.redis.aclose()
    asyncio.run(check())


def test_recipient_quota_shared_by_signup_and_mail_routes():
    async def check():
        app = middleware(mail_per_recipient=2)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                assert (await client.post("/v1/hacker/signup", json={"email": "person@example.test"})).status_code == 200
                assert (await client.post("/v1/auth/reset-password?email=PERSON@example.test")).status_code == 200
                assert (await client.post("/v1/auth/resend-verification?email=person@example.test")).status_code == 429
        finally:
            await app.redis.aclose()
    asyncio.run(check())


def test_body_limits_declared_and_chunked_and_timeout():
    async def check():
        app = middleware(max_body_bytes=1024, body_timeout_seconds=.01)
        async def chunks():
            yield b"a" * 600
            yield b"b" * 600
        async def slow():
            await asyncio.sleep(.1)
            yield b"small"
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                assert (await client.post("/", content=b"x" * 1025)).status_code == 413
                assert (await client.post("/", content=chunks())).status_code == 413
                assert (await client.post("/", content=slow())).status_code == 408
        finally:
            await app.redis.aclose()
    asyncio.run(check())


def test_storage_failure_rejects_before_endpoint():
    async def check():
        app = middleware()
        from redis.exceptions import ConnectionError
        try:
            with patch.object(app.redis, "eval", side_effect=ConnectionError("offline")):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    assert (await client.get("/")).status_code == 503
        finally:
            await app.redis.aclose()
    asyncio.run(check())


def test_real_signup_stops_before_database_and_mail(client, signup_payload):
    from src.impl.Mail.client import MailClient
    with patch.object(MailClient, "send_mail_by_id") as send:
        first = client.post("/v1/hacker/signup", json=signup_payload)
        assert first.status_code == 200
        for _ in range(2):
            client.post("/v1/hacker/signup", json=signup_payload)
        assert client.post("/v1/hacker/signup", json=signup_payload).status_code == 429
        assert send.call_count == 1


def test_signup_ip_and_global_mail_budgets():
    async def check():
        app = middleware(signup_per_hour=2, mail_total_per_hour=3)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                for email in ("one@test", "two@test"):
                    assert (await client.post("/v1/hacker/signup", json={"email": email})).status_code == 200
                assert (await client.post("/v1/hacker/signup", json={"email": "three@test"})).status_code == 429
            for index in range(2):
                transport = httpx.ASGITransport(app=app, client=(f"192.0.2.{index}", 123))
                async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post("/v1/auth/contact", json={"email": f"other{index}@test"})
                    assert response.status_code == (200 if index == 0 else 429)
        finally:
            await app.redis.aclose()
    asyncio.run(check())


def test_ipv6_addresses_share_subnet_quota():
    async def check():
        app = middleware(requests_per_minute=1)
        try:
            for index in range(2):
                transport = httpx.ASGITransport(app=app, client=(f"2001:db8::{index + 1}", 123))
                async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                    assert (await client.get("/")).status_code == (200 if index == 0 else 429)
        finally:
            await app.redis.aclose()
    asyncio.run(check())
