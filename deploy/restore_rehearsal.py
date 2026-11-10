#!/usr/bin/env python3
"""Verify a PostgreSQL archive in a disposable, network-isolated container."""

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path
from uuid import uuid4


def run(*args, timeout=300):
    return subprocess.run(
        args, check=True, capture_output=True, text=True, timeout=timeout
    ).stdout.strip()


def rehearse(archive, expected_sha256, image="postgres:15"):
    archive = Path(archive).resolve(strict=True)
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != expected_sha256.lower():
        raise ValueError("Backup checksum mismatch")
    name = "llh-restore-rehearsal-" + uuid4().hex[:12]
    created = False
    try:
        run(
            "docker",
            "run",
            "--detach",
            "--name",
            name,
            "--network",
            "none",
            "--memory",
            "2g",
            "--cpus",
            "2",
            "--tmpfs",
            "/var/lib/postgresql/data:rw,size=1g",
            "-e",
            "POSTGRES_HOST_AUTH_METHOD=trust",
            image,
        )
        created = True
        for _ in range(30):
            try:
                run("docker", "exec", name, "pg_isready", "-U", "postgres", timeout=5)
                break
            except subprocess.CalledProcessError:
                time.sleep(1)
        else:
            raise RuntimeError("Isolated database did not become ready")
        run("docker", "cp", str(archive), name + ":/tmp/backup.dump")
        run("docker", "exec", name, "createdb", "-U", "postgres", "rehearsal")
        run(
            "docker",
            "exec",
            name,
            "pg_restore",
            "--exit-on-error",
            "--no-owner",
            "--no-privileges",
            "-U",
            "postgres",
            "-d",
            "rehearsal",
            "/tmp/backup.dump",
        )
        tables = run(
            "docker",
            "exec",
            name,
            "psql",
            "-U",
            "postgres",
            "-d",
            "rehearsal",
            "-At",
            "-c",
            "SELECT count(*) FROM pg_tables WHERE schemaname='public'",
        )
        if int(tables) == 0:
            raise RuntimeError("Restored database has no public tables")
        return {
            "restored": True,
            "sha256": digest,
            "public_tables": int(tables),
            "network": "none",
        }
    finally:
        if created:
            run("docker", "rm", "--force", "--volumes", name, timeout=30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive")
    parser.add_argument(
        "--sha256",
        required=True,
        help="Trusted checksum recorded when the backup was created",
    )
    args = parser.parse_args()
    try:
        print(json.dumps(rehearse(args.archive, args.sha256)))
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        # Restore errors can include application data; keep subprocess stderr private.
        parser.exit(
            1,
            f"Restore rehearsal failed ({type(error).__name__}); production was not connected.\n",
        )
