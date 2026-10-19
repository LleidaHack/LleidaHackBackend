"""Deploy application-only releases; refuse migrations and preserve production data."""

import argparse
import copy
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import yaml

HOST = Path("/root/LleidaHackWeb")
COMPOSE = HOST / "docker-compose.yml"
RELEASES = HOST / "releases/backend"
BACKUPS = Path("/root/backups")
REPOSITORY = "LleidaHack/LleidaHackBackend"
PUBLIC = "https://backend.main.lleidahack.dev"


class DeploymentError(RuntimeError):
    """A deployment gate failed without exposing runtime credentials."""


def require(condition, message):
    if not condition:
        raise DeploymentError(message)


def run(*args, stdout=None):
    result = subprocess.run(
        args, stdout=stdout or subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    require(
        result.returncode == 0,
        f"Command failed: {args[0]} {args[1]} (output withheld to protect secrets)",
    )
    return result.stdout.decode() if result.stdout else ""


def inspect(name):
    return json.loads(run("docker", "inspect", name))[0]


def api(path):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "LLH-production-deploy",
    }
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"
    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPOSITORY}/{path}", headers=headers
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except (OSError, ValueError) as error:
        raise DeploymentError(
            "GitHub CI could not be verified; retry later or configure GH_TOKEN"
        ) from error


def verify_ci(sha):
    runs = api(
        f"actions/workflows/deploy.yml/runs?branch=main&event=push&head_sha={sha}&per_page=100"
    )["workflow_runs"]
    matching = [r for r in runs if r["head_sha"] == sha and r["head_branch"] == "main"]
    require(matching, "No push-to-main validation run exists for this commit")
    latest = max(matching, key=lambda r: r["id"])
    require(
        latest["status"] == "completed" and latest["conclusion"] == "success",
        "Latest main validation is pending or failed; deployment refused",
    )
    jobs = api(f"actions/runs/{latest['id']}/jobs?per_page=100")["jobs"]
    for name in ["tests / tests", "security / scan"]:
        require(
            any(j["name"] == name and j["conclusion"] == "success" for j in jobs),
            f"Required CI job did not pass: {name}",
        )


def reject_schema_changes(paths):
    require(
        not any(p.startswith("alembic/") or p == "alembic.ini" for p in paths),
        "Migration/configuration changes detected. Use the reviewed migration runbook; no automatic migrations are allowed",
    )


def replacement(original, image):
    updated = copy.deepcopy(original)
    service = updated["services"]["backend-main"]
    require(
        service.get("command") == ["gunicorn", "main:app", "-c", "gunicorn_conf.py"],
        "Unexpected startup command; review it before deployment",
    )
    require(
        "build" not in service and bool(service.get("healthcheck")),
        "Expected an immutable image and Docker healthcheck",
    )
    service["image"] = image
    return updated


def atomic_write(path, content):
    temporary = path.with_name(path.name + ".deploy-tmp")
    temporary.write_bytes(content)
    temporary.chmod(0o600)
    os.replace(temporary, path)


def compose_up():
    run(
        "docker",
        "compose",
        "--project-directory",
        str(HOST),
        "-p",
        "lleidahackweb",
        "-f",
        str(COMPOSE),
        "--profile",
        "main",
        "up",
        "-d",
        "--no-deps",
        "--no-build",
        "backend-main",
    )


def wait_healthy(image_id, timeout=120):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        container = inspect("backend-main")
        require(
            container["Image"] == image_id, "Running container has an unexpected image"
        )
        state = container["State"]
        require(
            state["Running"] and container["RestartCount"] == 0,
            "Backend exited or restarted during validation",
        )
        if state.get("Health", {}).get("Status") == "healthy":
            return
        time.sleep(3)
    raise DeploymentError("Backend health check timed out")


def smoke():
    # GET only: never create users, rotate tokens, or send email.
    for path, expected in [("/openapi.json", 200), ("/v1/auth/me", 401)]:
        try:
            with urllib.request.urlopen(PUBLIC + path, timeout=20) as response:
                status = response.status
        except urllib.error.HTTPError as error:
            status = error.code
        require(status == expected, f"Public smoke check failed: {path}")
    run(
        "docker",
        "exec",
        "backend-main",
        "python",
        "-c",
        "import httpx; from src.configuration.Settings import settings; "
        "from src.impl.Mail.client import MailClient; MailClient().ensure_initialized(); "
        "r = httpx.get('http://127.0.0.1:8000/v1/event/all', "
        "headers={'Authorization': 'Bearer ' + settings.security.service_token}, timeout=20); "
        "assert r.status_code == 200; assert isinstance(r.json(), list)",
    )


def guarded_cutover(original, updated, new_id, old_id, verify, check_unchanged):
    """Recover application only; never restore or downgrade database contents."""
    require(
        COMPOSE.read_bytes() == original,
        "Compose changed during preparation; refusing to overwrite it",
    )
    atomic_write(COMPOSE, updated)
    try:
        run(
            "docker",
            "compose",
            "--project-directory",
            str(HOST),
            "-p",
            "lleidahackweb",
            "-f",
            str(COMPOSE),
            "--profile",
            "main",
            "config",
            "--quiet",
        )
        compose_up()
        wait_healthy(new_id)
        verify()
        check_unchanged()
    except BaseException as error:
        # A Ctrl-C during cutover also restores the previous application.
        if COMPOSE.read_bytes() != updated:
            raise DeploymentError(
                "Deployment failed and Compose was edited externally; manual recovery required"
            ) from error
        atomic_write(COMPOSE, original)
        try:
            compose_up()
            wait_healthy(old_id)
        except BaseException as rollback_error:
            raise DeploymentError(
                "AUTOMATIC ROLLBACK FAILED. Inspect backend-main immediately; database was not restored"
            ) from rollback_error
        raise DeploymentError(
            "Deployment failed; previous application restored and healthy. Database was not restored"
        ) from error


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deploy(check=False):
    require(os.geteuid() == 0, "Run on the production VPS as root")
    require(
        Path(run("git", "rev-parse", "--show-toplevel").strip()) == Path.cwd(),
        "Run from the repository root",
    )
    require(
        not run("git", "status", "--porcelain").strip(), "Working tree is not clean"
    )
    remote = run("git", "remote", "get-url", "origin").strip()
    require(
        remote
        in [f"https://github.com/{REPOSITORY}.git", f"git@github.com:{REPOSITORY}.git"],
        "Unexpected origin repository",
    )
    run("git", "fetch", "origin", "main")
    sha = run("git", "rev-parse", "FETCH_HEAD").strip()
    require(re.fullmatch("[0-9a-f]{40}", sha), "Invalid target commit")
    original = COMPOSE.read_bytes()
    config = yaml.safe_load(original)
    live = inspect("backend-main")
    old_id = live["Image"]
    old_image = json.loads(run("docker", "image", "inspect", old_id))[0]
    old_sha = (
        old_image["Config"]
        .get("Labels", {})
        .get("org.opencontainers.image.revision", "")
    )
    require(
        re.fullmatch("[0-9a-f]{40}", old_sha),
        "Current image has no valid source revision",
    )
    require(
        live["State"].get("Health", {}).get("Status") == "healthy",
        "Current backend is unhealthy; investigate first",
    )
    configured_image = config["services"]["backend-main"]["image"]
    require(
        json.loads(run("docker", "image", "inspect", configured_image))[0]["Id"]
        == old_id,
        "Compose does not match the running image",
    )
    run("git", "merge-base", "--is-ancestor", old_sha, sha)
    reject_schema_changes(
        run(
            "git", "diff", "--name-only", old_sha, sha, "--", "alembic", "alembic.ini"
        ).splitlines()
    )
    verify_ci(sha)
    image = f"lleidahack/backend-release:{sha}"
    updated = yaml.safe_dump(replacement(config, image), sort_keys=False).encode()
    env_files = config["services"]["backend-main"].get("env_file", [])
    require(env_files, "Explicit production env_file is required")
    paths = [Path(e["path"] if isinstance(e, dict) else e) for e in env_files]
    require(
        all(p.is_absolute() and p.is_file() for p in paths),
        "Runtime env files must be existing absolute paths",
    )
    resolved = json.loads(
        run(
            "docker",
            "compose",
            "--project-directory",
            str(HOST),
            "-p",
            "lleidahackweb",
            "-f",
            str(COMPOSE),
            "--profile",
            "main",
            "config",
            "--format",
            "json",
        )
    )
    current_env = dict(value.split("=", 1) for value in live["Config"]["Env"])
    require(
        all(
            current_env.get(key) == str(value)
            for key, value in resolved["services"]["backend-main"]
            .get("environment", {})
            .items()
        ),
        "Compose environment differs from the running backend; reconcile it first",
    )
    hashes = {p: fingerprint(p) for p in paths}
    protected = {
        name: inspect(name)["Id"]
        for name in ["db-main", "db-mail-main", "mail-backend-main", "redis-main"]
    }

    def unchanged():
        require(
            all(fingerprint(p) == h for p, h in hashes.items()),
            "Runtime configuration changed during deployment",
        )
        require(
            all(inspect(name)["Id"] == id for name, id in protected.items()),
            "An unrelated service changed during deployment",
        )

    print(
        f"Current: {old_sha}\nTarget:  {sha}\nCI passed; no schema changes.", flush=True
    )
    if check or sha == old_sha:
        print(
            "Preflight passed; no service changes."
            if check
            else "Already deployed; nothing to do."
        )
        return
    require(
        shutil.disk_usage(HOST).free >= 2 * 1024**3,
        "At least 2 GiB free disk space is required",
    )
    run("git", "checkout", "--detach", sha)
    release = RELEASES / sha
    print("Building immutable candidate...", flush=True)
    run("bash", "deploy/prepare-docker-release.sh", sha, str(release))
    new_id = (release / "image-id.txt").read_text().strip()
    backup = BACKUPS / ("deploy-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"))
    backup.mkdir(mode=0o700)
    (backup / "compose-before.yml").write_bytes(original)
    (backup / "previous-image.txt").write_text(old_id + "\n")
    for index, path in enumerate(paths):
        shutil.copy2(path, backup / f"runtime-{index}.env")
    print(f"Backing up production database to {backup}...", flush=True)
    with (backup / "backend-main.dump").open("xb") as output:
        run(
            "docker",
            "exec",
            "db-main",
            "pg_dump",
            "-U",
            "lleidahack_user",
            "-d",
            "lleidahack_main",
            "-Fc",
            stdout=output,
        )
    require((backup / "backend-main.dump").stat().st_size > 0, "Empty database backup")
    with (backup / "backend-main.dump").open("rb") as dump:
        result = subprocess.run(
            ["docker", "exec", "-i", "db-main", "pg_restore", "--list"],
            stdin=dump,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
    require(result.returncode == 0, "Database backup archive validation failed")
    files = [p for p in backup.iterdir() if p.is_file()]
    (backup / "SHA256SUMS").write_text(
        "".join(f"{fingerprint(p)}  {p.name}\n" for p in sorted(files))
    )
    destination_file = HOST / "deploy-backup-destination"
    if destination_file.exists():
        destination = destination_file.read_text().strip()
        require(
            bool(destination)
            and "\n" not in destination
            and not destination.startswith("-"),
            "Invalid off-host backup destination",
        )
        print("Copying backup off-host before activation...", flush=True)
        run("scp", "-B", "-r", "--", str(backup), destination)
    unchanged()
    require(
        inspect("backend-main")["Id"] == live["Id"],
        "Backend changed during preparation",
    )
    print(
        "Activating backend only; rollback is automatic if verification fails...",
        flush=True,
    )
    guarded_cutover(original, updated, new_id, old_id, smoke, unchanged)
    record = {
        "revision": sha,
        "previous_revision": old_sha,
        "image": new_id,
        "backup": str(backup),
        "deployed_at": datetime.now(UTC).isoformat(),
        "schema_migrated": False,
    }
    (release / "deployed.json").write_text(json.dumps(record, indent=2))
    print(
        f"Deployed and verified {sha}. Backup: {backup}. Copy this private backup off-host."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fetch main and check gates without building, backing up or restarting",
    )
    args = parser.parse_args()
    os.umask(0o077)
    try:
        require(RELEASES.is_dir(), "Production release directory not found")
        # Shared with the existing candidate-preparation workflow.
        with (RELEASES / ".prepare.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise DeploymentError(
                    "Another deployment/preparation is already running"
                ) from error
            deploy(args.check)
    except (DeploymentError, OSError, ValueError, KeyError, yaml.YAMLError) as error:
        # Runtime values and subprocess output must never reach deployment logs.
        print(
            str(error)
            if isinstance(error, DeploymentError)
            else "Deployment aborted: configuration or system error; inspect private files.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
