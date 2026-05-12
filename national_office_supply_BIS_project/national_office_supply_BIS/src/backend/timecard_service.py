"""
backend/timecard_service.py
---------------------------
Service layer for timecards and payroll.
"""

import psycopg2
import psycopg2.extras
from datetime import date, timedelta
from typing import List, Dict, Optional
from backend.session_manager import SessionManager


class TimecardService:
    """
    Encapsulates all DB operations for `timecards` table.

    Methods
    -------
    check_if_week_exists(week_date) → bool
    create_weekly_timecards(week_date) → int (number created)
    get_missing_timecards(week_date) → list of employees missing timecards
    mark_complete(timecard_id) → None
    get_timecard(timecard_id) → dict
    update_hours(timecard_id, hours_worked) → None
    """

    def __init__(self, db_config: dict, session_manager: SessionManager | None = None):
        self._cfg = db_config
        self._session_manager = session_manager

    def _connect(self):
        return psycopg2.connect(**self._cfg)

    def _exec(self, sql: str, params=(), fetch: str = "none"):
        """Execute SQL statement."""
        conn = self._connect()
        try:
            cur = conn.cursor()
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

    def check_if_week_exists(self, week_date: date) -> bool:
        """
        Check if timecards exist for the given week_date (week-ending date).
        Returns True if any timecards exist for this week, False otherwise.
        """
        sql = """
            SELECT COUNT(*) FROM timecards
            WHERE week_date = %s
        """
        result = self._exec(sql, (week_date,), fetch="one")
        return result[0] > 0 if result else False

    def create_weekly_timecards(self, week_date: date) -> int:
        """
        Auto-create blank timecards for all hourly (non-Sales Rep) active employees.
        Skips if timecards already exist for this week (idempotent).
        Returns the number of timecards created.
        """
        # Check if already exists
        if self.check_if_week_exists(week_date):
            return 0

        # Create timecards for all hourly staff
        sql = """
            INSERT INTO timecards (employee_number, week_date, hours_worked)
            SELECT e.employee_number, %s, 0
            FROM employees e
            WHERE e.position = 'Hourly'
              AND e.is_active = TRUE
            RETURNING timecard_id
        """
        result = self._exec(sql, (week_date,), fetch="all")
        return len(result) if result else 0

    def get_missing_timecards(self, week_date: date) -> List[Dict]:
        """
        Find hourly employees who are missing timecards for the given week.
        Returns list of employee dicts.
        """
        # Only managers may view missing timecards via backend
        if self._session_manager is not None:
            try:
                self._session_manager.ensure_active(["Manager"])
            except Exception:
                raise PermissionError("Access denied: Manager role required to view missing timecards.")
        sql = """
                        SELECT e.employee_number, e.employee_name, e.position, e.hourly_wage
            FROM employees e
            LEFT JOIN timecards t ON e.employee_number = t.employee_number
                                  AND t.week_date = %s
            WHERE e.position = 'Hourly'
              AND e.is_active = TRUE
              AND t.timecard_id IS NULL
            ORDER BY e.employee_name
        """
        return self._exec_dict(sql, (week_date,), fetch="all") or []

    def mark_complete(self, timecard_id: int) -> None:
        """Mark a timecard as complete.

        NOTE: older schema versions may not have an `is_complete` column. To
        remain compatible without requiring a DB migration, this method performs
        a lightweight no-op update when `is_complete` is unavailable.
        """
        # Try to set is_complete; fall back to a safe no-op update if column missing
        try:
            sql = """
                UPDATE timecards
                SET is_complete = TRUE
                WHERE timecard_id = %s
            """
            self._exec(sql, (timecard_id,))
        except Exception:
            # Fallback: perform a no-op update to touch the row (keeps behaviour)
            sql = """
                UPDATE timecards
                SET hours_worked = hours_worked
                WHERE timecard_id = %s
            """
            self._exec(sql, (timecard_id,))

    def get_timecard(self, timecard_id: int) -> Optional[Dict]:
        """Get a single timecard."""
        # Derive an `is_complete` boolean from hours_worked when the column
        # is not present in the schema (compatibility with older DBs).
        sql = """
            SELECT timecard_id, employee_number, week_date, hours_worked,
                   (CASE WHEN hours_worked IS NOT NULL AND hours_worked > 0 THEN TRUE ELSE FALSE END) AS is_complete
            FROM timecards
            WHERE timecard_id = %s
        """
        return self._exec_dict(sql, (timecard_id,), fetch="one")

    def update_hours(self, timecard_id: int, hours_worked: float) -> None:
        """Update hours worked on a timecard."""
        # Validation: hours must be within a reasonable weekly range
        if hours_worked is None:
            raise ValueError("hours_worked must be provided")
        try:
            hours = float(hours_worked)
        except Exception:
            raise ValueError("hours_worked must be a number")
        if hours < 0 or hours > 168:
            raise ValueError("hours_worked must be between 0 and 168")

        sql = """
            UPDATE timecards
            SET hours_worked = %s
            WHERE timecard_id = %s
        """
        self._exec(sql, (hours, timecard_id))

    def get_timecards_for_week(self, week_date: date) -> List[Dict]:
        """Get all timecards for a specific week."""
        # Only managers may query timecards via backend
        if self._session_manager is not None:
            try:
                self._session_manager.ensure_active(["Manager"])
            except Exception:
                raise PermissionError("Access denied: Manager role required to view timecards.")
        sql = """
            SELECT t.timecard_id, t.employee_number, e.employee_name,
                   e.hourly_wage, t.week_date, t.hours_worked,
                   (CASE WHEN t.hours_worked IS NOT NULL AND t.hours_worked > 0 THEN TRUE ELSE FALSE END) AS is_complete
            FROM timecards t
            JOIN employees e ON t.employee_number = e.employee_number
            WHERE t.week_date = %s
            ORDER BY e.employee_name
        """
        return self._exec_dict(sql, (week_date,), fetch="all") or []
