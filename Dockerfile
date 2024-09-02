FROM python:3.12-alpine
WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN pip install poetry && poetry install --no-root --no-dev
COPY . /app
EXPOSE 9000
#Cambiar url respecte a repo
RUN cd generated_src && poetry run openapi-python-client generate --url http://localhost:9000/openapi.json && cd .. 
#
CMD ["poetry", "run", "python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]