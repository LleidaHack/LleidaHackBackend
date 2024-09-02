FROM python:3.12-alpine
WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN pip install poetry && poetry install --no-root --no-dev
COPY . /app
#Cambiar url respecte a repo per clonar mail backend (integration o main)
RUN cd generated_src && poetry run openapi-python-client generate --url http://localhost:9000/openapi.json --meta=none && cd .. 
#
CMD ["poetry", "run", "python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
