"""Deployment safety checks run without Docker, PostgreSQL or production access."""

import copy

import pytest

from deploy import production_deploy as deployment


@pytest.fixture(autouse=True)
def database():
    """Override application DB fixtures: these tests only exercise orchestration."""


@pytest.fixture(autouse=True)
def clean_database():
    """Deployment tests must not reset an application database."""


@pytest.mark.parametrize(
    "path", ["alembic/versions/new.py", "alembic/env.py", "alembic.ini"]
)
def test_schema_changes_require_manual_release(path):
    with pytest.raises(deployment.DeploymentError, match="Migration"):
        deployment.reject_schema_changes([path])


def test_application_only_changes_are_allowed():
    deployment.reject_schema_changes(["src/impl/User/schema.py"])


def test_replacement_only_changes_image():
    original = {
        "services": {
            "backend-main": {
                "image": "old",
                "command": ["gunicorn", "main:app", "-c", "gunicorn_conf.py"],
                "healthcheck": {"test": ["CMD", "true"]},
                "env_file": ["/private/runtime.env"],
            },
            "db-main": {"image": "postgres:15", "volumes": ["production:/data"]},
        },
        "volumes": {"production": {}},
    }
    snapshot = copy.deepcopy(original)
    result = deployment.replacement(original, "new")
    assert result["services"]["backend-main"]["image"] == "new"
    result["services"]["backend-main"]["image"] = "old"
    assert result == snapshot == original
    original["services"]["backend-main"]["command"] = [
        "sh",
        "-c",
        "alembic upgrade head",
    ]
    with pytest.raises(deployment.DeploymentError, match="startup"):
        deployment.replacement(original, "new")


@pytest.mark.parametrize("conclusion", ["failure", "cancelled", None])
def test_ci_must_pass(monkeypatch, conclusion):
    monkeypatch.setattr(
        deployment,
        "api",
        lambda path: {
            "workflow_runs": [
                {
                    "id": 1,
                    "head_sha": "target",
                    "head_branch": "main",
                    "status": "completed",
                    "conclusion": conclusion,
                }
            ]
        },
    )
    with pytest.raises(deployment.DeploymentError, match="pending or failed"):
        deployment.verify_ci("target")


def test_latest_ci_run_and_required_jobs_are_checked(monkeypatch):
    runs = [
        {
            "id": 1,
            "head_sha": "target",
            "head_branch": "main",
            "status": "completed",
            "conclusion": "success",
        },
        {
            "id": 2,
            "head_sha": "target",
            "head_branch": "main",
            "status": "completed",
            "conclusion": "failure",
        },
    ]
    monkeypatch.setattr(
        deployment,
        "api",
        lambda path: {"workflow_runs": runs} if "workflows/" in path else {"jobs": []},
    )
    with pytest.raises(deployment.DeploymentError, match="pending or failed"):
        deployment.verify_ci("target")
    runs.pop()
    with pytest.raises(deployment.DeploymentError, match="Required CI job"):
        deployment.verify_ci("target")


@pytest.fixture
def cutover(tmp_path, monkeypatch):
    compose = tmp_path / "compose.yml"
    compose.write_bytes(b"original")
    monkeypatch.setattr(deployment, "COMPOSE", compose)
    monkeypatch.setattr(deployment, "run", lambda *args: "")
    starts = []
    health = []
    monkeypatch.setattr(
        deployment, "compose_up", lambda: starts.append(compose.read_bytes())
    )
    monkeypatch.setattr(deployment, "wait_healthy", lambda image: health.append(image))
    return compose, starts, health


def test_success_leaves_candidate_config(cutover):
    compose, starts, health = cutover
    deployment.guarded_cutover(
        b"original", b"new", "new-id", "old-id", lambda: None, lambda: None
    )
    assert compose.read_bytes() == b"new"
    assert starts == [b"new"] and health == ["new-id"]


@pytest.mark.parametrize(
    "error", [deployment.DeploymentError("smoke failed"), KeyboardInterrupt()]
)
def test_failed_checks_or_interrupt_restore_application_only(cutover, error):
    compose, starts, health = cutover

    def fail():
        raise error

    with pytest.raises(
        deployment.DeploymentError, match="previous application restored"
    ):
        deployment.guarded_cutover(
            b"original", b"new", "new-id", "old-id", fail, lambda: None
        )
    assert compose.read_bytes() == b"original"
    assert starts == [b"new", b"original"]
    assert health == ["new-id", "old-id"]


def test_external_compose_change_prevents_cutover(cutover):
    compose, starts, _ = cutover
    compose.write_bytes(b"external edit")
    with pytest.raises(deployment.DeploymentError, match="changed during preparation"):
        deployment.guarded_cutover(
            b"original", b"new", "new-id", "old-id", lambda: None, lambda: None
        )
    assert starts == [] and compose.read_bytes() == b"external edit"


def test_external_edit_during_failure_is_not_overwritten(cutover):
    compose, starts, _ = cutover

    def fail():
        compose.write_bytes(b"external edit")
        raise deployment.DeploymentError("smoke failed")

    with pytest.raises(deployment.DeploymentError, match="manual recovery"):
        deployment.guarded_cutover(
            b"original", b"new", "new-id", "old-id", fail, lambda: None
        )
    assert starts == [b"new"] and compose.read_bytes() == b"external edit"


def test_rollback_failure_is_reported(cutover, monkeypatch):
    compose, _, _ = cutover
    monkeypatch.setattr(
        deployment,
        "wait_healthy",
        lambda image: (_ for _ in ()).throw(deployment.DeploymentError("unhealthy")),
    )
    with pytest.raises(deployment.DeploymentError, match="AUTOMATIC ROLLBACK FAILED"):
        deployment.guarded_cutover(
            b"original", b"new", "new-id", "old-id", lambda: None, lambda: None
        )
    assert compose.read_bytes() == b"original"
