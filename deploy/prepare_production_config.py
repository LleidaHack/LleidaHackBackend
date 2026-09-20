"""Write a private Docker candidate using the running main backend's settings.

This does not start containers, modify the existing Compose file or migrate data.
Requires Docker Compose >=2.30 for raw env files. Review origins before cutover.
"""

import argparse
import json
import os
import re
import secrets
import subprocess
from pathlib import Path
from urllib.parse import urlsplit


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commit")
    parser.add_argument("destination", type=Path)
    parser.add_argument(
        "--origins", required=True, help="JSON list of exact production browser origins"
    )
    parser.add_argument(
        "--rotate-secrets",
        action="store_true",
        help="Stage new JWT and service keys; coordinate sessions, email links and service clients at cutover",
    )
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        raise SystemExit("A full commit SHA is required")
    origins = json.loads(args.origins)
    if not isinstance(origins, list) or not origins:
        raise SystemExit("Explicit production origins are required")
    for origin in origins:
        parsed = urlsplit(origin)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.path
            or parsed.query
            or parsed.fragment
            or parsed.username
        ):
            raise SystemExit("Origins must be HTTPS origins without paths")
    os.umask(0o077)
    dest = args.destination.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    if any(
        (dest / name).exists() for name in ["runtime.env", "compose.json", "static"]
    ):
        raise SystemExit("Refusing to overwrite an existing prepared configuration")
    backend = json.loads(docker("inspect", "backend-main"))[0]
    proxy = json.loads(docker("inspect", "nginx-proxy-manager"))[0]
    networks = backend["NetworkSettings"]["Networks"]
    if len(networks) != 1:
        raise SystemExit("Review unexpected production networks")
    network = next(iter(networks))
    proxy_ip = proxy["NetworkSettings"]["Networks"][network]["IPAddress"]
    # Capture only to memory: effective settings may come from an old image's .env.
    settings = json.loads(
        docker(
            "exec",
            "backend-main",
            "/app/.venv/bin/python",
            "-c",
            "import json, subprocess; from io import StringIO; from dotenv import dotenv_values; "
            "from src.configuration.Settings import settings; "
            "tracked = subprocess.check_output(['git', 'show', 'HEAD:.env'], text=True); "
            "values = dotenv_values(stream=StringIO(tracked)); "
            "data = settings.model_dump(mode='json'); "
            "data['_tracked_secret_exposure'] = any(key in values.values() for key in "
            "[settings.security.secret_key, settings.security.service_token]); print(json.dumps(data))",
        )
    )
    if settings.pop("_tracked_secret_exposure") and not args.rotate_secrets:
        raise SystemExit(
            "Production credentials appear in tracked history; use --rotate-secrets and coordinate client/link changes"
        )
    security = settings["security"]
    if args.rotate_secrets:
        security["secret_key"] = secrets.token_urlsafe(48)
        security["service_token"] = secrets.token_urlsafe(48)
    for key in ["secret_key", "service_token"]:
        if len(security[key]) < 32 or security[key].lower().startswith(
            ("your-", "tu-", "change", "${")
        ):
            raise SystemExit(
                "Existing credentials require coordinated rotation before preparing main"
            )
    if security["secret_key"] == security["service_token"]:
        raise SystemExit("Existing credentials are not independent")
    environment = {
        "ENV": "main",
        "LOCAL": "false",
        "FRONT_URL": settings["front_url"],
        "BACK_URL": settings["back_url"],
        "CONTACT_MAIL": settings["contact_mail"],
        "DATABASE__URL": settings["database"]["url"],
        "CLIENTS__MAIL_CLIENT__URL": settings["clients"]["mail_client"]["url"],
        "SECURITY__SECRET_KEY": security["secret_key"],
        "SECURITY__SERVICE_TOKEN": security["service_token"],
        "SECURITY__ALGORITHM": security["algorithm"],
        "SECURITY__EXPIRE_TIME": str(security["expire_time"]),
        "CORS_ORIGINS": json.dumps(origins),
        "RATE_LIMIT__ENABLED": "true",
        "RATE_LIMIT__REDIS_URL": "redis://redis-main:6379/0",
        "RATE_LIMIT__PREFIX": "lleidahack:main:limits",
        "FORWARDED_ALLOW_IPS": proxy_ip,
        "WEB_CONCURRENCY": "2",
    }
    if any("\n" in value or "\r" in value for value in environment.values()):
        raise SystemExit("Multiline environment values require manual review")
    (dest / "runtime.env").write_text(
        "".join(f"{key}={value}\n" for key, value in environment.items())
    )
    subprocess.run(
        ["docker", "cp", "backend-main:/app/static", str(dest / "static")], check=True
    )
    for path in [dest / "static", *(dest / "static").rglob("*")]:
        if path.is_symlink():
            raise SystemExit("Review symlinks in production static assets")
        path.chmod(0o755 if path.is_dir() else 0o644)
    redis = json.loads(docker("image", "inspect", "redis:7-alpine"))[0]
    redis_image = next(
        (name for name in redis["RepoDigests"] if name.startswith("redis@sha256:")),
        None,
    )
    if not redis_image:
        raise SystemExit("Redis image must have a verified repository digest")
    logging = {"driver": "json-file", "options": {"max-size": "10m", "max-file": "3"}}
    config = {
        "name": backend["Config"]["Labels"]["com.docker.compose.project"],
        "services": {
            "backend-main": {
                "image": f"lleidahack/backend-release:{args.commit}",
                "container_name": "backend-main",
                "restart": "unless-stopped",
                "env_file": [{"path": str(dest / "runtime.env"), "format": "raw"}],
                # Schema migration is an explicit, backed-up operation before cutover.
                "command": ["gunicorn", "main:app", "-c", "gunicorn_conf.py"],
                "volumes": [
                    {
                        "type": "bind",
                        "source": str(dest / "static"),
                        "target": "/app/static",
                        "read_only": True,
                    }
                ],
                "networks": ["production"],
                "logging": logging,
                "healthcheck": {
                    "test": [
                        "CMD",
                        "python",
                        "-c",
                        "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/openapi.json', timeout=5)",
                    ],
                    "interval": "15s",
                    "timeout": "6s",
                    "retries": 4,
                    "start_period": "20s",
                },
                "depends_on": {"redis-main": {"condition": "service_healthy"}},
            },
            "redis-main": {
                "image": redis_image,
                "container_name": "redis-main",
                "restart": "unless-stopped",
                "command": [
                    "redis-server",
                    "--save",
                    "",
                    "--appendonly",
                    "no",
                    "--maxmemory",
                    "64mb",
                    "--maxmemory-policy",
                    "noeviction",
                ],
                "networks": ["production"],
                "logging": logging,
                "healthcheck": {
                    "test": ["CMD", "redis-cli", "ping"],
                    "interval": "5s",
                    "timeout": "3s",
                    "retries": 5,
                },
            },
        },
        "networks": {"production": {"external": True, "name": network}},
    }
    (dest / "compose.json").write_text(json.dumps(config, indent=2))
    subprocess.run(
        ["docker", "compose", "-f", str(dest / "compose.json"), "config", "--quiet"],
        check=True,
    )
    print(
        "Private candidate configuration validated; production containers were not changed."
    )
    print(
        "Review FRONT_URL, BACK_URL, origins, credential rotation and the proxy address before cutover."
    )
    if args.rotate_secrets:
        print(
            "NEW KEYS STAGED: update service clients; existing sessions and signed email links will need reissuance at cutover."
        )


if __name__ == "__main__":
    main()
