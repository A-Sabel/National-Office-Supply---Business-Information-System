"""
backend/employee_service.py
---------------------------
Service layer for all employee-related DB operations.
"""

import psycopg2
import psycopg2.extras
from decimal import Decimal
from typing import List, Dict, Optional
from backend.session_manager import SessionManager


class EmployeeService:
    """
    Encapsulates all DB operations for the `employees` table.

    Methods
    -------
    get_all()               → list of employee dicts
    get_by_id(emp_number)   → single employee dict or None
    get_hourly_staff()      → list of hourly employees
    get_active_staff()      → list of active employees
    """

    def __init__(self, db_config: dict, session_manager: SessionManager | None = None):
        self._cfg = db_config
        self._session_manager = session_manager

    def _connect(self):
        return psycopg2.connect(**self._cfg)

    def _exec_dict(self, sql: str, params=(), fetch: str = "none"):
        """Execute SQL and return as list of dicts."""
        conn = self._connect()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, params)
            result = None
            if fetch == "one":
                result = cur.fetchone()
            elif fetch == "all":
                result = cur.fetchall()
            conn.commit()
            cur.close()
            return result
        finally:
            conn.close()

    def get_all(self) -> List[Dict]:
        """Get all employees."""
        sql = """
            SELECT employee_number, employee_name, position, ssn, employee_address,
                   username, is_locked, is_active, hourly_wage, ytdsales, commission_rate
            FROM employees
            ORDER BY employee_number
        """
        return self._exec_dict(sql, fetch="all") or []

    def get_by_id(self, employee_number: int) -> Optional[Dict]:
        """Get a single employee by employee_number."""
        sql = """
            SELECT employee_number, employee_name, position, ssn, employee_address,
                   username, is_locked, is_active, hourly_wage, ytdsales, commission_rate
            FROM employees
            WHERE employee_number = %s
        """
        return self._exec_dict(sql, (employee_number,), fetch="one")

    def get_hourly_staff(self) -> List[Dict]:
        """Get all hourly (wage-based) employees."""
        sql = """
            SELECT employee_number, employee_name, position, hourly_wage, is_active
            FROM employees
            WHERE position = 'Hourly' AND is_active = TRUE
            ORDER BY employee_name
        """
        return self._exec_dict(sql, fetch="all") or []

    def get_active_staff(self) -> List[Dict]:
        """Get all active employees regardless of position."""
        sql = """
            SELECT employee_number, employee_name, position, is_active
            FROM employees
            WHERE is_active = TRUE
            ORDER BY employee_name
        """
        return self._exec_dict(sql, fetch="all") or []

    def get_by_username(self, username: str) -> Optional[Dict]:
        """Get employee by username (for login)."""
        sql = """
            SELECT employee_number, employee_name, position, username, password_hash,
                   is_locked, is_active, hourly_wage, ytdsales, commission_rate
            FROM employees
            WHERE username = %s
        """
        return self._exec_dict(sql, (username,), fetch="one")
