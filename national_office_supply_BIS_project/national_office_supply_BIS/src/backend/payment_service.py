"""
backend/payment_service.py
--------------------------
Service layer for customer payment operations.

Methods
-------
record_payment(cust_id, amount, method, invoice_id=None) → payment_id (int)
get_customer_payments(cust_id, limit=100)                → list of dicts
mark_invoice_paid(invoice_id)                            → None
update_balance(cust_id, delta)                           → new balance (Decimal)
"""

import psycopg2
from decimal import Decimal


class PaymentService:
    """
    Encapsulates all DB operations for `customer_payments`
    and the balance side-effects on the `customers` table.
    """

    def __init__(self, db_config: dict):
        self._cfg = db_config

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self):
        return psycopg2.connect(**self._cfg)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_payment(
        self,
        cust_id: int,
        amount: Decimal,
        method: str,
        invoice_id: int | None = None,
    ) -> int:
        """
        Insert a row into customer_payments and decrement current_balance.
        This is the single authoritative place for recording a payment.

        Parameters
        ----------
        cust_id    : customer_number FK
        amount     : positive Decimal amount paid
        method     : 'cash' | 'check' | 'transfer'  (matches DB CHECK constraint)
        invoice_id : optional FK to invoices.invoice_id;
                     None → general account credit

        Returns
        -------
        The new payment_id (int).

        Raises
        ------
        ValueError  – invalid method or non-positive amount
        RuntimeError – customer not found in DB
        """
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")
        method = method.strip().lower()
        if method not in ("cash", "check", "transfer"):
            raise ValueError(f"Invalid payment method: '{method}'. Must be cash, check, or transfer.")

        conn = self._connect()
        try:
            cur = conn.cursor()

            # 1. Insert payment record
            cur.execute(
                """
                INSERT INTO customer_payments (
                    customer_number,
                    invoice_id,
                    payment_date,
                    amount_paid,
                    payment_method
                )
                VALUES (%s, %s, CURRENT_DATE, %s, %s)
                RETURNING payment_id;
                """,
                (cust_id, invoice_id, amount, method),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("INSERT into customer_payments did not return a payment_id.")
            payment_id = row[0]

            # 2. Decrement customer balance
            cur.execute(
                """
                UPDATE customers
                SET current_balance = current_balance - %s
                WHERE customer_number = %s
                RETURNING current_balance;
                """,
                (amount, cust_id),
            )
            if cur.fetchone() is None:
                raise RuntimeError(f"Customer {cust_id} not found.")

            conn.commit()
            cur.close()
            return payment_id

        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_customer_payments(self, cust_id: int, limit: int = 100) -> list:
        """
        Return a list of payment dicts for the given customer,
        ordered most-recent first.

        Each dict has keys:
            payment_id, payment_date, amount_paid,
            payment_method, invoice_ref
        where invoice_ref is the invoice_id as a string or 'General Credit'.
        """
        sql = """
            SELECT
                payment_id,
                payment_date,
                amount_paid,
                payment_method,
                COALESCE(invoice_id::text, 'General Credit') AS invoice_ref
            FROM customer_payments
            WHERE customer_number = %s
            ORDER BY payment_date DESC, payment_id DESC
            LIMIT %s;
        """
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (cust_id, limit))
            rows = cur.fetchall()
            cur.close()
        finally:
            conn.close()

        keys = ["payment_id", "payment_date", "amount_paid", "payment_method", "invoice_ref"]
        return [dict(zip(keys, row)) for row in rows]

    def mark_invoice_paid(self, invoice_id: int) -> None:
        """
        Set invoices.status = 'paid' for the given invoice_id.
        Typically called after cumulative payments >= invoice total_amount.
        """
        sql = """
            UPDATE invoices
            SET status = 'paid'
            WHERE invoice_id = %s;
        """
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (invoice_id,))
            conn.commit()
            cur.close()
        finally:
            conn.close()

    def update_balance(self, cust_id: int, delta: Decimal) -> Decimal:
        """
        Directly adjust current_balance by `delta` (positive or negative).
        Useful for cases where balance changes come from a source other
        than a payment record (e.g. invoice shipped → balance increases).

        Returns the new balance.
        Raises RuntimeError if the customer is not found.
        """
        sql = """
            UPDATE customers
            SET current_balance = current_balance + %s
            WHERE customer_number = %s
            RETURNING current_balance;
        """
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (delta, cust_id))
            row = cur.fetchone()
            if row is None:
                raise RuntimeError(f"Customer {cust_id} not found.")
            conn.commit()
            cur.close()
            return row[0]
        finally:
            conn.close()