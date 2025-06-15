FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY App.py ./
COPY src/ src/
COPY generated_src/ generated_src/
COPY alembic/ alembic/
COPY alembic.ini ./
COPY main.py ./
COPY gunicorn_conf.py ./
COPY static/ static/

# Install dependencies with uv
RUN uv sync --no-cache

# Create placeholder mail client structure (real generation happens after services start)
RUN mkdir -p generated_src/lleida_hack_mail_api_client/models && \
    printf "# Generated mail API client\n" > generated_src/lleida_hack_mail_api_client/__init__.py && \
    printf "# Generated models\n" > generated_src/lleida_hack_mail_api_client/models/__init__.py && \
    printf "from typing import Any, Dict, Optional\n\nclass MailCreate:\n    def __init__(self, sender_id: Optional[int] = 0, receiver_id: Optional[str] = '', template_id: int = 0, subject: str = '', receiver_mail: Optional[str] = '', fields: str = ''):\n        self.sender_id = sender_id\n        self.receiver_id = receiver_id\n        self.template_id = template_id\n        self.subject = subject\n        self.receiver_mail = receiver_mail\n        self.fields = fields\n" > generated_src/lleida_hack_mail_api_client/models/mail_create.py

# Create logs directory
RUN mkdir -p logs

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Create startup script
RUN printf '#!/bin/bash\nset -e\n\necho "Starting backend initialization..."\n\n# Wait for database to be ready\necho "Waiting for database connection..."\nfor i in {1..30}; do\n  if uv run python -c "from src.configuration.Configuration import Configuration; from sqlalchemy import create_engine; engine = create_engine(Configuration.database.url); engine.connect().close(); print('"'"'Database connected successfully'"'"')" 2>/dev/null; then\n    echo "Database is ready!"\n    break\n  fi\n  echo "Waiting for database... ($i/30)"\n  sleep 2\ndone\n\n# Run Alembic migrations\necho "Running Alembic migrations..."\nuv run alembic upgrade head\n\n# Wait for mail backend and generate client\necho "Waiting for mail backend..."\nfor i in {1..60}; do\n  if curl -s http://mail-backend-integration:8001/health >/dev/null 2>&1; then\n    echo "Mail backend is ready, generating client..."\n    cd generated_src\n    uv run openapi-python-client generate --url http://mail-backend-integration:8001/openapi.json --meta=none --overwrite\n    cd ..\n    break\n  fi\n  echo "Waiting for mail backend... ($i/60)"\n  sleep 2\ndone\n\necho "Starting backend server..."\nuv run gunicorn main:app -c gunicorn_conf.py\n' > /app/start.sh && chmod +x /app/start.sh

# Run with startup script
CMD ["/app/start.sh"]