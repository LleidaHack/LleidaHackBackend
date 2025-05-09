FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev curl

RUN curl -Ls https://astral.sh/uv/install.sh | sh

COPY pyproject.toml .

RUN uv pip install -r <(uv pip compile pyproject.toml)

COPY . .

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "src.main:app", "--bind", "0.0.0.0:8000"]