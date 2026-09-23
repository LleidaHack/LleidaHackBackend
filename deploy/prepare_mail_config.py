"""Stage the current mail image with corrected links; never restart it or migrate."""

import argparse
import json
import os
import subprocess
from pathlib import Path
from urllib.parse import urlsplit


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--front-url", required=True)
    args = parser.parse_args()
    url = urlsplit(args.front_url)
    if (
        url.scheme != "https"
        or not url.hostname
        or url.username
        or url.query
        or url.fragment
    ):
        raise SystemExit("An explicit production HTTPS frontend URL is required")
    os.umask(0o077)
    dest = args.destination.resolve()
    dest.mkdir(parents=True, exist_ok=False)
    live = json.loads(docker("inspect", "mail-backend-main"))[0]
    if live["Mounts"] or len(live["NetworkSettings"]["Networks"]) != 1:
        raise SystemExit("Unexpected mail mounts/networks require review")
    settings = json.loads(
        docker(
            "exec",
            "mail-backend-main",
            "/app/.venv/bin/python",
            "-c",
            "import json; from src.configuration.Settings import settings; print(json.dumps(settings.model_dump(mode='json')))",
        )
    )
    environment = dict(item.split("=", 1) for item in live["Config"]["Env"])
    for key, value in settings.items():
        if isinstance(value, dict):
            for nested, item in value.items():
                # MailSettings uses an explicit alias for from_mail.
                suffix = (
                    "FROM"
                    if key == "mail" and nested == "from_mail"
                    else nested.upper()
                )
                environment[f"{key.upper()}__{suffix}"] = (
                    str(item).lower() if isinstance(item, bool) else str(item)
                )
        else:
            environment[key.upper()] = str(value)
    environment["FRONT_URL"] = args.front_url.rstrip("/")
    if any("\n" in value or "\r" in value for value in environment.values()):
        raise SystemExit("Multiline environment requires review")
    (dest / "runtime.env").write_text(
        "".join(f"{key}={value}\n" for key, value in environment.items())
    )
    config = {
        "name": live["Config"]["Labels"]["com.docker.compose.project"],
        "services": {
            "mail-backend-main": {
                "image": live["Image"],
                "container_name": "mail-backend-main",
                "restart": "unless-stopped",
                "env_file": [{"path": str(dest / "runtime.env"), "format": "raw"}],
                "command": [
                    "/app/.venv/bin/gunicorn",
                    "main:app",
                    "-c",
                    "gunicorn_conf.py",
                ],
                "networks": ["production"],
                "logging": {
                    "driver": "json-file",
                    "options": {"max-size": "10m", "max-file": "3"},
                },
            }
        },
        "networks": {
            "production": {
                "external": True,
                "name": next(iter(live["NetworkSettings"]["Networks"])),
            }
        },
    }
    (dest / "compose.json").write_text(json.dumps(config, indent=2))
    subprocess.run(
        ["docker", "compose", "-f", str(dest / "compose.json"), "config", "--quiet"],
        check=True,
    )
    print(
        "Mail configuration staged: existing image, SMTP and database retained; no restart or migration"
    )


if __name__ == "__main__":
    main()
