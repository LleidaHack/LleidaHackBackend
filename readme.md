# LleidaHack Backend

FastAPI API for LleidaHack and HackEPS: registration, teams, physical badge
assignment, check-in, meals, LleidaCoins, Live event operations and company judging.
HackEPS, Gestió and Live are separate frontend repositories.

## Start locally

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), and Docker running.
Install the locked dependencies from the repository root:

```bash
uv sync --frozen
```

Choose one environment; both launch the API on port 8000 and cannot run together.

| Environment | Command | Purpose |
| --- | --- | --- |
| Event operations | `bash scripts/local-operations.sh` | PostgreSQL on 55439, Redis on 56379, seeded event and role accounts; no mail delivery service |
| Registration and mail | `uv run python install/local.py` | Isolated database on 55440 and capture-only mail on 8001; see [local launcher](install/LOCAL.md) |

The event launcher stores its settings in ignored `.env.operations.local` and
uses database `llh_operations_dev`. It applies migrations and runs the demo seeds;
use it to initialize a demo, not to reset an ongoing rehearsal. To restart only
the API with existing rehearsal data:

```bash
uv run --env-file .env.operations.local uvicorn main:app --host 127.0.0.1 --port 8000
```

Frontend processes start separately: HackEPS on 3001 (`/organitzacio` for scanning),
Live on 3000 and Gestió on 5175. Point them at this API. Keep real credentials and
external delivery workers out of a local rehearsal.

## Configure an existing environment

See [configuration](README-config.md) for secrets, mail, Redis and browser origins.
For a manually configured database and services:

```bash
cp .env.example .env
# Edit .env before running the following commands.
export PYTHONPATH=backend:.
uv run --env-file .env alembic upgrade head
uv run --env-file .env uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The generated mail client is versioned under `backend/generated_src`. When using
an existing environment, set `PYTHONPATH=backend:.` so imports resolve; the local
launchers and Docker image configure their import paths themselves.

## Verify and develop

- [Swagger](http://localhost:8000/docs), [ReDoc](http://localhost:8000/redoc),
  [OpenAPI](http://localhost:8000/openapi.json).
- `GET /health/live`: process liveness.
- `GET /health/ready`: database and Redis readiness; returns 503 when unavailable.
- Sign in using HTTP Basic at `GET /v1/auth/login`, then use the returned access
  token as a Bearer token. Company accounts use the separate company portal API.

```bash
uv run --frozen ruff check .
uv run --frozen ruff format --check .
# Requires disposable PostgreSQL and Redis; read tests/README.md first.
uv run --frozen pytest -q
```

[Tests](tests/README.md) reset the configured test database schema. Never use the
rehearsal or production database for the test suite.

Create migrations with `uv run --env-file .env alembic revision --autogenerate -m
"describe_change"`, review the generated SQL and rehearse preservation before a
production migration. Retain the complete Alembic history.

## Deployment

The supported production path is Docker Compose with immutable release images,
backups and explicit activation. Follow the [deployment runbook](docs/production-deploy.md).
GitHub Actions validates releases; merging a PR does not activate the backend.
The manual preparation workflow builds a candidate, not a production cutover.

The Dockerfile's default command applies migrations before starting Gunicorn.
Production Compose overrides that command to keep migrations a separate release
step. Do not substitute a bare `docker run` for the production runbook.

## Repository map

| Path | Responsibility |
| --- | --- |
| `main.py`, `App.py` | Application entry point and initialization |
| `src/impl/` | Domain models, schemas, services and routes |
| `src/configuration/Settings.py` | Environment settings and validation |
| `src/utils/` | Shared authentication, request protection and infrastructure helpers |
| `backend/generated_src/` | Required generated mail client; regenerate rather than hand-edit |
| `alembic/` | Versioned database migrations |
| `scripts/` | Local fixtures, administration and badge printing tools |
| `install/` | Isolated local API and captured mail launcher |
| `deploy/` | Release, backup/restore, monitoring and worker tooling |
| `tests/` | Regression suite against disposable services |
| `docs/` | [Documentation index](docs/README.md) |

See the [documentation index](docs/README.md) for event operations, integrations,
security and historical release notes.
