import hashlib

import pytest

from deploy.load_rehearsal import exercise
from deploy.restore_rehearsal import rehearse


@pytest.fixture(autouse=True)
def database():
    """These guards do not need a database."""


@pytest.fixture(autouse=True)
def clean_database():
    """Do not reset databases for command argument validation."""


def test_load_test_refuses_production():
    with pytest.raises(ValueError, match="local HTTP"):
        exercise("https://backend.main.lleidahack.dev", 1)


def test_restore_rejects_invalid_checksum_before_starting_docker(tmp_path, monkeypatch):
    backup = tmp_path / "backup.dump"
    backup.write_bytes(b"not a valid backup")

    def forbidden(*args, **kwargs):
        pytest.fail("Docker must not run before checksum verification")

    monkeypatch.setattr("deploy.restore_rehearsal.run", forbidden)
    with pytest.raises(ValueError, match="checksum"):
        rehearse(backup, hashlib.sha256(b"different").hexdigest())
