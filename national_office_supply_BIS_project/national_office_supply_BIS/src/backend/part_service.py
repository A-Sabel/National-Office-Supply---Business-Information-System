"""
backend/part_service.py
-----------------------
Service layer for all part/inventory-related DB operations.
"""

import psycopg2
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
from backend.audit_logger import write_audit_log
from backend.session_manager import SessionManager


class PartService:
    """
    Encapsulates all DB operations for the `parts` table.

    Methods
    -------
    get_all()                               → list of part dicts
    get_by_id(part_number)                  → single part dict or None
    create(description, selling_price, trigger_amount, restock_value) → part_number (int)
    update(part_number, ...)                → None
    get_low_stock()                         → list of low-stock parts
    update_stock(part_number, quantity_delta) → new stock_count
    get_supplier_cost(part_number, supplier_id) → Decimal or None
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
        import psycopg2.extras

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
        """Get all parts with their details."""
        sql = """
            SELECT part_number, description, selling_price, stock_count,
                   trigger_amount, restock_value, on_order
            FROM parts
            ORDER BY part_number
        """
        return self._exec_dict(sql, fetch="all") or []

    def get_by_id(self, part_number: int) -> Optional[Dict]:
        """Get a single part by part_number."""
        sql = """
            SELECT part_number, description, selling_price, stock_count,
                   trigger_amount, restock_value, on_order
            FROM parts
            WHERE part_number = %s
        """
        return self._exec_dict(sql, (part_number,), fetch="one")

    def create(
        self,
        description: str,
        selling_price: Decimal,
        trigger_amount: int,
        restock_value: int,
    ) -> Optional[int]:
        """Create a new part. Returns part_number or None on error."""
        sql = """
            INSERT INTO parts (description, selling_price, trigger_amount, restock_value)
            VALUES (%s, %s, %s, %s)
            RETURNING part_number
        """
        result = self._exec(
            sql,
            (description, selling_price, trigger_amount, restock_value),
            fetch="one",
        )
        return result[0] if result else None

    def update(
        self,
        part_number: int,
        description: Optional[str] = None,
        selling_price: Optional[Decimal] = None,
        trigger_amount: Optional[int] = None,
        restock_value: Optional[int] = None,
        stock_count: Optional[int] = None,
    ) -> None:
        """Update part details. Only updates provided fields."""
        # Enforce role-based permission for price changes
        if selling_price is not None and self._session_manager is not None:
            try:
                if not self._session_manager.can_edit_prices():
                    raise PermissionError("Only Managers may update part prices.")
            except AttributeError:
                # If session manager doesn't implement can_edit_prices, fall back
                pass
        updates = []
        params = []

        if description is not None:
            updates.append("description = %s")
            params.append(description)
        if selling_price is not None:
            updates.append("selling_price = %s")
            params.append(selling_price)
        if stock_count is not None:
            updates.append("stock_count = %s")
            params.append(stock_count)
        if trigger_amount is not None:
            updates.append("trigger_amount = %s")
            params.append(trigger_amount)
        if restock_value is not None:
            updates.append("restock_value = %s")
            params.append(restock_value)

        if not updates:
            return

        conn = self._connect()
        try:
            with conn:
                with conn.cursor() as cur:
                    old_price = None
                    if selling_price is not None:
                        cur.execute(
                            "SELECT selling_price FROM parts WHERE part_number = %s FOR UPDATE",
                            (part_number,),
                        )
                        row = cur.fetchone()
                        old_price = row[0] if row else None

                    params.append(part_number)
                    sql = (
                        f"UPDATE parts SET {', '.join(updates)} WHERE part_number = %s"
                    )
                    cur.execute(sql, params)

                    if selling_price is not None and old_price is not None:
                        write_audit_log(
                            conn,
                            self._session_manager,
                            "PRICE_UPDATE",
                            "Parts",
                            part_number,
                            {
                                "old_price": old_price,
                                "new_price": selling_price,
                            },
                        )
        finally:
            conn.close()

    def get_low_stock(self) -> List[Dict]:
        """Get all parts where stock_count <= trigger_amount."""
        sql = """
            SELECT part_number, description, stock_count, trigger_amount, on_order
            FROM parts
            WHERE stock_count <= trigger_amount
            ORDER BY stock_count ASC
        """
        return self._exec_dict(sql, fetch="all") or []

    def update_stock(self, part_number: int, quantity_delta: int) -> Optional[int]:
        """
        Increment/decrement stock by quantity_delta.
        Returns new stock_count or None on error.
        """
        sql = """
            UPDATE parts
            SET stock_count = stock_count + %s
            WHERE part_number = %s
            RETURNING stock_count
        """
        result = self._exec(sql, (quantity_delta, part_number), fetch="one")
        return result[0] if result else None

    def get_supplier_cost(
        self, part_number: int, supplier_id: int
    ) -> Optional[Decimal]:
        """
        Get the cost a specific supplier charges for this part.
        Returns Decimal or None if not found.
        """
        sql = """
            SELECT cost FROM item_parts
            WHERE part_number = %s AND supplier_id = %s
        """
        result = self._exec(sql, (part_number, supplier_id), fetch="one")
        return Decimal(str(result[0])) if result else None
