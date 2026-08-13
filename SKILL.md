---
name: fastapi-ai-scaffold
description: 生成一套自包含、可分享的 FastAPI AI 后端脚手架（通用基础设施骨架，不含业务代码）。需要快速起一个新 FastAPI 项目、或把现有脚手架打包成可复用能力时使用。覆盖异步 SQLAlchemy + Alembic、JWT 鉴权（bcrypt）、统一响应、全局异常、CORS、请求日志中间件、Redis/Milvus/Neo4j 可选客户端、pytest、ruff、Makefile、CI、docker-compose。
---

# FastAPI AI Scaffold (redesigned)

Generate a self-contained, shareable FastAPI AI backend scaffold. Bundles only
**generic infrastructure** (no business source code), so it can be handed to
others without leaking code or credentials.

This is a redesign of the earlier `fastapi-ai-scaffold` ("ric-train") skill:
the layered architecture is kept, but the security and dependency problems are
fixed (no `/execute_sql`, no `CORS *`+credentials, lean dependency set, async
ORM + Alembic, validated JWT secret, lint gate).

## When to use

- "起一个新 FastAPI 项目 / 后端脚手架"
- "要一个带 MySQL/JWT/统一响应/可选向量库的 FastAPI 模板"
- "把这套 FastAPI 骨架打包成可分享的 skill"

## Architecture (generated project)

```
main.py                  FastAPI 入口：日志 → CORS(显式来源) → 请求日志 → 全局异常 → 路由 → 优雅停机
Base/
  config/               setting.py（pydantic-settings, extra=ignore, JWT secret 校验）+ log.py（彩色+轮转日志）
  db/                   base.py（异步引擎/Session/get_db/init_db）+ models/user.py（User ORM）
  schemas/              user.py（Pydantic 入参/出参）
  security/             jwt.py（签发/校验 + get_current_user）+ password.py（bcrypt 哈希/校验）
  common/               response.py（ApiResponse 统一响应）/ exceptions.py（BusinessError + 全局处理器）
  middleware/           request_log.py（X-Request-ID + 耗时）
  routers/              health.py / auth.py（login+me）/ users.py（基于 DB 的受保护 CRUD）
clients/                redis_client / milvus_client / neo4j_client（懒加载，核心不依赖重包）
migrations/             Alembic env + 0001_initial（users 表）
tests/                  conftest + test_health / test_auth / test_users（pytest，sqlite）
requirements.txt        核心依赖（精简）
requirements-extras.txt 可选：pymilvus / neo4j / minio / langchain / openai
requirements-dev.txt    pytest / ruff / alembic
pyproject.toml          ruff + pytest(pythonpath) 配置
Dockerfile + docker-compose.yml   app + mysql + redis（+ 可选 milvus/neo4j profile）
Makefile / .github/workflows/ci.yml
.env.template           已脱敏，分享安全
```

## How to generate a project

```bash
python scripts/scaffold.py --target <new_project_dir> --name <project_name>
# e.g.
python scripts/scaffold.py --target my_api --name my_api
```

The generator copies the repo (skipping `.git`/venv/caches), substitutes the
`__PROJECT_NAME__` placeholder, and copies `.env.template` → `.env`.

## How the other person runs it

```bash
cd <new_project_dir>
cp .env.template .env      # 填写 JWT_SECRET / 数据库等
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py             # http://localhost:8000/docs
# or: docker compose up -d
```

A demo admin (`admin` / `admin123`) is seeded on first boot.

## How to share this skill

Copy the whole `fastapi-ai-scaffold/` folder to the recipient's:
- user-level: `~/.workbuddy/skills/`, or
- project-level: `<project>/.workbuddy/skills/`

No source code, no credentials, no network needed. They just invoke the skill.

## Key design rules (do not regress)

- No `/execute_sql` or any arbitrary-SQL endpoint in the base scaffold.
- `CORS_ORIGINS` is an explicit list; never `allow_origins=["*"]` with credentials.
- Keep `requirements.txt` lean; optional heavy deps go in `requirements-extras.txt`.
- `JWT_SECRET` must be non-empty; the placeholder is rejected when `APP_ENV=prod`.
- Secrets/config come only from `.env` (gitignored) / `.env.template` (sanitized).
