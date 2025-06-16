FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p logs generated_src

EXPOSE 8000

# Run migrations, generate client, then start server
CMD sh -c 'uv run alembic upgrade head && uv run openapi-python-client generate --url http://mail-backend-local:8001/openapi.json --output-path generated_src/lleida_hack_mail_api_client --meta=none --overwrite 2>/dev/null || echo "Client generation skipped"; uv run gunicorn main:app -c gunicorn_conf.py'