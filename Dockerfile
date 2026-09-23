FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim@sha256:e5b65587bce7de595f299855d7385fe7fca39b8a74baa261ba1b7147afa78e58

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PYTHONPATH=/app/backend \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
COPY backend ./backend
COPY alembic ./alembic
COPY static ./static
COPY App.py main.py gunicorn_conf.py alembic.ini ./
RUN chmod -R a+rX src backend alembic static App.py main.py gunicorn_conf.py alembic.ini \
    && groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app \
    && mkdir -p logs && chown app:app logs
USER 10001:10001
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec gunicorn main:app -c gunicorn_conf.py"]
