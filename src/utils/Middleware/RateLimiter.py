"""Bounded HTTP requests and atomic, expiring counters shared by all workers."""

import asyncio
import base64
import hashlib
import hmac
import ipaddress
import json
import logging

from redis.asyncio import Redis
from redis.backoff import NoBackoff
from redis.exceptions import RedisError
from redis.retry import Retry
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Increment and expiry must be atomic. Rejections never extend the window.
COUNTER = """
local count = tonumber(redis.call('GET', KEYS[1]) or '0')
if count >= tonumber(ARGV[1]) then
    return math.max(1, redis.call('TTL', KEYS[1]))
end
count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[2]) end
return 0
"""
SIGNUPS = {"/v1/hacker/signup", "/v1/lleidahacker/signup", "/v1/company-user/signup"}
MAIL_ROUTES = {
    "/v1/auth/reset-password",
    "/v1/auth/resend-verification",
    "/v1/auth/contact",
}


class RateLimitingMiddleware:
    def __init__(self, app, config, secret):
        self.app = app
        self.config = config
        self.secret = secret.encode()
        self.redis = Redis.from_url(
            config.redis_url,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
            max_connections=50,
            retry_on_timeout=False,
            retry=Retry(NoBackoff(), 0),
        )

    def key(self, rule, identity):
        digest = hmac.new(self.secret, identity.encode(), hashlib.sha256).hexdigest()
        return f"{self.config.prefix}:{rule}:{digest}"

    async def consume(self, rule, identity, limit, seconds):
        return int(
            await self.redis.eval(COUNTER, 1, self.key(rule, identity), limit, seconds)
        )

    async def reject(self, scope, receive, send, status, detail, retry=None):
        headers = {"Cache-Control": "no-store"}
        if retry is not None:
            headers["Retry-After"] = str(retry)
        await JSONResponse({"detail": detail}, status_code=status, headers=headers)(
            scope, receive, send
        )

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            try:
                await self.app(scope, receive, send)
            finally:
                await self.redis.aclose()
            return
        if scope["type"] != "http" or not self.config.enabled:
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        # Only the ASGI peer is trusted. Forwarded headers are never parsed here.
        peer = scope.get("client") or ("unknown", 0)
        identity = peer[0]
        try:
            address = ipaddress.ip_address(identity)
            if address.version == 6:
                identity = str(ipaddress.ip_network(f"{address}/64", strict=False))
        except ValueError:
            pass
        c = self.config
        path = scope["path"].rstrip("/")
        signup = request.method == "POST" and path in SIGNUPS
        mail = request.method == "POST" and path in MAIL_ROUTES
        login = request.method == "GET" and path == "/v1/auth/login"
        rules = [
            ("burst", identity, c.burst_per_second, 1),
            ("general", identity, c.requests_per_minute, 60),
        ]
        if login:
            rules.append(("login-ip", identity, c.login_per_minute, 60))
        if signup:
            rules.append(("signup-ip", identity, c.signup_per_hour, 3600))
        if mail:
            rules.append(("mail-ip", identity, c.mail_per_hour, 3600))
        try:
            for rule in rules:
                retry = await self.consume(*rule)
                if retry:
                    await self.reject(
                        scope,
                        receive,
                        send,
                        429,
                        "Too many requests. Please try again later.",
                        retry,
                    )
                    return
            body = bytearray()

            async def read_body():
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return False
                    body.extend(message.get("body", b""))
                    if len(body) > c.max_body_bytes:
                        return False
                    if not message.get("more_body", False):
                        return True

            length = request.headers.get("content-length")
            if length and (
                len(length) > 12
                or not length.isdecimal()
                or int(length) > c.max_body_bytes
            ):
                await self.reject(
                    scope, receive, send, 413, "Request body is too large."
                )
                return
            try:
                complete = await asyncio.wait_for(read_body(), c.body_timeout_seconds)
            except TimeoutError:
                await self.reject(scope, receive, send, 408, "Request body timed out.")
                return
            if not complete:
                if len(body) > c.max_body_bytes:
                    await self.reject(
                        scope, receive, send, 413, "Request body is too large."
                    )
                return
            account = ""
            if login:
                auth = request.headers.get("authorization", "").split(" ", 1)
                if len(auth) == 2 and auth[0].lower() == "basic":
                    try:
                        account = (
                            base64.b64decode(auth[1], validate=True)
                            .decode()
                            .split(":", 1)[0]
                        )
                    except (ValueError, UnicodeError):
                        pass
            elif signup or path == "/v1/auth/contact":
                try:
                    payload = json.loads(body)
                    if isinstance(payload, dict) and isinstance(
                        payload.get("email"), str
                    ):
                        account = payload["email"]
                except (ValueError, UnicodeError):
                    pass
            elif mail:
                account = request.query_params.get("email", "")
            account = account.strip().casefold()
            rules = []
            if login and account:
                rules.append(("login-account", account, c.login_per_account, 900))
            if signup or mail:
                if account:
                    rules.append(("mail-recipient", account, c.mail_per_recipient, 900))
                rules.append(("mail-total", "all", c.mail_total_per_hour, 3600))
            for rule in rules:
                retry = await self.consume(*rule)
                if retry:
                    await self.reject(
                        scope,
                        receive,
                        send,
                        429,
                        "Too many requests. Please try again later.",
                        retry,
                    )
                    return
        except RedisError:
            logger.warning("Rate-limit storage unavailable; rejecting request")
            await self.reject(
                scope,
                receive,
                send,
                503,
                "Request protection temporarily unavailable.",
                5,
            )
            return

        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)
