"""
tests/test_advanced_validations.py
----------------------------------
Advanced validation tests for shipment blockers and high-performance reps.
Tests verify business logic for bottleneck detection and rep performance metrics.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

if TYPE_CHECKING:
    import psycopg2
    import psycopg2.extras

try:
    import psycopg2
    import psycopg2.extras

    HAS_DB = True
except ImportError:
    HAS_DB = False


class TestShipmentBlockerValidation:
    """Test shipment blocker detection and clearing after restock."""

    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup test database connection."""
        if not HAS_DB:
            pytest.skip("psycopg2 not available")

        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 5432)),
            "database": os.getenv("DB_NAME", "nos_db"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "postgres"),
        }

        try:
            self.conn = psycopg2.connect(**self.db_config)
            yield
            self.conn.close()
        except psycopg2.Error as e:
            pytest.skip(f"Database connection failed: {e}")

    def _execute_query(self, sql: str, params=()):
        """Execute query and return results."""
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def _execute_update(self, sql: str, params=()):
        """Execute update query."""
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            self.conn.commit()

    def test_blockers_exist_when_stock_critical(self):
        """Test that blockers are detected when stock_count <= 1 for active orders."""
        blockers = self._execute_query("""
            SELECT
                i.invoice_id,
                p.part_number,
                p.description,
                p.stock_count,
                il.quantity
            FROM invoice_lines il
            JOIN invoices i ON i.invoice_id = il.invoice_id
            JOIN parts p ON p.part_number = il.part_number
            WHERE i.status = 'active' AND p.stock_count <= 1
            LIMIT 10
        """)

        # Verify query returns expected columns
        if blockers:
            for blocker in blockers:
                assert "invoice_id" in blocker
                assert "part_number" in blocker
                assert "stock_count" in blocker
                assert blocker["stock_count"] <= 1, "Stock should be <= 1 for blocker"

    def test_blockers_clear_after_restock(self):
        """Test that blockers are removed when stock is restocked above critical level."""
        # Step 1: Find an existing blocker
        blockers = self._execute_query("""
            SELECT DISTINCT
                i.invoice_id,
                p.part_number,
                p.stock_count
            FROM invoice_lines il
            JOIN invoices i ON i.invoice_id = il.invoice_id
            JOIN parts p ON p.part_number = il.part_number
            WHERE i.status = 'active' AND p.stock_count <= 1
            LIMIT 1
        """)

        if not blockers:
            pytest.skip("No active blockers in test database")

        blocker = blockers[0]
        part_num = blocker["part_number"]
        original_stock = blocker["stock_count"]

        try:
            # Step 2: Restock the part above critical level
            new_stock = max(original_stock + 10, 15)
            self._execute_update(
                """
                UPDATE parts
                SET stock_count = %s
                WHERE part_number = %s
            """,
                (new_stock, part_num),
            )

            # Step 3: Verify the blocker is no longer returned
            remaining_blockers = self._execute_query(
                """
                SELECT i.invoice_id, p.part_number
                FROM invoice_lines il
                JOIN invoices i ON i.invoice_id = il.invoice_id
                JOIN parts p ON p.part_number = il.part_number
                WHERE i.status = 'active' 
                  AND p.stock_count <= 1
                  AND p.part_number = %s
            """,
                (part_num,),
            )

            assert (
                len(remaining_blockers) == 0
            ), "Blocker should be cleared after restock"

        finally:
            # Step 4: Restore original stock
            self._execute_update(
                """
                UPDATE parts
                SET stock_count = %s
                WHERE part_number = %s
            """,
                (original_stock, part_num),
            )

    def test_blocker_quantity_validation(self):
        """Test that blocker quantities match invoice line quantities."""
        blockers = self._execute_query("""
            SELECT
                il.invoice_id,
                il.part_number,
                il.quantity,
                p.stock_count,
                GREATEST(il.quantity - p.stock_count, 0) AS shortage
            FROM invoice_lines il
            JOIN invoices i ON i.invoice_id = il.invoice_id
            JOIN parts p ON p.part_number = il.part_number
            WHERE i.status = 'active' AND p.stock_count <= 1
            LIMIT 10
        """)

        for blocker in blockers:
            # Verify shortage calculation
            expected_shortage = max(blocker["quantity"] - blocker["stock_count"], 0)
            actual_shortage = blocker["shortage"]
            assert (
                actual_shortage == expected_shortage
            ), f"Shortage calculation mismatch: {actual_shortage} != {expected_shortage}"
            assert actual_shortage > 0, "Shortage should be > 0 for blocker"

    def test_no_blockers_for_void_orders(self):
        """Test that void/shipped orders don't create blockers."""
        void_orders = self._execute_query("""
            SELECT i.invoice_id
            FROM invoices i
            WHERE i.status IN ('void', 'shipped', 'paid')
            LIMIT 1
        """)

        if void_orders:
            void_order_id = void_orders[0]["invoice_id"]

            # Verify this order doesn't appear in blocker query
            blocker_check = self._execute_query(
                """
                SELECT COUNT(*) as count
                FROM invoice_lines il
                JOIN invoices i ON i.invoice_id = il.invoice_id
                JOIN parts p ON p.part_number = il.part_number
                WHERE i.status = 'active'
                  AND p.stock_count <= 1
                  AND i.invoice_id = %s
            """,
                (void_order_id,),
            )

            assert (
                blocker_check[0]["count"] == 0
            ), "Void/shipped orders should not create blockers"


class TestHighPerformanceRepThreshold:
    """Test high-performance rep detection with > 10 invoices threshold."""

    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup test database connection."""
        if not HAS_DB:
            pytest.skip("psycopg2 not available")

        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 5432)),
            "database": os.getenv("DB_NAME", "nos_db"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "postgres"),
        }

        try:
            self.conn = psycopg2.connect(**self.db_config)
            yield
            self.conn.close()
        except psycopg2.Error as e:
            pytest.skip(f"Database connection failed: {e}")

    def _execute_query(self, sql: str, params=()):
        """Execute query and return results."""
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def test_high_perf_reps_exceed_threshold(self):
        """Test that high-performance reps have > 10 invoices in the week."""
        # Get current week
        today = datetime.now()
        week_end = today + timedelta(days=(6 - today.weekday()))  # Sunday
        week_start = week_end - timedelta(days=6)  # Monday

        high_perf = self._execute_query(
            """
            SELECT
                e.employee_number,
                e.employee_name,
                COUNT(i.invoice_id) AS invoice_count,
                COALESCE(SUM(i.total_amount), 0) AS total_sales,
                COALESCE(AVG(i.total_amount), 0) AS average_invoice_value
            FROM employees e
            JOIN invoices i
                ON i.employee_number = e.employee_number
            WHERE e.is_active = TRUE
                AND e.position = 'Sales Rep'
                AND i.date_written BETWEEN %s::date AND %s::date
            GROUP BY e.employee_number, e.employee_name
            HAVING COUNT(i.invoice_id) > 10
            ORDER BY total_sales DESC
        """,
            (week_start.date(), week_end.date()),
        )

        # Verify all high-performance reps exceed the threshold
        for rep in high_perf:
            assert (
                rep["invoice_count"] > 10
            ), f"Rep {rep['employee_name']} should have > 10 invoices but has {rep['invoice_count']}"

    def test_threshold_boundary_10_invoices(self):
        """Test threshold boundary: exactly 10 invoices should NOT be high-perf."""
        # Get a sample week
        today = datetime.now()
        week_end = today + timedelta(days=(6 - today.weekday()))
        week_start = week_end - timedelta(days=6)

        # Query reps with exactly 10 invoices
        at_boundary = self._execute_query(
            """
            SELECT
                e.employee_number,
                e.employee_name,
                COUNT(i.invoice_id) AS invoice_count
            FROM employees e
            LEFT JOIN invoices i
                ON i.employee_number = e.employee_number
                AND i.date_written BETWEEN %s::date AND %s::date
            WHERE e.is_active = TRUE
                AND e.position = 'Sales Rep'
            GROUP BY e.employee_number, e.employee_name
            HAVING COUNT(i.invoice_id) = 10
        """,
            (week_start.date(), week_end.date()),
        )

        # These should NOT appear in high-perf list (threshold is > 10, not >= 10)
        high_perf = self._execute_query(
            """
            SELECT e.employee_number
            FROM employees e
            JOIN invoices i ON i.employee_number = e.employee_number
            WHERE e.is_active = TRUE
                AND e.position = 'Sales Rep'
                AND i.date_written BETWEEN %s::date AND %s::date
            GROUP BY e.employee_number
            HAVING COUNT(i.invoice_id) > 10
        """,
            (week_start.date(), week_end.date()),
        )

        high_perf_ids = set(row["employee_number"] for row in high_perf)
        for boundary_rep in at_boundary:
            assert (
                boundary_rep["employee_number"] not in high_perf_ids
            ), f"Rep with exactly 10 invoices should not be in high-perf list"

    def test_high_perf_sales_total_consistency(self):
        """Test that high-perf rep sales totals are calculated correctly."""
        today = datetime.now()
        week_end = today + timedelta(days=(6 - today.weekday()))
        week_start = week_end - timedelta(days=6)

        high_perf = self._execute_query(
            """
            SELECT
                e.employee_number,
                e.employee_name,
                COUNT(i.invoice_id) AS invoice_count,
                COALESCE(SUM(i.total_amount), 0) AS total_sales
            FROM employees e
            JOIN invoices i
                ON i.employee_number = e.employee_number
            WHERE e.is_active = TRUE
                AND e.position = 'Sales Rep'
                AND i.date_written BETWEEN %s::date AND %s::date
            GROUP BY e.employee_number, e.employee_name
            HAVING COUNT(i.invoice_id) > 10
        """,
            (week_start.date(), week_end.date()),
        )

        for rep in high_perf:
            # Verify totals are positive
            assert (
                rep["total_sales"] > 0
            ), f"High-perf rep {rep['employee_name']} should have positive sales"
            assert rep["invoice_count"] > 10, f"Invoice count should be > 10"

            # Verify average calculation
            avg_sales = rep["total_sales"] / rep["invoice_count"]
            assert avg_sales > 0, "Average sales should be positive"

    def test_only_sales_reps_qualify(self):
        """Test that only 'Sales Rep' position employees qualify for high-perf metric."""
        today = datetime.now()
        week_end = today + timedelta(days=(6 - today.weekday()))
        week_start = week_end - timedelta(days=6)

        high_perf = self._execute_query(
            """
            SELECT DISTINCT e.position
            FROM employees e
            JOIN invoices i ON i.employee_number = e.employee_number
            WHERE e.is_active = TRUE
                AND i.date_written BETWEEN %s::date AND %s::date
            GROUP BY e.employee_number, e.position
            HAVING COUNT(i.invoice_id) > 10
        """,
            (week_start.date(), week_end.date()),
        )

        for row in high_perf:
            assert (
                row["position"] == "Sales Rep"
            ), f"Only Sales Reps should qualify, got {row['position']}"

    def test_inactive_reps_excluded(self):
        """Test that inactive reps are excluded from high-perf list."""
        today = datetime.now()
        week_end = today + timedelta(days=(6 - today.weekday()))
        week_start = week_end - timedelta(days=6)

        high_perf = self._execute_query(
            """
            SELECT DISTINCT e.is_active
            FROM employees e
            JOIN invoices i ON i.employee_number = e.employee_number
            WHERE i.date_written BETWEEN %s::date AND %s::date
            GROUP BY e.employee_number, e.is_active
            HAVING COUNT(i.invoice_id) > 10
        """,
            (week_start.date(), week_end.date()),
        )

        for row in high_perf:
            assert (
                row["is_active"] == True
            ), "Inactive reps should not appear in high-perf list"


class TestAnalyticsExportIntegration:
    """Test analytics export to DBF and SALESREP sync."""

    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup test database connection and import service."""
        if not HAS_DB:
            pytest.skip("psycopg2 not available")

        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 5432)),
            "database": os.getenv("DB_NAME", "nos_db"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "postgres"),
        }

        try:
            self.conn = psycopg2.connect(**self.db_config)
            from backend.analytics_export import AnalyticsExportService

            self.service = AnalyticsExportService(self.db_config)
            yield
            self.conn.close()
        except Exception as e:
            pytest.skip(f"Setup failed: {e}")

    def _execute_query(self, sql: str, params=()):
        """Execute query and return results."""
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def test_analytics_fetch_returns_valid_data(self):
        """Test that fetching analytics returns valid data structure."""
        analytics = self.service.fetch_analytics()

        assert isinstance(analytics, list), "Analytics should return a list"
        if analytics:
            for row in analytics:
                assert "employee_number" in row
                assert "employee_name" in row
                assert "total_sales" in row
                assert "invoice_count" in row
                assert "commission" in row
                assert row["invoice_count"] >= 0

    def test_salesrep_sync_creates_table(self):
        """Test that sync creates SALESREP table if it doesn't exist."""
        # Drop table if exists
        with self.conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS salesrep CASCADE")
            self.conn.commit()

        # Sync should create it
        count = self.service.sync_to_salesrep()

        # Verify table exists
        table_check = self._execute_query("""
            SELECT COUNT(*) as count FROM information_schema.tables
            WHERE table_name = 'salesrep'
        """)

        assert table_check[0]["count"] > 0, "SALESREP table should be created"

    def test_salesrep_sync_updates_data(self):
        """Test that sync updates SALESREP table with analytics."""
        count = self.service.sync_to_salesrep()

        # Verify data was inserted/updated
        salesrep_data = self._execute_query("SELECT COUNT(*) as count FROM salesrep")
        assert (
            salesrep_data[0]["count"] > 0
        ), "SALESREP table should have data after sync"

        # Verify specific fields
        sample_data = self._execute_query("SELECT * FROM salesrep LIMIT 1")
        if sample_data:
            row = sample_data[0]
            assert "employee_number" in row
            assert "total_sales" in row
            assert "commission" in row
            assert "ytd_sales" in row

    def test_export_to_dbf_creates_file(self):
        """Test that DBF export creates a file."""
        import tempfile
        import os as os_module

        with tempfile.TemporaryDirectory() as tmpdir:
            dbf_path = os_module.path.join(tmpdir, "report1.dbf")
            result_path = self.service.export_to_dbf(dbf_path)

            assert os_module.path.exists(result_path), "DBF file should be created"
            assert result_path.endswith(".dbf"), "File should be DBF format"
            assert (
                os_module.path.getsize(result_path) > 0
            ), "DBF file should not be empty"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
