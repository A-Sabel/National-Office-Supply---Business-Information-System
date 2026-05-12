"""
backend/invoice_service.py
--------------------------
Service layer for invoices and invoice lines.
"""

import psycopg2
import psycopg2.extras
from decimal import Decimal
from datetime import date
from typing import List, Dict, Optional, Tuple
from backend.session_manager import SessionManager
from utils.id_formatter import fmt_invoice


class InvoiceService:
    """
    Encapsulates all DB operations for `invoices` and `invoice_lines` tables.

    Methods
    -------
    create(customer_number, employee_number) → invoice_id
    add_line_item(invoice_id, part_number, quantity) → None
    get_invoice_total(invoice_id) → Decimal
    update_status(invoice_id, new_status) → None
    get_customer_invoices(customer_number) → list of invoices
    get_invoice_details(invoice_id) → dict with lines
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

    def create(
        self,
        customer_number: int,
        employee_number: int,
        total_amount: Decimal | None = None,
    ) -> Optional[int]:
        """
        Create a new invoice for a customer.
        Returns invoice_id or None on error.
        """
        sql = """
            INSERT INTO invoices (customer_number, employee_number, status, total_amount, date_written)
            VALUES (%s, %s, 'active', COALESCE(%s, 0), CURRENT_DATE)
            RETURNING invoice_id
        """
        result = self._exec(
            sql,
            (customer_number, employee_number, total_amount),
            fetch="one",
        )
        return result[0] if result else None

    def add_line_item(self, invoice_id: int, part_number: int, quantity: int) -> None:
        """
        Add a line item to an invoice.
        Calculates line_total from parts.selling_price * quantity.
        """
        sql = """
            INSERT INTO invoice_lines (invoice_id, part_number, quantity, line_total)
            SELECT %s, %s, %s, %s * p.selling_price
            FROM parts p
            WHERE p.part_number = %s
        """
        self._exec(sql, (invoice_id, part_number, quantity, quantity, part_number))

    def get_invoice_total(self, invoice_id: int) -> Decimal:
        """
        Calculate total amount for an invoice (sum of all line items).
        Returns Decimal or 0 if invoice not found.
        """
        sql = """
            SELECT COALESCE(SUM(line_total), 0) as total
            FROM invoice_lines
            WHERE invoice_id = %s
        """
        result = self._exec(sql, (invoice_id,), fetch="one")
        return Decimal(str(result[0])) if result else Decimal("0.00")

    def update_status(self, invoice_id: int, new_status: str) -> None:
        """
        Update invoice status. Valid values: 'active', 'shipped', 'paid', 'void'
        """
        sql = """
            UPDATE invoices
            SET status = %s
            WHERE invoice_id = %s
        """
        self._exec(sql, (new_status, invoice_id))

    def get_customer_invoices(self, customer_number: int) -> List[Dict]:
        """Get all invoices for a customer."""
        sql = """
            SELECT invoice_id, customer_number, employee_number, date_written, 
                   total_amount, status
            FROM invoices
            WHERE customer_number = %s
            ORDER BY date_written DESC
        """
        return self._exec_dict(sql, (customer_number,), fetch="all") or []

    def get_recent_invoices(
        self, status_filter: str | None = None, limit: int = 200
    ) -> List[Dict]:
        """Get recent invoices with customer and employee names for the Orders view."""
        sql = """
            SELECT
                i.invoice_id,
                i.invoice_id::text           AS invoice_number,
                c.customer_name              AS customer_name,
                c.company_name               AS company_name,
                c.customer_number,
                COALESCE(i.total_amount, 0)  AS amount,
                i.status,
                i.date_written::text         AS date,
                e.employee_name              AS sales_rep,
                e.employee_number
            FROM invoices i
            JOIN customers c ON c.customer_number = i.customer_number
            JOIN employees e ON e.employee_number = i.employee_number
        """
        params: list[object] = []
        if status_filter and status_filter.lower() in {
            "active",
            "shipped",
            "paid",
            "void",
        }:
            sql += " WHERE i.status = %s"
            params.append(status_filter.lower())
        sql += " ORDER BY i.date_written DESC, i.invoice_id DESC LIMIT %s"
        params.append(limit)
        rows = self._exec_dict(sql, tuple(params), fetch="all") or []
        for row in rows:
            row["invoice_number"] = fmt_invoice(
                row["invoice_id"], row.get("company_name", "")
            )
        return rows

    def get_invoice_details(self, invoice_id: int) -> Optional[Dict]:
        """Get invoice header with calculated total and line item count."""
        sql = """
            SELECT i.invoice_id, i.customer_number, i.employee_number, i.date_written,
                   i.status, COUNT(il.part_number) as line_count,
                   COALESCE(SUM(il.line_total), 0) as total_amount
            FROM invoices i
            LEFT JOIN invoice_lines il ON i.invoice_id = il.invoice_id
            WHERE i.invoice_id = %s
            GROUP BY i.invoice_id
        """
        return self._exec_dict(sql, (invoice_id,), fetch="one")

    def get_invoice_lines(self, invoice_id: int) -> List[Dict]:
        """Get all line items for an invoice."""
        sql = """
            SELECT il.invoice_id, il.part_number, il.quantity, il.line_total,
                   p.description, p.selling_price
            FROM invoice_lines il
            JOIN parts p ON il.part_number = p.part_number
            WHERE il.invoice_id = %s
            ORDER BY il.part_number
        """
        return self._exec_dict(sql, (invoice_id,), fetch="all") or []
