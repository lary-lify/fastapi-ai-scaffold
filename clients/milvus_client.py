from typing import Any, List, Optional

from app.config.setting import settings


class MilvusClient:
    """Milvus vector-store wrapper. Heavy ``pymilvus`` import is deferred to connect().

    Keep this out of the default import path so the core app boots without
    installing the optional vector-stack dependencies.
    """

    def __init__(self, alias: Optional[str] = None):
        self.alias = alias or "default"
        self.cfg = settings.milvus
        self._collection = None
        self._m = None  # loaded pymilvus submodule handles

    def _load(self) -> None:
        from pymilvus import Collection, connections, utility

        self._m = {"Collection": Collection, "connections": connections, "utility": utility}

    def connect(self) -> "MilvusClient":
        self._load()
        self._m["connections"].connect(
            alias=self.alias,
            host=self.cfg.host,
            port=self.cfg.port,
            user=self.cfg.user,
            password=self.cfg.password,
            secure=False,
        )
        return self

    def disconnect(self) -> None:
        self._m["connections"].disconnect(self.alias)

    def has_collection(self, name: Optional[str] = None) -> bool:
        self._load()
        return self._m["utility"].has_collection(name or self.cfg.collection_name)

    def get_collection(self, name: Optional[str] = None):
        self._load()
        name = name or self.cfg.collection_name
        if self._collection is None:
            self._collection = self._m["Collection"](name, using=self.alias)
        return self._collection

    def insert(
        self,
        data: List[List[Any]],
        name: Optional[str] = None,
        partition_name: Optional[str] = None,
    ):
        return self.get_collection(name).insert(data, partition_name=partition_name)

    def search(
        self,
        vectors: List[List[float]],
        top_k: int = 5,
        name: Optional[str] = None,
        output_fields: Optional[List[str]] = None,
        metric_type: str = "L2",
    ):
        return self.get_collection(name).search(
            vectors,
            "vector",
            {"metric_type": metric_type, "params": {"ef": 32}},
            top_k=top_k,
            output_fields=output_fields or ["text"],
        )
