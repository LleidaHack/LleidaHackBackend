# LleidaHack Backend

API backend de LleidaHack construida con FastAPI, SQLAlchemy y Alembic.

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL (local o remoto)
- Redis compartido para limitar peticiones (ver [configuración](docs/request-protection.md))

## 1) Configuración inicial

Desde la raíz del proyecto:

```bash
uv sync --frozen
cp .env.example .env
```

Edita `.env` y configura al menos:

```env
DATABASE__URL=postgresql://usuario:password@host:5432/base_de_datos
SECURITY__SECRET_KEY=tu-secret-key
SECURITY__SERVICE_TOKEN=tu-service-token
CLIENTS__MAIL_CLIENT__URL=http://mail:8000/
RATE_LIMIT__REDIS_URL=redis://127.0.0.1:6379/0
```

Notas:
- Sustituye los secretos de ejemplo por valores aleatorios independientes de al menos 32 caracteres.
- Redis debe estar disponible: sin él, el backend rechaza temporalmente las peticiones con 503.
- `DATABASE__URL` es obligatorio en entorno `ENV=main`.
- Si quieres usar integración, puedes ejecutar con `ENV=integration` y `INTEGRATION_POSTGRES_PASSWORD`.

## 2) Preparar base de datos

Aplica todas las migraciones:

```bash
uv run alembic upgrade head
```

## 3) Ejecutar el backend en local

Para el entorno de pruebas aislado con PostgreSQL, Redis y correo capturado (requiere Docker):

```bash
uv run python install/local.py
```

Modo desarrollo (autoreload), con los servicios ya configurados:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Modo similar a producción (Gunicorn + Uvicorn workers):

```bash
uv run gunicorn main:app -c gunicorn_conf.py
```

## 4) Verificar que funciona

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- OpenAPI: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## 5) Ejecución con Docker

El `Dockerfile` ya instala dependencias, ejecuta migraciones y levanta Gunicorn.

```bash
docker build -t lleidahack-backend --build-arg GIT_BRANCH=main .
docker run --rm -p 8000:8000 --env-file .env lleidahack-backend
```

Asegúrate de que la `DATABASE__URL` del `.env` sea accesible desde el contenedor.

## 6) Comandos útiles

Crear nueva migración:

```bash
uv run alembic revision --autogenerate -m "descripcion_del_cambio"
```

Aplicar migraciones pendientes:

```bash
uv run alembic upgrade head
```

Revertir última migración:

```bash
uv run alembic downgrade -1
```

## Problemas comunes

- Error de `DATABASE__URL` faltante: revisa `.env` y que estés ejecutando en la raíz del repo.
- Error de conexión a BD: valida host, puerto, usuario, password y permisos.
- Fallo con `uv`: instala `uv` o usa Python 3.12 con entorno virtual y pip (no recomendado en este repo porque existe `uv.lock`).
