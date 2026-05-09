"""Helpers for loading and running named QD queries.

The queries live in ``src/database/queries.sql`` and are grouped by comment
headers such as ``-- QD-Sec1: ...`` so the Python layer can execute them by
section name.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from backend.database import get_db_connection

QD_SECTION_PATTERN = re.compile(
    r"^\s*--\s*(QD-Sec[\w-]+)\s*:\s*(.+?)\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class QueryResult:
    """Simple container for query output."""

    columns: tuple[str, ...]
    rows: list[dict[str, Any]]


class QueryManager:
    """Load and execute named QD queries from the shared SQL library."""

    def __init__(self, queries_path: str | Path | None = None) -> None:
        self.queries_path = (
            Path(queries_path) if queries_path else self._default_queries_path()
        )
        self._queries = self._load_queries(self.queries_path)

    @staticmethod
    def _default_queries_path() -> Path:
        return Path(__file__).resolve().parents[1] / "database" / "queries.sql"

    @staticmethod
    def _normalize_query_name(name: str) -> str:
        return name.strip().upper()

    def _load_queries(self, path: Path) -> dict[str, str]:
        if not path.exists():
            raise FileNotFoundError(f"Query library not found: {path}")

        queries: dict[str, str] = {}
        current_name: str | None = None
        buffer: list[str] = []

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            match = QD_SECTION_PATTERN.match(raw_line)
            if match:
                if current_name and buffer:
                    queries[current_name] = self._finalize_query(buffer)
                current_name = self._normalize_query_name(match.group(1))
                buffer = []
                continue

            if current_name is not None:
                buffer.append(raw_line)

        if current_name and buffer:
            queries[current_name] = self._finalize_query(buffer)

        return queries

    @staticmethod
    def _finalize_query(lines: Iterable[str]) -> str:
        query = "\n".join(line for line in lines if line.strip()).strip()
        if not query:
            raise ValueError("Encountered an empty QD query block.")
        if not query.rstrip().endswith(";"):
            query = f"{query};"
        return query

    def list_queries(self) -> tuple[str, ...]:
        return tuple(sorted(self._queries))

    def get_query(self, section_name: str) -> str:
        query_name = self._normalize_query_name(section_name)
        try:
            return self._queries[query_name]
        except KeyError as exc:
            available = ", ".join(self.list_queries())
            raise KeyError(
                f"Unknown QD query '{section_name}'. Available sections: {available}"
            ) from exc

    def run_query(
        self, section_name: str, params: dict[str, Any] | None = None
    ) -> QueryResult:
        query = self.get_query(section_name)
        connection = get_db_connection()
        if connection is None:
            raise ConnectionError("Could not open a database connection.")

        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params or {})
                    if cursor.description is None:
                        return QueryResult(columns=tuple(), rows=[])
                    columns = tuple(column[0] for column in cursor.description)
                    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    return QueryResult(columns=columns, rows=rows)
        finally:
            connection.close()


def load_qd_queries(queries_path: str | Path | None = None) -> QueryManager:
    """Return a query manager bound to the shared QD query library."""
    return QueryManager(queries_path=queries_path)


def run_qd_query(
    section_name: str, params: dict[str, Any] | None = None
) -> QueryResult:
    """Convenience helper for callers that only need one query execution."""
    return QueryManager().run_query(section_name, params=params)
