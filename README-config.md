# Configuration

Copy `.env.example` to `.env` and provide independent random JWT and service
secrets of at least 32 characters, a PostgreSQL URL, mail URL and private Redis
URL. Integration also requires an explicit `DATABASE__URL`; there is no default
password. Never commit runtime `.env` files or private keys.

Pass the environment explicitly when using the CLI:

```sh
uv run --env-file .env alembic upgrade head
uv run --env-file .env gunicorn main:app -c gunicorn_conf.py
```

For Docker use `--env-file .env`; the file is excluded from the build context and
image. For systemd use an appropriately protected EnvironmentFile. Configure
`CORS_ORIGINS` as a JSON array of exact origins, without URL paths or wildcards.
For same-origin frontends the default empty list is sufficient.

For the isolated local development environment use `uv run python install/local.py`.
It generates ignored random credentials and explicitly permits local frontend
origins. The verification shortcut is registered only by that launcher and is
excluded from the production image.

See [request protection](docs/request-protection.md) and
[public repository security review](docs/public-repository-security.md).
