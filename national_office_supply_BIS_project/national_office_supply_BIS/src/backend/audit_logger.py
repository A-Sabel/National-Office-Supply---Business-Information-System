"""Shared audit logging helpers for sensitive business actions."""

from __future__ import annotations

import json
from typing import Any


def ensure_audit_log_table(conn) -> None:
    """Create the logs table if it does not already exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                log_id SERIAL PRIMARY KEY,
                actor_id INTEGER,
                action_type VARCHAR(50) NOT NULL,
                target_table VARCHAR(50) NOT NULL,
                target_id INTEGER,
                timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
                details TEXT
            )
            """)


def _serialize_details(details: Any) -> str:
    if details is None:
        return ""
    if isinstance(details, str):
        return details
    try:
        return json.dumps(details, default=str, ensure_ascii=True)
    except Exception:
        return str(details)


def write_audit_log(
    conn,
    session_manager,
    action_type: str,
    target_table: str,
    target_id: int | None,
    details: Any,
) -> None:
    """Insert a single audit record using the active session identity."""
    if session_manager is None:
        return

    status = session_manager.get_status()
    actor_id = status.employee_number
    if actor_id is None:
        return

    ensure_audit_log_table(conn)
    payload = _serialize_details(details)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO logs (
                actor_id,
                action_type,
                target_table,
                target_id,
                timestamp,
                details
            )
            VALUES (%s, %s, %s, %s, NOW(), %s)
            """,
            (actor_id, action_type, target_table, target_id, payload),
        )
