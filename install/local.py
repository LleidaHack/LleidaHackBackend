"""Start an isolated local backend, PostgreSQL and a capture-only mail service."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
import socket

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT), str(ROOT / "install")]
os.chdir(ROOT)


def run():
    for port in (8000, 8001):
        with socket.socket() as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                listener.bind(("127.0.0.1", port))
            except OSError:
                raise RuntimeError(f"Local port {port} is already in use") from None
    config_path = ROOT / ".local-backend.json"
    if config_path.exists():
        config = json.loads(config_path.read_text())
    else:
        config = {"jwt_secret": secrets.token_urlsafe(48),
                  "service_token": secrets.token_urlsafe(48),
                  "database_password": secrets.token_urlsafe(32),
                  "organizer_password": secrets.token_urlsafe(18)}
        with os.fdopen(os.open(config_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as file:
            json.dump(config, file, indent=2)
    container = "lleidahack-local"
    exists = subprocess.run(["docker", "container", "inspect", container], capture_output=True).returncode == 0
    if exists:
        subprocess.run(["docker", "start", container], check=True, stdout=subprocess.DEVNULL)
    else:
        subprocess.run([
            "docker", "run", "-d", "--name", container,
            "-e", "POSTGRES_USER=lleidahack_local",
            "-e", f"POSTGRES_PASSWORD={config['database_password']}",
            "-e", "POSTGRES_DB=lleidahack_local", "-p", "127.0.0.1:55440:5432", "postgres:16",
        ], check=True, stdout=subprocess.DEVNULL)
    for _ in range(60):
        ready = subprocess.run(["docker", "exec", container, "pg_isready", "-U", "lleidahack_local"], capture_output=True)
        if ready.returncode == 0:
            break
        time.sleep(0.5)
    else:
        raise RuntimeError("Local PostgreSQL did not become ready")
    redis_container = "lleidahack-rate-limit"
    exists = subprocess.run(["docker", "container", "inspect", redis_container], capture_output=True).returncode == 0
    if exists:
        subprocess.run(["docker", "start", redis_container], check=True, stdout=subprocess.DEVNULL)
    else:
        subprocess.run(["docker", "run", "-d", "--name", redis_container,
                        "-p", "127.0.0.1:56379:6379", "redis:7-alpine",
                        "redis-server", "--maxmemory", "128mb", "--maxmemory-policy", "noeviction"],
                       check=True, stdout=subprocess.DEVNULL)
    from redis import Redis
    from redis.exceptions import RedisError
    with Redis.from_url("redis://127.0.0.1:56379/0") as limiter:
        for _ in range(60):
            try:
                if limiter.ping():
                    break
            except RedisError:
                pass
            time.sleep(0.5)
        else:
            raise RuntimeError("Local Redis did not become ready")
    os.environ.update(
        RATE_LIMIT__REDIS_URL="redis://127.0.0.1:56379/0",
        ENV="main", DATABASE__URL=f"postgresql://lleidahack_local:{config['database_password']}@127.0.0.1:55440/lleidahack_local",
        SECURITY__SECRET_KEY=config["jwt_secret"], SECURITY__SERVICE_TOKEN=config["service_token"],
        CLIENTS__MAIL_CLIENT__URL="http://127.0.0.1:8001/", LOCAL="true",
    )
    from alembic import command
    from alembic.config import Config
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    from datetime import date
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from src.impl.LleidaHacker.model import LleidaHacker
    from src.impl.UserConfig.model import UserConfig
    from src.utils.security import get_password_hash
    engine = create_engine(os.environ["DATABASE__URL"])
    with Session(engine) as session:
        if not session.query(LleidaHacker).filter_by(email="organizer@example.test").first():
            user = LleidaHacker(
                name="Local Organizer", nickname="local-organizer", email="organizer@example.test",
                telephone="600000000", birthdate=date(2000, 1, 1), password=get_password_hash(config["organizer_password"]),
                role="organizer", nif="LOCAL-ONLY", github="", linkedin="", food_restrictions="",
                address="", shirt_size="M", code="local-organizer", is_verified=True, active=True, accepted=True,
                config=UserConfig(default_lang="en"),
            )
            session.add(user)
            session.commit()
    engine.dispose()
    import uvicorn
    from local_mail import app as mail_app
    mail_server = uvicorn.Server(uvicorn.Config(mail_app, host="127.0.0.1", port=8001, log_level="warning"))
    thread = threading.Thread(target=mail_server.run, daemon=True)
    thread.start()
    for _ in range(60):
        if mail_server.started:
            break
        if not thread.is_alive():
            raise RuntimeError("Local mail capture stopped during startup")
        time.sleep(0.1)
    else:
        raise RuntimeError("Local mail capture did not become ready")
    from main import app
    from local_verification import local_verification_router
    app.include_router(local_verification_router())
    print("Backend: http://127.0.0.1:8000/docs", flush=True)
    print("Captured mail: http://127.0.0.1:8001/messages", flush=True)
    print(f"Local organizer: organizer@example.test (password in {config_path})", flush=True)
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, access_log=False, proxy_headers=False)
    finally:
        mail_server.should_exit = True
        thread.join(timeout=5)


if __name__ == "__main__":
    run()
