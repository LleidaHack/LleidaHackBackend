# Local backend

Requirements: Docker running, Python 3.12 and `uv`.

From the repository root:

```sh
uv sync
uv run python install/local.py
```

The launcher applies migrations to an isolated PostgreSQL 16 database in the
`lleidahack-local` container (loopback port 55440), starts a capture-only mail
service and serves the backend. It does not use production credentials.

- API documentation: http://127.0.0.1:8000/docs
- Captured messages: http://127.0.0.1:8001/messages
- Organizer email: `organizer@example.test`
- Organizer password: `organizer_password` in `.local-backend.json`

The ignored configuration file is generated with owner-only permissions. Keep it
alongside the database container so credentials match on subsequent starts.
Captured mail contains local verification links/tokens, is stored only in memory
and disappears on restart. No email is delivered externally.

Use the organizer credentials with `GET /v1/auth/login` (HTTP Basic), then use the
returned access token as a Bearer token for authenticated requests.

Ctrl+C stops the API and mail capture. PostgreSQL and its data remain available;
stop it separately with `docker stop lleidahack-local` when no longer needed.
Ports 8000 and 8001 must be available before starting the launcher.
