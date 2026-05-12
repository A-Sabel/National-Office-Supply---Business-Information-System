"""
backend/customer_service.py
---------------------------
Service layer for all customer-related DB operations.
CustomersView delegates to this instead of calling psycopg2 directly.
"""

import psycopg2
from decimal import Decimal

from backend.audit_logger import write_audit_log
from backend.session_manager import SessionManager


class CustomerService:
    """
    Encapsulates all DB operations for the `customers` table.

    Methods
    -------
    get_all()               → list of customer row-tuples (with computed tier)
    get_by_id(cust_id)      → single dict or None
    create(...)             → new customer_number (int)
    update(cust_id, ...)    → None  (raises on error)
    update_balance(cust_id, delta) → new balance (Decimal)
    delete(cust_id)         → None  (soft-delete: is_active = FALSE)
    """

    # SQL shared across get_all / search
    _SELECT_COLS = """
        SELECT
            customer_number,
            company_name,
            customer_name,
            phone_number,
            address,
            current_balance,
            is_active,
            CASE
                WHEN current_balance >= 10000 THEN 'Gold'
                WHEN current_balance >= 5000  THEN 'Silver'
                WHEN current_balance >= 1000  THEN 'Bronze'
                ELSE ''
            END AS balance_tier
        FROM customers
    """

    def __init__(self, db_config: dict, session_manager: SessionManager | None = None):
        self._cfg = db_config
        self._session_manager = session_manager

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self):
        return psycopg2.connect(**self._cfg)

    def _exec(self, sql: str, params=(), fetch: str = "none"):
        """
        Run a single statement.
        fetch: 'one' | 'all' | 'none'
        Returns fetched rows / None.
        Commits automatically for INSERT/UPDATE/DELETE.
        """
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

    def _ensure_active_session(self) -> None:
        if self._session_manager is not None:
            self._session_manager.ensure_active()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_all(self) -> list:
        """
        Return all customers ordered by company name, then customer name.
        Each row: (customer_number, company_name, customer_name,
                   phone_number, address, current_balance,
                   is_active, balance_tier)
        """
        sql = self._SELECT_COLS + " ORDER BY company_name, customer_name;"
        return self._exec(sql, fetch="all") or []

    def search(self, term: str) -> list:
        """
        Search by customer_number (exact int match) or
        company_name / customer_name (case-insensitive LIKE).
        Returns same row shape as get_all().
        """
        try:
            cust_id = int(term)
        except (ValueError, TypeError):
            cust_id = None

        if cust_id is not None:
            sql = (
                self._SELECT_COLS + " WHERE customer_number = %s ORDER BY company_name;"
            )
            return self._exec(sql, (cust_id,), fetch="all") or []

        like = f"%{term}%"
        sql = (
            self._SELECT_COLS
            + " WHERE company_name ILIKE %s OR customer_name ILIKE %s ORDER BY company_name;"
        )
        return self._exec(sql, (like, like), fetch="all") or []

    def get_by_id(self, cust_id: int) -> dict | None:
        """
        Return a single customer as a dict, or None if not found.
        Dict keys: customer_number, company_name, customer_name,
                   phone_number, address, current_balance, is_active
        """
        sql = """
            SELECT customer_number, company_name, customer_name,
                   phone_number, address, current_balance, is_active
            FROM customers
            WHERE customer_number = %s;
        """
        row = self._exec(sql, (cust_id,), fetch="one")
        if row is None:
            return None
        keys = [
            "customer_number",
            "company_name",
            "customer_name",
            "phone_number",
            "address",
            "current_balance",
            "is_active",
        ]
        return dict(zip(keys, row))

    def create(
        self,
        company_name: str,
        customer_name: str,
        phone_number: str,
        address: str,
        opening_balance: Decimal = Decimal("0.00"),
    ) -> int:
        """
        Insert a new customer row.
        Uses MAX(customer_number)+1 for the ID (no sequence dependency).
        Returns the new customer_number.
        """
        self._ensure_active_session()
        sql = """
            INSERT INTO customers (
                customer_number, company_name, customer_name,
                phone_number, address, current_balance
            )
            VALUES (
                (SELECT COALESCE(MAX(customer_number), 0) + 1 FROM customers),
                %s, %s, %s, %s, %s
            )
            RETURNING customer_number;
        """
        row = self._exec(
            sql,
            (company_name, customer_name, phone_number, address, opening_balance),
            fetch="one",
        )
        if row is None:
            raise RuntimeError("INSERT did not return a customer_number.")
        return row[0]

    def update(
        self,
        cust_id: int,
        company_name: str,
        customer_name: str,
        phone_number: str,
        address: str,
        current_balance: Decimal,
        is_active: bool,
    ) -> None:
        """
        Update all editable fields for an existing customer.
        Raises on DB error.
        """
        self._ensure_active_session()
        sql = """
            UPDATE customers
            SET company_name     = %s,
                customer_name    = %s,
                phone_number     = %s,
                address          = %s,
                current_balance  = %s,
                is_active        = %s
            WHERE customer_number = %s;
        """
        self._exec(
            sql,
            (
                company_name,
                customer_name,
                phone_number,
                address,
                current_balance,
                is_active,
                cust_id,
            ),
        )

    def update_balance(self, cust_id: int, delta: Decimal) -> Decimal:
        """
        Adjust a customer's current_balance by `delta`.
        Pass a negative delta to decrease (e.g. after a payment).
        Pass a positive delta to increase (e.g. after a new invoice is shipped).
        Returns the new balance.
        Raises RuntimeError if the customer is not found.
        """
        self._ensure_active_session()
        sql = """
            UPDATE customers
            SET current_balance = current_balance + %s
            WHERE customer_number = %s
            RETURNING current_balance;
        """
        conn = self._connect()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT current_balance
                        FROM customers
                        WHERE customer_number = %s
                        FOR UPDATE;
                        """,
                        (cust_id,),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise RuntimeError(f"Customer {cust_id} not found.")
                    old_balance = row[0] or Decimal("0.00")

                    cur.execute(sql, (delta, cust_id))
                    new_row = cur.fetchone()
                    if new_row is None:
                        raise RuntimeError(f"Customer {cust_id} not found.")

                    write_audit_log(
                        conn,
                        self._session_manager,
                        "BALANCE_UPDATE",
                        "Customers",
                        cust_id,
                        {
                            "old_balance": old_balance,
                            "new_balance": new_row[0],
                            "reason": "customer service balance adjustment",
                            "delta": delta,
                        },
                    )
                    return new_row[0]
        finally:
            conn.close()

    def delete(self, cust_id: int) -> None:
        """
        Soft-delete: sets is_active = FALSE.
        Does NOT physically delete the row (preserves invoice history).
        Raises RuntimeError if the customer has un-voided / unpaid invoices.
        """
        self._ensure_active_session()
        # Guard: block deactivation if there are open invoices
        check_sql = """
            SELECT COUNT(*) FROM invoices
            WHERE customer_number = %s
              AND status NOT IN ('void', 'paid');
        """
        row = self._exec(check_sql, (cust_id,), fetch="one")
        active_invoices = row[0] if row else 0
        if active_invoices > 0:
            raise RuntimeError(
                f"Customer has {active_invoices} active invoice(s). "
                "Settle all invoices before deactivating."
            )

        sql = "UPDATE customers SET is_active = FALSE WHERE customer_number = %s;"
        self._exec(sql, (cust_id,))
