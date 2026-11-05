#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! docker inspect llh-operations-db >/dev/null 2>&1; then
  docker run -d --name llh-operations-db -e POSTGRES_USER=audit_test -e POSTGRES_PASSWORD=local-test-password -e POSTGRES_DB=lleidahack_test -p 127.0.0.1:55439:5432 postgres:16
else
  docker start llh-operations-db >/dev/null
fi
if ! docker inspect llh-operations-redis >/dev/null 2>&1; then
  docker run -d --name llh-operations-redis -p 127.0.0.1:56379:6379 redis:7-alpine
else
  docker start llh-operations-redis >/dev/null
fi
until docker exec llh-operations-db pg_isready -U audit_test >/dev/null; do sleep 1; done
if ! docker exec llh-operations-db psql -U audit_test -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='llh_operations_dev'" | grep -q 1; then
  docker exec llh-operations-db createdb -U audit_test llh_operations_dev
fi
if [ ! -f .env.operations.local ]; then
  uv run python - <<'PY'
from pathlib import Path
import secrets
Path('.env.operations.local').write_text('\n'.join([
 'DATABASE__URL=postgresql://audit_test:local-test-password@127.0.0.1:55439/llh_operations_dev',
 'SECURITY__SECRET_KEY='+secrets.token_urlsafe(48),
 'SECURITY__SERVICE_TOKEN='+secrets.token_urlsafe(48),
 'SECURITY__EXPIRE_TIME=720',
 'CLIENTS__MAIL_CLIENT__URL=http://127.0.0.1:59999/',
 'RATE_LIMIT__REDIS_URL=redis://127.0.0.1:56379/0',
 'RATE_LIMIT__PREFIX=lleidahack:local-operations',
 'CORS_ORIGINS=\'["http://localhost:3000","http://127.0.0.1:3000","http://localhost:3001","http://127.0.0.1:3001","http://localhost:5175","http://127.0.0.1:5175"]\'',
 'LOCAL=true', 'PYTHONPATH=backend:.',
])+'\n')
Path('.env.operations.local').chmod(0o600)
PY
fi
uv run --env-file .env.operations.local alembic upgrade head
uv run --env-file .env.operations.local python scripts/seed_operations.py
uv run --env-file .env.operations.local python scripts/seed_local_roles.py
exec uv run --env-file .env.operations.local uvicorn main:app --host 127.0.0.1 --port 8000
