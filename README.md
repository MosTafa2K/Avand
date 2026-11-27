# Avand (آوند)

**Avand** is the backend API for a multi-vendor marketplace where users can create their own booths and manage products. It is built with FastAPI and uses PostgreSQL to store its data.

This project is designed as a foundation for a marketplace: it currently covers accounts, authentication, booths, and products, and can be extended.

## What can Avand do?

- Create an account and log in.
- Authenticate requests using JWT access and refresh tokens.
- Manage user profiles.
- Create a vendor profile automatically when needed.
- Create and manage booths.
- Add, edit, and remove products from booths.
- Browse active booths and products without logging in.
- Search products using product name and browse paginated results.
- Restrict booth and product management to their owners.
- Keep product data consistent using database constraints.

## Built with

| Tool | What it's used for |
|---|---|
| Python 3.12+ | The language used to build the project |
| FastAPI | Building the REST API |
| PostgreSQL | Storing application data |
| SQLAlchemy 2.x | Database access using an async ORM |
| asyncpg | Async PostgreSQL driver |
| Alembic | Managing database migrations |
| Pydantic v2 | Validating and serializing data |
| Pydantic Settings | Loading application configuration |
| PyJWT | Creating and validating JWTs |
| pwdlib / Argon2 | Secure password hashing |
| uv | Managing dependencies and the Python environment |
| Ruff | Linting and formatting |

## Getting started

Follow these steps to run Avand locally.

### 1. Requirements

Make sure you have installed:

- Python 3.12 or newer
- PostgreSQL
- [uv](https://docs.astral.sh/uv/)

### 2. Get the project

```bash
git clone <repository-url>
cd Avand
```

### 3. Set up your environment

Create your local `.env` file using the example:

**Windows PowerShell:**
```powershell
Copy-Item .env.example .env
```

**Linux/macOS:**
```bash
cp .env.example .env
```

Open `.env` and configure the database URL and secret key, along with any other settings you need.

### 4. Install dependencies

```bash
uv sync
```

### 5. Prepare the database

Apply the migrations:

```bash
uv run alembic upgrade head
```

### 6. Run Avand

```bash
uv run uvicorn app.main:app --reload
```

The server will be available at `http://localhost:8000`.

<details>
<summary>Useful links after starting the server</summary>

- **Swagger UI:** http://localhost:8000/docs — try the API interactively.
- **ReDoc:** http://localhost:8000/redoc — browse the API documentation.
- **OpenAPI schema:** http://localhost:8000/openapi.json — view or download the API schema.

</details>

## Configuration

Avand loads its configuration from environment variables and the `.env` file.

| Variable | Description | Example |
|---|---|---|
| `APP_NAME` | Name shown in API documentation | `Avand` |
| `ENVIRONMENT` | Current environment | `development` |
| `DEBUG` | Enable debug mode | `true` |
| `API_V1_PREFIX` | Prefix for API routes | `/api/v1` |
| `SECRET_KEY` | Key used to sign JWTs | Use a strong, private value |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://...` |
| `ALLOWED_ORIGINS` | Allowed origins for CORS | `http://localhost:3000` |
| `LOG_LEVEL` | Logging level | `INFO` |

Example database URL:

```text
postgresql+asyncpg://postgres:postgres@localhost:5432/avand
```

## API at a glance

All API routes use the `/api/v1` prefix by default. Protected endpoints require a Bearer access token.

### Health checks

| Method | Endpoint | Login required? | What it does |
|---|---|---|---|
| `GET` | `/health` | No | Checks that the application is running. |
| `GET` | `/ready` | No | Checks database connectivity. |

### Authentication

| Method | Endpoint | Login required? | What it does |
|---|---|---|---|
| `POST` | `/auth/register` | No | Creates a user account. |
| `POST` | `/auth/login` | No | Logs in and returns tokens. |
| `POST` | `/auth/refresh` | No | Refreshes the token pair. |
| `POST` | `/auth/token` | No | Provides an OAuth2-compatible token endpoint. |

### Users

| Method | Endpoint | Login required? | What it does |
|---|---|---|---|
| `GET` | `/users/me` | Yes | Shows your profile. |
| `GET` | `/users` | Yes | Lists users with pagination and optional search. |
| `GET` | `/users/{user_id}` | Yes | Gets a user by ID. |
| `PATCH` | `/users/{user_id}` | Yes | Updates a user, subject to authorization rules. |

### Booths

| Method | Endpoint | Login required? | What it does |
|---|---|---|---|
| `GET` | `/booths` | No | Browses active booths. |
| `POST` | `/booths` | Yes | Creates a booth for you. A vendor profile is created if needed. |
| `GET` | `/booths/me` | Yes | Lists your booths. |
| `GET` | `/booths/{booth_id}` | No | Views an active booth. |
| `GET` | `/booths/{booth_id}/products` | No | Lists active products in a booth, with pagination. |
| `PATCH` | `/booths/{booth_id}` | Yes | Updates a booth you own. |
| `DELETE` | `/booths/{booth_id}` | Yes | Deletes a booth you own. |

### Products

| Method | Endpoint | Login required? | What it does |
|---|---|---|---|
| `GET` | `/products` | No | Browses active products, with pagination, search, and optional `min_rating` filter (1–5). |
| `POST` | `/products/booths/{booth_id}` | Yes | Adds a product to a booth you own. |
| `GET` | `/products/me/booths/{booth_id}` | Yes | Lists your booth's products, including inactive ones. |
| `GET` | `/products/{product_id}` | No | Views an active product. |
| `PATCH` | `/products/{product_id}` | Yes | Updates a product you own. |
| `DELETE` | `/products/{product_id}` | Yes | Deletes a product you own. |

Supported `/products` query parameters include `search`, `min_price`, `max_price`, `min_rating`,
`city`, `sort_by=price|sales|created_at`, and `sort_order=asc|desc`.

### Orders

| Method | Endpoint | Login required? | What it does |
|---|---|---|---|
| `GET` | `/orders` | Yes | Lists your orders with pagination and optional `product_search`. |

For example, `GET /orders?product_search=عسل` returns only your orders containing a product
whose name matches «عسل».

## Using the API

### Register an account

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","full_name":"Your Name","password":"your-strong-password"}'
```

### Log in

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"your-strong-password"}'
```

The response includes your tokens. For protected endpoints, send the access token in the `Authorization` header.

### Make an authenticated request

```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

You can also try these requests directly through Swagger UI at `/docs`.

## Pagination and search

List endpoints that support pagination accept `page` and `size` query parameters. Product listing also supports a `search` parameter.

| Parameter | Description | Default / limits |
|---|---|---|
| `page` | Page to retrieve | `1` or higher |
| `size` | Items per page | Default: `20`, maximum: `100` |
| `search` | Search by product name(where supported) | Optional |

Example:

```http
GET /api/v1/products?page=1&size=20&search=keyboard
```

Paginated responses look like this:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "size": 20
}
```

## How the project is organized

Avand uses separate layers so each part of the application has a focused responsibility.

```text
.
├── app/
│   ├── api/
│   │   ├── routes/          # Endpoints and HTTP handling
│   │   ├── deps.py          # Shared dependencies
│   │   └── router.py        # Route registration
│   ├── core/                # Settings and security utilities
│   ├── models/               # SQLAlchemy database models
│   ├── repositories/         # Database queries
│   ├── schemas/              # Request and response schemas
│   ├── services/              # Business rules and operations
│   ├── db.py                 # Database engine and sessions
│   ├── middleware.py         # Request middleware
│   └── main.py               # Application entry point
├── migrations/               # Alembic migrations
├── tests/                    # Automated tests
├── .env.example              # Example configuration
├── alembic.ini               # Alembic configuration
├── pyproject.toml             # Project configuration and dependencies
└── uv.lock                   # Locked dependency versions
```

In a typical request, the router receives the request, the schema validates the data, the service applies business rules, and the repository handles database operations.

## Database migrations

When you change a database model, create a migration and review it before applying it.

Create a migration:

```bash
uv run alembic revision --autogenerate -m "describe change"
```

Apply migrations:

```bash
uv run alembic upgrade head
```

Check the current revision or migration history:

```bash
uv run alembic current
uv run alembic history
```

Undo the most recent migration:

```bash
uv run alembic downgrade -1
```

For database-backed tests, use a separate test database rather than your development or production database.

## Security notes

- Passwords are hashed instead of being stored as plaintext.
- Protected endpoints use JWT authentication.
- Booth and product management includes ownership checks.
- Database constraints help prevent invalid product data.
- Keep `.env` and secret keys out of version control.
- Use a strong, unique secret key.
- Configure CORS for the origins your application actually needs.
- Disable debug mode in production.

Before deploying to production, consider additional safeguards such as rate limiting, token revocation and rotation, email verification, account recovery, audit logging, TLS, and database access restrictions.

## License

This project is released under the [MIT License](LICENSE).
