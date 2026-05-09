"""Helpers for loading and running named QD queries and executing restricted transactions.

The read-only queries live in ``src/database/queries.sql`` and are grouped by comment
headers such as ``-- QD-Sec1: ...``. Transactional writes are hardcoded as methods
and protected by RBAC decorators.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from backend.database import get_db_connection
from utils.auth_guard import require_role

# Assuming AppSession is in utils.session
from utils.session import AppSession 

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
    """Load and execute named QD queries and handle secure DB transactions."""

    def __init__(self, session: AppSession, queries_path: str | Path | None = None) -> None:
        # INJECT THE SESSION: This is the core of backend RBAC
        self.session = session
        
        self.queries_path = (
            Path(queries_path) if queries_path else self._default_queries_path()
        )
        self._queries = self._load_queries(self.queries_path)

    @staticmethod
    def _default_queries_path() -> Path:
        # Adjusted path resolution to be safer depending on execution context
        return Path(__file__).resolve().parent.parent / "database" / "queries.sql"

    @staticmethod
    def _normalize_query_name(name: str) -> str:
        return name.strip().upper()

    def _load_queries(self, path: Path) -> dict[str, str]:
        if not path.exists():
            print(f"[WARNING] Query library not found at: {path}")
            return {}

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

    # ==========================================
    # 1. READ OPERATIONS (QD-SEC)
    # ==========================================

    def run_query(self, section_name: str, params: dict[str, Any] | None = None) -> QueryResult:
        """Executes a parsed QD-Sec query. Open to all logged-in users (UI handles tab hiding)."""
        query = self.get_query(section_name)
        return self._execute_sql(query, params)

    # ==========================================
    # 2. RESTRICTED WRITE OPERATIONS (Phase 2)
    # ==========================================

    @require_role(["Manager"])
    def update_part_price(self, part_number: int, new_price: float) -> QueryResult:
        """Only Managers can update inventory pricing."""
        print(f"[AUDIT] Manager {self.session.employee_name} updating price for part {part_number}")
        query = "UPDATE parts SET selling_price = %(price)s WHERE part_number = %(part)s RETURNING part_number;"
        return self._execute_sql(query, {"price": new_price, "part": part_number})

    @require_role(["Manager"])
    def generate_weekly_timecards(self, week_date: str) -> QueryResult:
        """Only Managers can trigger payroll generation."""
        # Add actual insert logic for timecards here
        print(f"[AUDIT] Manager {self.session.employee_name} generating timecards for {week_date}")
        return QueryResult(columns=tuple(), rows=[])

    @require_role(["Manager", "Sales Rep"])
    def create_invoice(self, customer_number: int) -> QueryResult:
        """Managers and Reps can create orders. Hourly staff cannot."""
        query = "INSERT INTO invoices (customer_number, employee_number) VALUES (%(cust)s, %(emp)s) RETURNING invoice_id;"
        return self._execute_sql(query, {"cust": customer_number, "emp": self.session.employee_number})

    # ==========================================
    # INTERNAL DB EXECUTOR
    # ==========================================

    def _execute_sql(self, query: str, params: dict[str, Any] | None = None) -> QueryResult:
        connection = get_db_connection()
        if connection is None:
            raise ConnectionError("Could not open a database connection.")

        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params or {})
                    # If it's an INSERT/UPDATE without RETURNING, description is None
                    if cursor.description is None:
                        return QueryResult(columns=tuple(), rows=[])
                    
                    columns = tuple(column[0] for column in cursor.description)
                    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    return QueryResult(columns=columns, rows=rows)
        finally:
            connection.close()