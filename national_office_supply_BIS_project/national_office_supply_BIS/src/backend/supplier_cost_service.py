"""
backend/supplier_cost_service.py
--------------------------------
Service layer for supplier cost analysis and procurement optimization.
"""

import psycopg2
import psycopg2.extras
from decimal import Decimal
from typing import List, Dict, Optional
from backend.session_manager import SessionManager


class SupplierCostService:
    """
    Encapsulates all DB operations for supplier cost analysis.

    Methods
    -------
    get_lowest_cost_supplier(part_number) → dict with supplier_id, supplier_name, cost
    get_all_costs_for_part(part_number) → list of suppliers and costs (sorted by cost)
    get_suppliers_by_part(part_number) → list of supplier details
    get_parts_by_supplier(supplier_id) → list of parts this supplier provides
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

    def get_lowest_cost_supplier(self, part_number: int) -> Optional[Dict]:
        """
        Get the supplier with the lowest cost for a given part.
        Returns dict with supplier_id, supplier_name, company_name, cost.
        Returns None if no suppliers found.
        """
        sql = """
            SELECT 
                s.supplier_id,
                s.company_name,
                s.phone_number,
                s.address,
                ip.cost
            FROM item_parts ip
            JOIN suppliers s ON ip.supplier_id = s.supplier_id
            WHERE ip.part_number = %s
            ORDER BY ip.cost ASC
            LIMIT 1
        """
        return self._exec_dict(sql, (part_number,), fetch="one")

    def get_all_costs_for_part(self, part_number: int) -> List[Dict]:
        """
        Get all suppliers for a part, sorted by cost (lowest first).
        Returns list of dicts with supplier_id, company_name, cost.
        """
        sql = """
            SELECT 
                s.supplier_id,
                s.company_name,
                s.phone_number,
                s.address,
                ip.cost
            FROM item_parts ip
            JOIN suppliers s ON ip.supplier_id = s.supplier_id
            WHERE ip.part_number = %s
            ORDER BY ip.cost ASC
        """
        return self._exec_dict(sql, (part_number,), fetch="all") or []

    def get_suppliers_by_part(self, part_number: int) -> List[Dict]:
        """
        Get detailed supplier info for a part.
        Returns list of suppliers with cost, contact info.
        """
        sql = """
            SELECT 
                s.supplier_id,
                s.company_name,
                s.phone_number,
                s.address,
                ip.cost,
                COUNT(DISTINCT ip.part_number) OVER (PARTITION BY s.supplier_id) 
                    as total_parts_from_supplier
            FROM item_parts ip
            JOIN suppliers s ON ip.supplier_id = s.supplier_id
            WHERE ip.part_number = %s
            ORDER BY ip.cost ASC
        """
        return self._exec_dict(sql, (part_number,), fetch="all") or []

    def get_parts_by_supplier(self, supplier_id: int) -> List[Dict]:
        """
        Get all parts supplied by a specific supplier.
        Returns list of parts with their costs from this supplier.
        """
        sql = """
            SELECT 
                p.part_number,
                p.description,
                p.selling_price,
                p.stock_count,
                ip.cost,
                (p.selling_price - ip.cost) as margin
            FROM item_parts ip
            JOIN parts p ON ip.part_number = p.part_number
            WHERE ip.supplier_id = %s
            ORDER BY p.part_number
        """
        return self._exec_dict(sql, (supplier_id,), fetch="all") or []

    def get_best_price_procurement(self) -> List[Dict]:
        """
        Get the lowest-cost supplier for each part.
        Useful for procurement recommendations.
        Returns list of parts with their recommended supplier and cost.
        """
        sql = """
            WITH ranked_suppliers AS (
                SELECT 
                    ip.part_number,
                    s.supplier_id,
                    s.company_name,
                    ip.cost,
                    ROW_NUMBER() OVER (PARTITION BY ip.part_number ORDER BY ip.cost ASC)
                        as cost_rank
                FROM item_parts ip
                JOIN suppliers s ON ip.supplier_id = s.supplier_id
            )
            SELECT 
                rs.part_number,
                p.description,
                p.selling_price,
                rs.supplier_id,
                rs.company_name,
                rs.cost,
                (p.selling_price - rs.cost) as margin_per_unit
            FROM ranked_suppliers rs
            JOIN parts p ON rs.part_number = p.part_number
            WHERE rs.cost_rank = 1
            ORDER BY rs.part_number
        """
        return self._exec_dict(sql, fetch="all") or []

    def get_supplier_spending_summary(
        self, week_start: Optional[str] = None
    ) -> List[Dict]:
        """
        Get total spending by supplier (optionally filtered by date range).
        Returns list of suppliers with total amount spent.
        """
        sql = """
            SELECT 
                s.supplier_id,
                s.company_name,
                COUNT(DISTINCT po.po_number) as total_orders,
                SUM(po.quantity_ordered * ip.cost) as total_spent
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.supplier_id
            JOIN item_parts ip ON po.part_number = ip.part_number 
                              AND po.supplier_id = ip.supplier_id
            GROUP BY s.supplier_id, s.company_name
            ORDER BY total_spent DESC
        """
        return self._exec_dict(sql, fetch="all") or []
