# Backend regression tests

Run against a disposable PostgreSQL database. Tests require a database name ending
in `_test` and reset its public schema before applying the actual Alembic migrations.
Never point `TEST_DATABASE_URL` at a shared database.

```sh
docker run -d --name lleidahack-refactor-tests \
  -e POSTGRES_USER=audit_test -e POSTGRES_PASSWORD=local-test-password \
  -e POSTGRES_DB=lleidahack_test -p 127.0.0.1:55439:5432 postgres:16
docker run -d --name lleidahack-rate-limit \
  -p 127.0.0.1:56379:6379 redis:7-alpine
uv sync --frozen
uv run pytest -q
```

Set `TEST_DATABASE_URL` to use another disposable database. Mail is mocked before
application initialization and no real email is sent. The generated mail client
is imported from the versioned `backend/` directory.

Tests also require Redis (`TEST_REDIS_URL`, default `redis://127.0.0.1:56379/15`).
Each run uses a random key prefix; cleanup only deletes that run’s keys.
The limiter stays enabled during all HTTP regression tests.
