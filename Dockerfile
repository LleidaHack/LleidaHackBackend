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

# Default command (can be overridden in docker-compose.yml)
CMD sh -c 'uv run alembic upgrade head && uv run gunicorn main:app -c gunicorn_conf.py'