# __PROJECT_NAME__

A clean, production-minded **FastAPI AI backend scaffold** — generic infrastructure only, no business code. Drop it in, fill `.env`, and you have auth, a relational DB layer, unified responses, structured logging, and optional Redis / Milvus / Neo4j clients.

> This is a **redesign** of the older `fastapi-ai-scaffold` (a.k.a. "ric-train") skill. See [What changed](#what-changed-vs-the-old-base-scaffold) below.

## Features

- **Async everywhere** — FastAPI + async SQLAlchemy 2.0 (`AsyncSession`, `async_sessionmaker`).
- **Migrations** — Alembic wired up with an initial `users` table.
- **Auth** — JWT issuance/validation (`/auth/login`, `/auth/me`) with bcrypt password hashing; `JWT_SECRET` is validated at startup (refuses to run in prod with the placeholder).
- **Unified API envelope** — `ApiResponse{code,message,data}`; `BusinessError` + validation + HTTP errors all render consistently. Internal errors are never leaked in `prod`.
- **CORS done right** — explicit `CORS_ORIGINS` list; never `*` + credentials.
- **Structured logging** — colored console + daily-rotated files, `X-Request-ID` request middleware.
- **Optional clients** — Redis / Milvus / Neo4j wrappers with **lazy imports**, so the core runs without installing the heavy vector/graph stacks.
- **Quality gates** — `ruff` lint + `pytest` in CI, `pre-commit` config, `Makefile`.

## Architecture

```
main.py                      Entry: logging → CORS → request-log → exception handlers → routers → lifespan
app/
  config/                   setting.py (pydantic-settings, extra=ignore, validated secret)
                            log.py (colored + rotating logging)
  db/                       base.py (async engine, session, get_db, init_db)
                            models/user.py (User ORM)
  schemas/                  user.py (Pydantic in/out schemas)
  security/                 jwt.py (create/decode/get_current_user)
                            password.py (bcrypt hash/verify)
  common/                   response.py (ApiResponse) / exceptions.py (handlers)
  middleware/               request_log.py (X-Request-ID + timing)
  routers/                  health.py / auth.py / users.py (DB-backed, protected)
clients/                    redis_client.py / milvus_client.py / neo4j_client.py (lazy imports)
migrations/                 Alembic env + 0001_initial (users)
tests/                      conftest + health/auth/users (pytest, sqlite)
requirements.txt            lean core deps
requirements-extras.txt     optional: pymilvus / neo4j / minio / langchain / openai
requirements-dev.txt        pytest / ruff / alembic
pyproject.toml              ruff + pytest (pythonpath) config
Dockerfile + docker-compose.yml   app + mysql + redis (+ optional milvus/neo4j via profiles)
Makefile / .github/workflows/ci.yml
```

## Quick start

```bash
cp .env.template .env          # then set JWT_SECRET and DB url
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python main.py                 # http://localhost:8000/docs
```

A demo admin user (`admin` / `admin123`) is seeded on first boot so `/auth/login` works immediately.
Override it (or disable seeding) before any real deployment.

### Run the tests

```bash
pytest tests -q
```

Tests use an isolated SQLite DB and run fully offline.

### Database

- Dev default: `sqlite+aiosqlite:///./dev.db` (zero config).
- Production: set `DATABASE_URL=mysql+aiomysql://user:pass@host:3306/db`.
- Migrations: `python -m alembic upgrade head`. `init_db()` in the lifespan is a dev convenience
  (creates tables from metadata); rely on Alembic for production.

### Docker

```bash
docker compose up -d                       # app + mysql + redis
docker compose --profile vector up -d     # also milvus stack
docker compose --profile graph up -d      # also neo4j
```

## API

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | public | liveness probe |
| POST | `/auth/login` | public | exchange credentials for JWT |
| GET | `/auth/me` | JWT | current user |
| GET | `/users` | JWT | list users |
| GET | `/users/{id}` | JWT | get user |
| POST | `/users` | JWT | create user |
| PUT | `/users/{id}` | JWT | update user |
| DELETE | `/users/{id}` | JWT | delete user |

## What changed vs the old `Base/` scaffold

| Area | Old | New |
|------|-----|-----|
| Arbitrary SQL | `POST /execute_sql` ran **any** SQL (critical hole) | **removed**; auth + DB-backed CRUD instead |
| CORS | `allow_origins=["*"]` + `allow_credentials=True` (invalid) | explicit `CORS_ORIGINS` list |
| Dependencies | 145-pkg freeze (Django, scikit-learn, nibabel…) | lean core (~15 pkgs) + `requirements-extras.txt` |
| DB layer | sync `pymysql`, no ORM | async SQLAlchemy 2.0 + Alembic |
| Settings | `extra="allow"` | `extra="ignore"` |
| JWT secret | optional, could be `None` | validated, placeholder rejected in prod |
| Error handling | raw `f"err: {exc}"` leaked | unified envelope, no leak in prod |
| Lint | none | `ruff` + pre-commit + CI gate |
| Package naming | top-level `Base` | standard `app` package |

## Use as a WorkBuddy skill

Copy this folder into `~/.workbuddy/skills/fastapi-ai-scaffold/` (or `<project>/.workbuddy/skills/`).
See `SKILL.md`. To instantiate a new project with a custom name:

```bash
python scripts/scaffold.py --target my_api --name my_api
```
