"""Nginx appends the actual peer; untrusted client headers must not select identity."""

import asyncio

import pytest
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


@pytest.mark.parametrize(
    ("peer", "forwarded", "expected"),
    [
        ("172.18.0.7", "203.0.113.10", "203.0.113.10"),
        ("172.18.0.7", "198.51.100.99, 203.0.113.10", "203.0.113.10"),
        ("172.18.0.8", "198.51.100.99", "172.18.0.8"),
        ("172.18.0.7", "198.51.100.99, 2001:db8::10", "2001:db8::10"),
    ],
)
def test_only_actual_proxy_can_forward_rightmost_untrusted_peer(
    peer, forwarded, expected
):
    observed = []

    async def application(scope, receive, send):
        observed.append(scope["client"][0])

    middleware = ProxyHeadersMiddleware(application, trusted_hosts=["172.18.0.7"])
    scope = {
        "type": "http",
        "scheme": "http",
        "client": (peer, 45000),
        "headers": [(b"x-forwarded-for", forwarded.encode())],
    }
    asyncio.run(middleware(scope, None, None))
    assert observed == [expected]
