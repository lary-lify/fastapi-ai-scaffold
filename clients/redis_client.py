from typing import Any, Dict, List, Optional

from Base.config.setting import settings


class RedisClient:
    """Thin wrapper over redis-py (process-level connection-pool singleton)."""

    _pool = None

    def __init__(self, db: Optional[int] = None, decode_responses: bool = True):
        import redis  # lazy import — redis is an optional dependency

        cfg = settings.redis
        self.db = db if db is not None else cfg.db
        if RedisClient._pool is None:
            RedisClient._pool = redis.ConnectionPool(
                host=cfg.host,
                port=cfg.port,
                password=cfg.password,
                db=self.db,
                decode_responses=decode_responses,
                max_connections=50,
                health_check_interval=30,
            )
        self._client = redis.Redis(connection_pool=RedisClient._pool)

    @property
    def client(self):
        return self._client

    def ping(self) -> bool:
        return bool(self._client.ping())

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        return bool(self._client.set(key, value, ex=ex))

    def get(self, key: str) -> Optional[str]:
        return self._client.get(key)

    def delete(self, *keys: str) -> int:
        return int(self._client.delete(*keys))

    def exists(self, key: str) -> bool:
        return bool(self._client.exists(key))

    def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        return int(self._client.hset(name, mapping=mapping))

    def hgetall(self, name: str) -> Dict[str, Any]:
        return self._client.hgetall(name)

    def lpush(self, name: str, *values: Any) -> int:
        return int(self._client.lpush(name, *values))

    def lrange(self, name: str, start: int = 0, end: int = -1) -> List[Any]:
        return self._client.lrange(name, start, end)

    def close(self) -> None:
        self._client.close()


def get_redis() -> RedisClient:
    """FastAPI dependency returning a RedisClient instance."""
    return RedisClient()
