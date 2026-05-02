# FastAPI Foundation

A reusable FastAPI commons library that provides a pre-built, opinionated foundation for building production-ready FastAPI microservices. It eliminates repeated boilerplate setup — logging, error handling, authentication, database connectivity, dependency injection, and middleware — across every new service.

---

## Problems It Solves

| Pain Point | Solution |
|---|---|
| Repeated boilerplate for every new FastAPI service | `FastAPIFoundation` abstract base class to extend |
| Inconsistent error response shapes across services | Standardized `ApiResponse[T]` envelope with `status`, `code`, `error`, `data` |
| Manual MongoDB lifecycle management | `MongoDbClient` with async `connect/close` wired into app startup/shutdown |
| Repeated CRUD boilerplate for MongoDB | `BaseMongoRepository[T]` with `create`, `find_by_id`, `find_one`, `find_many`, `update_by_id`, `delete_by_id`, `count` |
| No SQL database support | `BaseSqlRepository[T]` + `SqlClient` — covers PostgreSQL & MySQL via SQLAlchemy async |
| No shared repository contract | `BaseRepository[T, IDType]` abstract interface — swap backends without changing service code |
| No structured logging | `JsonFormatter` + separate request/response log file; standard formatter in development |
| Missing JWT auth utilities | `AuthUtils` for creating/validating access & refresh tokens via `python-jose` |
| No DI wiring | `BaseDiContainer` via `dependency-injector` with a pluggable MongoDB provider |
| Unhandled exceptions leaking stack traces | `GlobalExceptionMiddleware` returns structured JSON for all unhandled errors |
| No request/response audit trail | `RequestResponseLoggerMiddleware` logs structured JSON for every request/response |
| Mobile client validation missing | `UserAgentMiddleware` parses and validates a custom `User-Agent` header |
| AWS Secrets Manager integration | `SecretManagerSettings` utility to pull secrets at startup |
| Docs hidden in production | `/docs` disabled automatically when `is_prod=True`; Scalar docs available at `/scalar` |
| No CORS handling | `CORSMiddleware` applied automatically by `add_common_wrappers()` |
| No built-in HTTP client | `HttpxClient` — async wrapper around `httpx.AsyncClient` with GET, POST, PUT support |

---

## Architecture Overview

```
fastapi_foundation/
├── app/
│   ├── foundation.py         # FastAPIFoundation — abstract FastAPI subclass to extend
│   └── run_config.py         # add_common_wrappers(), run_server() — middleware & server config
├── data/
│   ├── db/
│   │   ├── models/
│   │   │   ├── mongo_base_model.py    # MongoBaseModel — Pydantic base with ObjectId & timestamps
│   │   │   ├── mongo_con_details.py   # MongoConDetails — connection config model
│   │   │   └── sql_base_model.py      # SqlBaseModel — SQLAlchemy declarative base with id/timestamps
│   │   ├── mongo/
│   │   │   └── mongo_client.py        # MongoDbClient — async Motor wrapper
│   │   └── sql/
│   │       └── sql_client.py          # SqlClient — async SQLAlchemy engine/session (PostgreSQL & MySQL)
│   └── repositories/
│       ├── base_repository.py         # BaseRepository[T, IDType] — abstract CRUD interface
│       ├── base_mongo_repository.py   # BaseMongoRepository[T] — MongoDB implementation
│       └── base_sql_repository.py     # BaseSqlRepository[T] — PostgreSQL/MySQL implementation
├── di/
│   └── containers.py          # BaseDiContainer — dependency-injector base container
├── middlewares/
│   ├── global_exception_handler.py            # Catches all unhandled exceptions
│   ├── request_response_logger_middleware.py   # Logs every request/response as JSON
│   └── user_agent_middleware.py               # Validates custom mobile User-Agent header
├── models/
│   ├── api_response.py        # ApiResponse[T], Error, ErrorDescription, ErrorItem
│   ├── auth_models.py         # UserClaims
│   ├── secret_manager_settings.py  # AWS Secrets Manager client
│   └── user_agent_params.py   # UserAgentParams (platform, version, device)
├── routers/
│   └── info_router.py         # GET /health — built-in health check endpoint
└── utils/
    ├── auth_utils.py          # AuthUtils — JWT create/validate access & refresh tokens
    ├── date_time_utils.py     # Date/time helpers
    ├── error_handler_utils.py # HTTP status → human-readable error title mapping
    ├── httpx_client.py        # HttpxClient — async HTTP client wrapper (GET, POST, PUT)
    └── logger_utils.py        # setup_logging() — JSON + file logging configuration
```

---

## Installation

This package is distributed as `fastapi-foundation`. Install it from a local clone or as a private package:

```bash
# MongoDB only (default)
pip install -e ../fastapi_foundation

# PostgreSQL support
pip install -e "../fastapi_foundation[postgresql]"

# MySQL support
pip install -e "../fastapi_foundation[mysql]"

# or install all dependencies directly
pip install fastapi motor dependency-injector python-jose passlib httpx pydantic-settings \
            python-dotenv boto3 scalar-fastapi uvicorn uvloop httptools pytz cryptography

# Additional async SQL drivers (install the one matching your DB):
pip install asyncpg    # PostgreSQL
pip install aiomysql   # MySQL
```

---

## How to Use

### 1. Create Your App Class

Extend `FastAPIFoundation` and implement the required abstract methods:

```python
# my_service/app.py
from fastapi_foundation.app.foundation import FastAPIFoundation
from fastapi_foundation.di.containers import BaseDiContainer
from pydantic_settings import BaseSettings

class MySettings(BaseSettings):
    environment: str = "development"
    log_level: str = "INFO"
    mongodb_url: str
    db_name: str

class MyContainer(BaseDiContainer):
    pass

class MyApp(FastAPIFoundation):
    def get_settings(self) -> MySettings:
        return MySettings()

    def get_container(self) -> MyContainer:
        return MyContainer()

    def get_modules(self) -> list[str]:
        return []

    @property
    def app_name(self) -> str:
        return "My Service"

    @property
    def app_description(self) -> str:
        return "My service description"

    @property
    def is_debug(self) -> bool:
        return True

    @property
    def is_prod(self) -> bool:
        return False

    def on_startup(self):
        return []

    def on_shutdown(self):
        return []
```

### 2. Apply Common Middleware & Wrappers

```python
# my_service/main.py
from fastapi_foundation.app.run_config import add_common_wrappers
from my_service.app import MyApp

app = MyApp()
add_common_wrappers(app)

# Include your own routers
from my_service.routers import my_router
app.include_router(my_router, prefix="/api/v1")
```

### 3. Add MongoDB Support

Wire MongoDB into the DI container:

```python
from dependency_injector import providers
from fastapi_foundation.di.containers import BaseDiContainer
from fastapi_foundation.data.db.mongo.mongo_client import MongoDbClient

class MyContainer(BaseDiContainer):
    mongo_db_client = providers.Singleton(
        MongoDbClient,
        url="mongodb://localhost:27017",
        db_name="my_database"
    )
```

The base app automatically calls `connect()` on startup and `close()` on shutdown.

### 4. Create a MongoDB Repository

```python
from fastapi_foundation.data.repositories.base_mongo_repository import BaseMongoRepository
from fastapi_foundation.data.db.models.mongo_base_model import MongoBaseModel

class Product(MongoBaseModel):
    name: str
    price: float

class ProductRepository(BaseMongoRepository[Product]):
    def __init__(self, db_client):
        super().__init__(db_client, "products", Product)

# Usage
repo = ProductRepository(db_client)
product_id = await repo.create(Product(name="Widget", price=9.99))
product    = await repo.find_by_id(product_id)
products   = await repo.find_many({"price": {"$lt": 100}}, skip=0, limit=20)
total      = await repo.count({"category": "electronics"})
```

### 5. Add SQL Support (PostgreSQL or MySQL)

`SqlClient` is a thin async SQLAlchemy wrapper. The target database is chosen
entirely by the connection URL — no other code changes are needed.

```python
from fastapi_foundation.data.db.sql.sql_client import SqlClient

# PostgreSQL — requires: pip install asyncpg
pg_client = SqlClient("postgresql+asyncpg://user:pass@localhost:5432/mydb")

# MySQL — requires: pip install aiomysql
mysql_client = SqlClient("mysql+aiomysql://user:pass@localhost:3306/mydb")

await pg_client.connect()
await pg_client.create_all()  # creates tables (dev/test only; use Alembic in production)
```

### 6. Create a SQL Repository

Define your table as a `SqlBaseModel` subclass and wrap it with `BaseSqlRepository`:

```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Numeric
from fastapi_foundation.data.db.models.sql_base_model import SqlBaseModel
from fastapi_foundation.data.repositories.base_sql_repository import BaseSqlRepository

class Product(SqlBaseModel):
    __tablename__ = "products"

    name:  Mapped[str]   = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Numeric(10, 2))

class ProductRepository(BaseSqlRepository[Product]):
    def __init__(self, db_client):
        super().__init__(db_client, Product)

# Usage — filter_query is a list of SQLAlchemy column expressions
repo = ProductRepository(sql_client)
product_id = await repo.create(Product(name="Widget", price=9.99))
product    = await repo.find_by_id(product_id)
cheap      = await repo.find_many(
    filter_query=[Product.price < 100],
    skip=0,
    limit=20,
    sort_by=[Product.price.asc()],
)
total      = await repo.count([Product.category == "electronics"])
```

### 7. Swap Backends Without Changing Service Code

Both `BaseMongoRepository` and `BaseSqlRepository` implement the same
`BaseRepository[T, str]` interface, so you can depend on the abstract type
in your service layer and inject whichever backend you need:

```python
from fastapi_foundation.data.repositories.base_repository import BaseRepository

class ProductService:
    def __init__(self, repo: BaseRepository[Product, str]):
        self.repo = repo

    async def get_cheap_products(self):
        # Works with both MongoDB and SQL repositories
        return await self.repo.find_many(
            filter_query=...,  # dict for Mongo, list of expressions for SQL
            limit=50,
        )
```



```python
from fastapi_foundation.models.api_response import ApiResponse
from fastapi import APIRouter

router = APIRouter()

@router.get("/products/{id}", response_model=ApiResponse[Product])
async def get_product(id: str):
    product = await repo.find_by_id(id)
    return ApiResponse[Product](status="success", code=200, data=product)
```

### 8. JWT Authentication

```python
from fastapi_foundation.utils.auth_utils import AuthUtils

auth = AuthUtils(settings={
    "jwt_secret_key": "your-secret",
    "algorithm": "HS256",
    "access_token_expire_minutes": "60",
    "refresh_token_expire_days": "7"
})

access_token = auth.create_access_token({"sub": user_id})
refresh_token = auth.create_refresh_token({"sub": user_id})
claims = auth.validate_access_token(access_token)
```

### 9. AWS Secrets Manager

```python
from fastapi_foundation.models.secret_manager_settings import SecretManagerSettings

sm = SecretManagerSettings(secret_name="my-service/prod", region_name="us-east-1")
secrets = sm.get_secret(aws_access_key_id="...", aws_secret_access_key="...")
```

---

## Built-in Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Returns `{"status": "healthy"}` wrapped in `ApiResponse` |
| `GET` | `/scalar` | Scalar interactive API documentation UI |
| `GET` | `/docs` | Swagger UI (disabled when `is_prod=True`) |


---

## Middleware Stack (applied by `add_common_wrappers`)

Applied in order (outermost first at request time):

1. **`GlobalExceptionMiddleware`** — catches any unhandled exception and returns a structured JSON error response
2. **`CORSMiddleware`** — allows all origins, methods, and headers
3. **`UserAgentMiddleware`** — parses a custom `fastapi-foundation_cross_connect/version/...` User-Agent header and attaches `UserAgentParams` to `request.state` (can be disabled with `disable_ua_enforse=True`)
4. **`RequestResponseLoggerMiddleware`** — logs every request and response as structured JSON (can be disabled with `disable_logger=True`)

Exception handlers are also registered for `HTTPException` and `RequestValidationError`, both returning the standard `ApiResponse` error shape.

---

## Standard Error Response Shape

All errors — validation, HTTP, and unhandled — return this shape:

```json
{
  "status": "error",
  "code": 422,
  "error": {
    "message": "Validation Error",
    "title": "Invalid Input",
    "description": {
      "errors": [
        { "message": "body -> field_name: field required" }
      ]
    }
  },
  "data": null
}
```

---

## Key Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `motor` | Async MongoDB driver |
| `sqlalchemy[asyncio]` | Async SQL ORM — optional, install for PostgreSQL/MySQL support |
| `asyncpg` | Async PostgreSQL driver (used with SQLAlchemy) |
| `aiomysql` | Async MySQL driver (used with SQLAlchemy) |
| `dependency-injector` | Dependency injection container |
| `python-jose` | JWT encode/decode |
| `passlib` | Password hashing utilities |
| `pydantic-settings` | Settings management |
| `httpx` | Async HTTP client |
| `boto3` | AWS SDK (Secrets Manager) |
| `scalar-fastapi` | Scalar API docs UI |
| `uvicorn` | ASGI server |
