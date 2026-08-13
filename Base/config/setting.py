from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from Base.utils.path import find_project_root


class BaseEnvSettings(BaseSettings):
    """Loads ``.env`` from the project root and rejects unknown env keys.

    Every concrete settings class inherits this so a single ``.env`` at the
    repo root drives all modules. Unknown variables are ignored (``extra=ignore``)
    to avoid fragile "allow everything" behavior.
    """

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def __init__(self, **kwargs):
        root = find_project_root()
        env_file = root / ".env"
        if env_file.exists():
            kwargs.setdefault("_env_file", str(env_file))
        super().__init__(**kwargs)


class AppSettings(BaseEnvSettings):
    name: str = Field("fastapi-ai-scaffold", alias="APP_NAME")
    env: str = Field("dev", alias="APP_ENV")  # dev | prod
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    cors_origins: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8000"],
        alias="CORS_ORIGINS",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("log_level")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper()

    @field_validator("env")
    @classmethod
    def _lower_env(cls, v: str) -> str:
        return v.lower()


class DatabaseSettings(BaseEnvSettings):
    # Async database URL, e.g. sqlite+aiosqlite:///./dev.db or
    # mysql+aiomysql://user:pass@host:3306/db
    url: str = Field("sqlite+aiosqlite:///./dev.db", alias="DATABASE_URL")
    echo: bool = Field(False, alias="DB_ECHO")


class RedisSettings(BaseEnvSettings):
    host: str = Field("localhost", alias="REDIS_HOST")
    port: int = Field(6379, alias="REDIS_PORT")
    db: int = Field(0, alias="REDIS_DB")
    password: Optional[str] = Field(None, alias="REDIS_PASSWORD")


class MilvusSettings(BaseEnvSettings):
    host: str = Field("localhost", alias="MILVUS_HOST")
    port: int = Field(19530, alias="MILVUS_PORT")
    user: Optional[str] = Field(None, alias="MILVUS_USER")
    password: Optional[str] = Field(None, alias="MILVUS_PASSWORD")
    collection_name: str = Field("demo_collection", alias="MILVUS_COLLECTION_NAME")
    vector_dim: int = Field(768, alias="VECTOR_DIM")


class Neo4jSettings(BaseEnvSettings):
    uri: str = Field("bolt://localhost:7687", alias="NEO4J_URI")
    user: str = Field("neo4j", alias="NEO4J_USER")
    password: Optional[str] = Field(None, alias="NEO4J_PASSWORD")
    database: str = Field("neo4j", alias="NEO4J_DATABASE")


class AuthSettings(BaseEnvSettings):
    jwt_secret: str = Field("change-me-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    @model_validator(mode="after")
    def _require_secret(self):
        if not self.jwt_secret or not self.jwt_secret.strip():
            raise ValueError("JWT_SECRET must be set (non-empty) in .env")
        return self


class Settings(BaseEnvSettings):
    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    milvus: MilvusSettings = Field(default_factory=MilvusSettings)
    neo4j: Neo4jSettings = Field(default_factory=Neo4jSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


settings = get_settings()
