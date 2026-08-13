# FastAPI AI Scaffold

一个开箱即用的 **FastAPI AI 后端起步模板**（分层结构 + 异步 SQLAlchemy + JWT 认证 + 统一响应 + 可选 Redis / Milvus / Neo4j 客户端）。基于原 `fastapi-ai-scaffold`（ric-train）skill 的架构**重设计**，修复了原版多处安全隐患（任意 SQL 端点、非法 CORS、臃肿依赖）。

> 适用：AI 项目的后端底座、需要快速起一个带认证与 DB 层的 API 服务、作为 Agent / RAG 系统的 HTTP 入口。

## 特性

- **异步优先**：FastAPI + 异步 SQLAlchemy 2.0（`AsyncSession` / `async_sessionmaker`），`DATABASE_URL` 一行切换 SQLite / MySQL
- **数据库迁移**：内置 Alembic，初始迁移含 `users` 表
- **JWT 认证**：`/auth/login`、`/auth/me`，bcrypt 密码哈希；`JWT_SECRET` 启动时校验（占位值直接拒绝 prod 启动）
- **统一响应 / 异常处理**：`ApiResponse{code,message,data}`；业务异常 / 校验 / HTTP 错误统一信封；生产环境不泄露内部错误
- **CORS 正确姿势**：显式 `CORS_ORIGINS` 列表，绝不 `*` + credentials
- **结构化日志**：彩色控制台 + 按天滚动文件，`X-Request-ID` 请求中间件
- **可选客户端**：Redis / Milvus / Neo4j 包装层均为**懒加载**，不装重依赖也能跑核心
- **代码门禁**：ruff + pre-commit，CI 同步跑 lint + pytest

## 目录结构

```
fastapi-ai-scaffold/
├── main.py                 # 入口：日志 → CORS → 请求日志 → 异常处理器 → 路由 → lifespan
├── app/
│   ├── config/             # setting.py（pydantic-settings, extra=ignore）· log.py（彩色+滚动日志）
│   ├── db/                 # base.py（async engine/session/get_db/init_db）· models/user.py（User ORM）
│   ├── schemas/            # user.py（Pydantic 出入参）
│   ├── security/           # jwt.py（签发/校验/get_current_user）· password.py（bcrypt）
│   ├── common/             # response.py（ApiResponse）· exceptions.py（统一处理器）
│   ├── middleware/         # request_log.py（X-Request-ID + 耗时）
│   └── routers/            # health.py · auth.py · users.py（DB CRUD，受保护）
├── clients/                # redis_client.py · milvus_client.py · neo4j_client.py（懒加载）
├── migrations/             # Alembic env + 0001_initial（users）
├── tests/                  # conftest + health/auth/users（pytest，sqlite）
├── scripts/                # scaffold.py（生成新项目）
├── requirements.txt        # 核心依赖（~15 包）
├── requirements-extras.txt # 可选栈：pymilvus / neo4j / minio / langchain / openai
├── requirements-dev.txt    # pytest / ruff / alembic
├── pyproject.toml          # ruff + pytest（pythonpath）配置
├── Dockerfile + docker-compose.yml   # 应用 + MySQL + Redis（+ 可选 Milvus/Neo4j profile）
├── Makefile · .env.template · SKILL.md
└── README.md
```

## 快速开始（本地，零依赖）

```bash
cp .env.template .env                     # 默认 SQLite，开箱即跑；设置 JWT_SECRET
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
python main.py                            # http://localhost:8000/docs
```

首次启动会种入一个 demo 管理员（`admin` / `admin123`），`/auth/login` 直接可用；正式部署前请覆盖或关闭自动种用户。

运行测试（隔离 SQLite，完全离线）：

```bash
pytest tests -q
```

## 认证用法

```bash
# 1. 登录拿 token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 2. 带 token 访问受保护接口
curl http://localhost:8000/auth/me -H "Authorization: Bearer <TOKEN>"
```

## 数据库迁移（Alembic）

开发期 `init_db()` 会用 `create_all` 建表（零配置）；生产环境请改用 Alembic 管理 schema：

```bash
python -m alembic upgrade head                       # 首次建表
alembic revision --autogenerate -m "add column xxx"  # 改模型后生成迁移
alembic upgrade head
```

切换到 MySQL：在 `.env` 设置 `DATABASE_URL=mysql+aiomysql://user:pass@host:3306/db`（需 `pip install aiomysql`）。

## Docker 一键起

```bash
docker compose up -d                       # 应用 + MySQL + Redis
docker compose --profile vector up -d     # 额外起 Milvus 栈
docker compose --profile graph up -d      # 额外起 Neo4j
```

## 相比原脚手架（ric-train）的优化

| 项 | 原版 | 本版 |
|----|------|------|
| 任意 SQL | `POST /execute_sql` 跑任意 SQL（致命） | **已删除**，仅走 ORM/CRUD |
| CORS | `allow_origins=["*"]` + credentials（非法） | 显式 `CORS_ORIGINS` |
| 依赖 | 145 包大杂烩（含 Django/nibabel） | 核心 ~15 包 + `requirements-extras.txt` |
| DB 层 | 同步 pymysql，无 ORM | 异步 SQLAlchemy 2.0 + Alembic |
| 配置 | `extra="allow"`，secret 不校验 | `extra="ignore"`，启动时校验 secret |
| 错误处理 | 原始 `f"err: {exc}"` 泄露 | 统一信封，prod 不泄露 |
| 代码门禁 | 无 | ruff + pre-commit + CI |
| 包命名 | 顶层 `Base` | 标准 `app` 包 |

## 生产化建议

- 通过环境变量注入强随机 `JWT_SECRET`，生产环境关闭自动种用户
- 配置正式 `CORS_ORIGINS`，不要用 `*`
- 用 Alembic 管理 schema（已内置），关闭 `init_db` 的自动建表
- 给可选客户端（Redis / Milvus / Neo4j）配置鉴权与超时

## License

MIT
