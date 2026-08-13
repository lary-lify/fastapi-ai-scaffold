from typing import Any, Dict, List, Optional

from app.config.setting import settings


class Neo4jClient:
    """Neo4j graph-db wrapper (driver-level singleton)."""

    _driver = None

    def __init__(self):
        from neo4j import GraphDatabase

        cfg = settings.neo4j
        if Neo4jClient._driver is None:
            Neo4jClient._driver = GraphDatabase.driver(
                cfg.uri, auth=(cfg.user, cfg.password)
            )
        self._driver = Neo4jClient._driver
        self.database = cfg.database

    def execute_query(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        with self._driver.session(database=self.database) as session:
            return [record.data() for record in session.run(cypher, params or {})]

    def execute_write(self, cypher: str, params: Optional[Dict[str, Any]] = None):
        with self._driver.session(database=self.database) as session:
            return session.execute_write(
                lambda tx: tx.run(cypher, params or {}).consume()
            )

    def close(self) -> None:
        if Neo4jClient._driver is not None:
            Neo4jClient._driver.close()
            Neo4jClient._driver = None
