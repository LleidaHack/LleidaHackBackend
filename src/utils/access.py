"""Application access roles, separate from legacy account types and job titles."""

import re

from fastapi import HTTPException

from src.utils.UserType import UserType

IDENTITY_ROUTES = re.compile(r"/v1/(?:user|hacker|lleidahacker|company-user)(?:/|$)")


def access_role(token):
    if token.user_type == UserType.SERVICE.value and token.is_admin and token.available:
        return "superadmin"
    return getattr(token, "access_role", "hacker")


def require_management(token):
    if access_role(token) not in {"superadmin", "admin"}:
        raise HTTPException(403, "Management access requires admin or superadmin")


def require_superadmin(token):
    if access_role(token) != "superadmin":
        raise HTTPException(403, "Superadmin permission required")


def authorize_route(token, method, path):
    """Defense in depth for existing management routes as well as new operations."""
    role = access_role(token)
    if role in {"superadmin", "hacker"}:
        return
    own_profile = re.fullmatch(
        r"/v1/(?:user|lleidahacker)/" + str(token.user_id) + r"/?", path
    )
    session_route = path in {
        "/v1/auth/me",
        "/v1/auth/check_token",
        "/v1/auth/refresh-token",
    }
    if role == "mentor":
        if not (
            session_route
            or (own_profile and method == "GET")
            or (path == "/v1/nicknames/me" and method in {"GET", "POST"})
        ):
            raise HTTPException(403, "Mentor accounts have meal-only access")
    elif role == "lleidahacker":
        allowed = (
            (path == "/v1/nicknames/me" and method in {"GET", "POST"})
            or session_route
            or (own_profile and method in {"GET", "PUT", "PATCH"})
        )
        allowed = allowed or (
            method == "GET" and re.fullmatch(r"/v1/operations/\d+/scanner", path)
        )
        allowed = allowed or (
            method == "PUT"
            and re.fullmatch(r"/v1/operations/\d+/mentors/\d+/badge", path)
        )
        allowed = allowed or (
            method == "POST" and re.fullmatch(r"/v1/operations/\d+/scan", path)
        )
        allowed = allowed or (
            method == "PUT"
            and re.fullmatch(r"/v1/event/\d+/vouchers/[^/]+/assign/[^/]+", path)
        )
        allowed = allowed or (
            method == "PUT"
            and re.fullmatch(r"/v1/(?:meal/\d+/eat|event/\d+/participate)/[^/]+", path)
        )
        if not allowed:
            raise HTTPException(
                403, "Use the HackEPS scanner; management access is not permitted"
            )
    elif role == "admin":
        critical = method == "DELETE" and not re.fullmatch(
            # Withdrawing alerts and revoking lost badges are routine operations
            # (VoucherService.unassign enforces require_management itself).
            r"/v1/operations/\d+/alerts/[^/]+|/v1/event/\d+/vouchers/[^/]+/assign",
            path,
        )
        critical = critical or (
            method != "GET"
            # Match whole path segments so e.g. /v1/userConfig is not treated as /v1/user.
            and IDENTITY_ROUTES.match(path)
            and not own_profile
        )
        critical = (
            critical
            or "/force-verify/" in path
            or (method != "GET" and "/archive" in path)
        )
        if critical:
            raise HTTPException(403, "Superadmin permission required")
    else:
        raise HTTPException(403, "Unknown access role")
