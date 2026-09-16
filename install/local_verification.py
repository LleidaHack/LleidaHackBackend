"""Development-only routes, registered exclusively by install/local.py."""
from ipaddress import ip_address
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


class LocalVerification(BaseModel):
    email: str = Field(min_length=3, max_length=320)


def require_local(request: Request):
    try:
        peer_is_local = request.client and ip_address(request.client.host).is_loopback
    except ValueError:
        peer_is_local = False
    origin = request.headers.get("origin")
    if (not peer_is_local or request.url.hostname not in LOOPBACK_HOSTS
            or (origin and urlsplit(origin).hostname not in LOOPBACK_HOSTS)):
        raise HTTPException(status_code=403, detail="Local development only")


def local_verification_router():
    from src.impl.Authentication.router_v1 import auth_service
    from src.impl.User.service import UserService
    from src.utils.Token import VerificationToken

    router = APIRouter(prefix="/v1/auth", include_in_schema=False)

    @router.get("/local-verification")
    def available(request: Request):
        require_local(request)
        return {"enabled": True}

    @router.post("/local-verification")
    def verify(payload: LocalVerification, request: Request):
        require_local(request)
        user = UserService().get_by_email(payload.email)
        if user.is_deleted:
            raise HTTPException(status_code=400, detail="Account is not available")
        if not user.is_verified:
            token = VerificationToken(user)
            token.user_set()
            auth_service.verify_user(token)
        return {"success": True}

    return router
