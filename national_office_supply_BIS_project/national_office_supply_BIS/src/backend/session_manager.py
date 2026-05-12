"""Session management helpers for the National Office Supplies BIS.

This module builds on :class:`utils.session.AppSession` and adds the policy
layer needed by the application: role checks, session age tracking, and a
single place to validate whether the current user can keep working.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional

from utils.session import AppSession


@dataclass(frozen=True)
class SessionStatus:
    """Lightweight snapshot of the current session state."""

    authenticated: bool
    expired: bool
    role: Optional[str]
    employee_number: Optional[int]
    employee_name: Optional[str]


class SessionManager:
    """Manage the active application session and enforce basic policy rules."""

    def __init__(self, session: Optional[AppSession] = None, timeout_minutes: int = 30):
        self.session = session or AppSession()
        self.timeout_minutes = timeout_minutes
        self.started_at: Optional[datetime] = None
        self.last_activity_at: Optional[datetime] = None

    def start_session(
        self, employee_number: int, employee_name: str, role: str
    ) -> AppSession:
        """Start a new authenticated session and mark the activity timestamp."""
        self.session.login(employee_number, employee_name, role)
        now = datetime.now()
        self.started_at = now
        self.last_activity_at = now
        return self.session

    def logout(self) -> None:
        """End the current session and clear all tracking data."""
        self.session.logout()
        self.started_at = None
        self.last_activity_at = None

    def touch(self) -> None:
        """Refresh the last-activity timestamp for the active session."""
        if self.session.is_authenticated():
            self.last_activity_at = datetime.now()

    def is_authenticated(self) -> bool:
        return self.session.is_authenticated()

    def is_expired(self) -> bool:
        if not self.is_authenticated() or self.last_activity_at is None:
            return False
        return datetime.now() - self.last_activity_at > timedelta(
            minutes=self.timeout_minutes
        )

    def has_role(self, allowed_roles: Iterable[str]) -> bool:
        """Return True when the active user role is one of the allowed roles."""
        if not self.is_authenticated():
            return False
        return self.session.role in set(allowed_roles)

    def ensure_active(self, allowed_roles: Iterable[str] | None = None) -> None:
        """Raise if the session is missing, expired, or not allowed for the action."""
        if not self.is_authenticated():
            raise PermissionError("No active session found.")
        if self.is_expired():
            self.logout()
            raise PermissionError("Session expired. Please log in again.")
        if allowed_roles is not None and not self.has_role(allowed_roles):
            raise PermissionError(
                f"Access Denied: The role '{self.session.role}' is not authorized to perform this action."
            )

    def get_status(self) -> SessionStatus:
        """Return a frozen snapshot of the active session state."""
        return SessionStatus(
            authenticated=self.is_authenticated(),
            expired=self.is_expired(),
            role=self.session.role,
            employee_number=self.session.employee_number,
            employee_name=self.session.employee_name,
        )

    # ---- RBAC Helper Methods ----

    def is_manager(self) -> bool:
        """Check if current user is a Manager."""
        return self.has_role(["Manager"])

    def is_sales_rep(self) -> bool:
        """Check if current user is a Sales Rep."""
        return self.has_role(["Sales Rep"])

    def is_hourly(self) -> bool:
        """Check if current user is Hourly staff."""
        return self.has_role(["Hourly"])

    def can_edit_payroll(self) -> bool:
        """Only Managers can edit payroll."""
        return self.is_manager()

    def can_edit_prices(self) -> bool:
        """Only Managers can edit part prices."""
        return self.is_manager()

    def can_create_invoices(self) -> bool:
        """Sales Reps and Managers can create invoices."""
        return self.has_role(["Sales Rep", "Manager"])

    def can_view_timecards(self) -> bool:
        """Only Managers can view timecards."""
        return self.is_manager()

    def get_session_age_minutes(self) -> int:
        """Get the age of the session in minutes."""
        if self.started_at is None:
            return 0
        return int((datetime.now() - self.started_at).total_seconds() / 60)

    def get_inactivity_minutes(self) -> int:
        """Get minutes since last activity."""
        if self.last_activity_at is None:
            return 0
        return int((datetime.now() - self.last_activity_at).total_seconds() / 60)

    def get_remaining_minutes(self) -> int:
        """Get minutes until session timeout."""
        inactivity = self.get_inactivity_minutes()
        remaining = self.timeout_minutes - inactivity
        return max(0, remaining)
