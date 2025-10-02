"""Utility helpers to query PostgreSQL vector tables using pgvector."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional

from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from pgvector.psycopg2 import register_vector


class PostgresVectorStore:
    """Lightweight helper to run similarity search against a pgvector table."""

    def __init__(
        self,
        table_name: str,
        *,
        dsn: Optional[str] = None,
        min_connections: int = 1,
        max_connections: int = 5,
    ) -> None:
        if not table_name:
            raise ValueError("A table name must be provided for the vector store.")

        self.table_name = table_name
        self._dsn = dsn or os.getenv("DATABASE_URL")
        if not self._dsn:
            raise ValueError("DATABASE_URL (or explicit dsn) is required for PostgresVectorStore.")

        try:
            self._pool = SimpleConnectionPool(min_connections, max_connections, self._dsn)
        except Exception as exc:  # pragma: no cover - connection issues bubble up
            raise RuntimeError(f"Failed to create Postgres connection pool: {exc}") from exc

    @contextmanager
    def _connection(self):
        conn = self._pool.getconn()
        try:
            register_vector(conn)
            yield conn
        finally:
            self._pool.putconn(conn)

    def similarity_search(
        self,
        embedding: Iterable[float],
        *,
        limit: int = 10,
        fetch_multiplier: int = 3,
    ) -> List[Dict[str, Any]]:
        """Return the closest rows ordered by vector cosine distance."""

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        fetch_limit = max(limit * fetch_multiplier, limit)

        query = sql.SQL(
            """
            SELECT
                id,
                conteudo_original,
                fonte_documento,
                dado_sensivel,
                apenas_para_si,
                areas_liberadas,
                nivel_hierarquico_minimo,
                geografias_liberadas,
                projetos_liberados,
                idioma,
                data_validade,
                responsavel,
                aprovador,
                data_ingestao,
                vetor <=> %s::vector AS distancia
            FROM {table}
            ORDER BY vetor <=> %s::vector
            LIMIT %s;
            """
        ).format(table=sql.Identifier(self.table_name))

        with self._connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (list(embedding), list(embedding), fetch_limit))
                rows = cur.fetchall()

        return rows

    def close(self) -> None:
        """Close all pooled connections."""
        if hasattr(self, "_pool") and self._pool:
            self._pool.closeall()

    def __del__(self):
        try:
            self.close()
        except Exception:  # pragma: no cover - best effort clean up
            pass
