# FastAPI Starter

A reusable, production-oriented starter template for building asynchronous FastAPI services with Python 3.12+, PostgreSQL, SQLAlchemy 2.0, Alembic, JWT authentication, Pydantic Settings, HTTPX, pytest, Ruff and Docker.

The template provides the common foundation for a new API project while keeping domain-specific features easy to add. It includes a layered application structure, database migrations, user authentication, request IDs, CORS configuration, health checks and a small initial test suite.

## Features

- Async FastAPI application with a lifespan hook for shared resources
- Async SQLAlchemy sessions with PostgreSQL and `asyncpg`
- Alembic migrations
- User registration, login, refresh-token and OAuth2-compatible token endpoints
- Password hashing with Argon2 through `pwdlib`
- JWT access and refresh tokens
- Authenticated user endpoints and role-based authorization dependency
- Pydantic Settings with `.env` support
- Request ID middleware and centralized unhandled-error response
- Liveness and database readiness endpoints
- CORS configuration through environment variables
- Docker and Docker Compose setup
- pytest test suite and Ruff linting/formatting
- Reproducible dependency lockfile managed by `uv`

## Requirements

- Python 3.12 or newer
- [`uv`](https://docs.astral.sh/uv/)
- Docker and Docker Compose, if you want to run PostgreSQL locally through containers

## Quick start

### 1. Configure the environment

Copy the example environment file and update the values as needed:

```bash
cp .env.example .env
```

On PowerShell:

```powershell
Copy-Item .env.example .env
```

At minimum, replace `SECRET_KEY` with a long, random value. Never commit `.env` or real credentials to the repository.

### 2. Start PostgreSQL

To start only the database:

```bash
docker compose up -d db
```

The default local database is available at `localhost:5432` with:

```text
database: app
user:     postgres
password: postgres
```

These values are intended for local development only.

### 3. Install dependencies

```bash
uv sync
```

This installs both runtime and development dependencies and uses `uv.lock` when resolving packages.

### 4. Apply migrations

```bash
uv run alembic upgrade head
```

### 5. Run the API

```bash
uv run uvicorn app.main:app --reload
```

The service is now available at:

- API base URL: `http://localhost:8000/api/v1`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## Docker Compose

To build and run both PostgreSQL and the API:

```bash
docker compose up --build
```

The Compose API service waits for PostgreSQL to become healthy before starting. The current Compose command enables Uvicorn reload and is intended for development. For production, use a dedicated image and deployment configuration with reload disabled.

To stop the services:

```bash
docker compose down
```

To stop the services and remove the local database volume:

```bash
docker compose down -v
```

The last command deletes local PostgreSQL data and should only be used when that data is disposable.

## Configuration

Configuration is loaded from environment variables and `.env`. Environment variables take precedence over defaults.

| Variable | Description | Example |
| --- | --- | --- |
| `APP_NAME` | Application name shown in OpenAPI metadata | `FastAPI Starter` |
| `ENVIRONMENT` | Runtime environment | `development` |
| `DEBUG` | Enables FastAPI debug mode | `true` |
| `API_V1_PREFIX` | API route prefix | `/api/v1` |
| `SECRET_KEY` | Key used to sign JWTs; use a strong secret | `replace-me` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh-token lifetime | `7` |
| `DATABASE_URL` | Async SQLAlchemy database URL | `postgresql+asyncpg://postgres:postgres@localhost:5432/app` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000,http://localhost:8000` |
| `LOG_LEVEL` | Application log level | `INFO` |

For production:

- Set `ENVIRONMENT=production` and `DEBUG=false`.
- Generate a unique `SECRET_KEY` of at least 32 characters.
- Use a managed or secured PostgreSQL instance and credentials stored in a secret manager.
- Restrict `ALLOWED_ORIGINS` to trusted frontend origins.
- Do not expose PostgreSQL publicly unless required.
- Run migrations as an explicit deployment step before serving traffic.

## API overview

All routes are prefixed with `/api/v1` by default.

| Method | Endpoint | Authentication | Description |
| --- | --- | --- | --- |
| `GET` | `/health` | None | Liveness check |
| `GET` | `/ready` | None | Database readiness check |
| `POST` | `/auth/register` | None | Create a user |
| `POST` | `/auth/login` | None | Return access and refresh tokens |
| `POST` | `/auth/token` | None | OAuth2 form-compatible login endpoint |
| `POST` | `/auth/refresh` | None | Issue a new token pair |
| `GET` | `/users/me` | Bearer token | Return the current user |
| `GET` | `/users` | Bearer token | List users with pagination and search |
| `GET` | `/users/{user_id}` | Bearer token | Get a user by ID |
| `PATCH` | `/users/{user_id}` | Bearer token | Update the current user or an admin-managed user |

### Register and login

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","full_name":"Your Name","password":"correct horse battery staple"}'

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"correct horse battery staple"}'
```

The login response contains `access_token`, `refresh_token` and `token_type`. Use the access token for protected endpoints:

```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

The `/auth/token` endpoint accepts OAuth2 form fields (`username` and `password`) and is used by the Swagger UI authorization flow.

## Project structure

```text
.
├── app/
│   ├── api/             # Routers, dependencies and HTTP concerns
│   ├── core/            # Settings, security and logging
│   ├── models/          # SQLAlchemy models
│   ├── repositories/    # Database access
│   ├── schemas/         # Pydantic request/response schemas
│   ├── services/        # Business logic
│   ├── db.py            # Engine, session factory and declarative base
│   └── main.py          # FastAPI application and middleware
├── migrations/          # Alembic environment and migration versions
├── tests/               # Automated tests
├── .env.example         # Local configuration template
├── docker-compose.yml   # Local PostgreSQL and API services
├── Dockerfile           # Container image definition
├── Makefile             # Common development commands
├── pyproject.toml       # Dependencies and tool configuration
└── uv.lock              # Locked dependency versions
```

### Request flow

For a typical feature, keep responsibilities separated:

```text
HTTP request
    -> router
    -> schema validation
    -> service
    -> repository
    -> SQLAlchemy model / database
```

Routers should handle HTTP concerns, services should contain business rules, and repositories should contain database queries. This makes features easier to test and replace.

## Adding a new feature

For a new resource, the usual workflow is:

1. Add the SQLAlchemy model under `app/models/`.
2. Export the model from `app/models/__init__.py` if Alembic needs to discover it.
3. Add request and response schemas under `app/schemas/`.
4. Add database operations under `app/repositories/`.
5. Add business logic under `app/services/`.
6. Add the router under `app/api/routes/`.
7. Include the router in `app/api/router.py`.
8. Create and review a migration.
9. Add tests for the service and API behavior.

## Database migrations

Create a migration after changing SQLAlchemy models:

```bash
uv run alembic revision --autogenerate -m "describe change"
```

Always review autogenerated migrations before applying them. Apply the latest migrations with:

```bash
uv run alembic upgrade head
```

Useful commands:

```bash
uv run alembic current
uv run alembic history
uv run alembic downgrade -1
```

## Development commands

The same commands are available through the Makefile:

```bash
make install   # Install dependencies
make run       # Start the development server
make test      # Run tests
make lint      # Run Ruff checks
make format    # Format the code
make migrate   # Apply migrations
```

Equivalent `uv` commands:

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
uv run uvicorn app.main:app --reload
```

Run the complete local validation before committing:

```bash
uv run ruff check .
uv run pytest
```

## Testing

Tests are located in `tests/` and are configured to use automatic asyncio support. The current health endpoint test does not require a running database. Tests that exercise database-backed endpoints should use an isolated test database and should not depend on the development PostgreSQL volume.

## Runtime behavior

- Database sessions are created per request through `get_db`.
- The application creates one reusable `httpx.AsyncClient` during FastAPI lifespan and closes it during shutdown.
- Every request receives a request ID through `RequestContextMiddleware`; the ID is returned in the response headers and included in logs.
- `/health` checks process liveness, while `/ready` verifies database connectivity.
- Unhandled exceptions are logged and returned as a generic `500` response.
- Distributed rate limiting is intentionally not included; add it at the gateway or application layer according to deployment needs.

## Security notes

This repository is a strong starting point, not a complete security policy for every deployment. Before production use, review token rotation and revocation, password policy, email verification, account recovery, rate limiting, audit logging, TLS termination, secret management and database permissions.

Never commit:

- `.env` files containing secrets
- Production JWT keys
- Database credentials
- User data or generated dumps

## License

This template is distributed under the [MIT License](https://opensource.org/license/mit/).
