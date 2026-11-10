from uuid import UUID

from redis.exceptions import RedisError


def test_health_and_request_correlation(client, monkeypatch):
    request_id = "4af94e8a-6538-44b0-9376-3d177cc6de9c"
    response = client.get("/health/ready", headers={"x-request-id": request_id})
    assert response.status_code == 200, response.text
    assert response.json() == {
        "status": "ok",
        "checks": {"database": True, "redis": True},
    }
    assert response.headers["x-request-id"] == request_id
    assert response.headers["cache-control"] == "no-store, private, max-age=0"
    response = client.get("/health/live", headers={"x-request-id": "invalid"})
    UUID(response.headers["x-request-id"])
    from src.utils import health

    def unavailable(*args, **kwargs):
        raise RedisError("private connection details")

    monkeypatch.setattr(health.Redis, "from_url", unavailable)
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["redis"] is False
    assert "private" not in response.text
