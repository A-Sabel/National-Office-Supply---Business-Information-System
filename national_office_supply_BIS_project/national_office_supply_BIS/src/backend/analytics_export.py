"""
backend/analytics_export.py
----------------------------
Export sales analytics to DBF file and sync to SALESREP table.
"""

import psycopg2
import psycopg2.extras
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Optional
import struct
import os


class DBFWriter:
    """Simple DBF file writer for legacy report1.dbf export."""

    def __init__(self, filename: str):
        self.filename = filename
        self.records: List[Dict] = []
        self.fields: List[tuple] = []

    def add_field(self, name: str, field_type: str, length: int, decimals: int = 0):
        """Add a field definition. Type: 'C' (char), 'N' (numeric), 'D' (date), 'L' (logical)."""
        self.fields.append((name[:10].ljust(10), field_type, length, decimals))

    def add_record(self, record: Dict):
        """Add a record (dict) to the DBF file."""
        self.records.append(record)

    def write(self):
        """Write records to DBF file."""
        if not self.fields:
            raise ValueError("No fields defined")

        with open(self.filename, "wb") as f:
            # DBF header
            num_records = len(self.records)
            header_length = 64 + len(self.fields) * 32 + 1
            record_length = (
                sum(field[2] for field in self.fields) + 1
            )  # +1 for deletion flag

            # Version byte (0x03 = dBASE III)
            f.write(bytes([0x03]))

            # Last update date (year - 1900, month, day)
            now = datetime.now()
            f.write(bytes([now.year - 1900, now.month, now.day]))

            # Number of records
            f.write(struct.pack("<I", num_records))

            # Header length
            f.write(struct.pack("<H", header_length))

            # Record length
            f.write(struct.pack("<H", record_length))

            # Reserved (20 bytes)
            f.write(b"\x00" * 20)

            # Field definitions
            for field_name, field_type, length, decimals in self.fields:
                f.write(field_name.encode("ascii"))
                f.write(field_type.encode("ascii"))
                f.write(b"\x00" * 4)  # Reserved
                f.write(bytes([length]))
                f.write(bytes([decimals]))
                f.write(b"\x00" * 14)  # Reserved

            # Field definition terminator
            f.write(b"\x0d")

            # Records
            for record in self.records:
                # Deletion flag (space = not deleted)
                f.write(b" ")

                # Write field values
                for field_name, field_type, length, decimals in self.fields:
                    value = record.get(field_name.strip(), "")

                    if field_type == "C":  # Character
                        f.write(
                            str(value)[:length].ljust(length).encode("ascii")[:length]
                        )
                    elif field_type == "N":  # Numeric
                        try:
                            num_val = float(value) if value else 0.0
                            formatted = f"{num_val:0{length}.{decimals}f}"[
                                :length
                            ].rjust(length)
                            f.write(formatted.encode("ascii")[:length])
                        except:
                            f.write(b"0".rjust(length)[:length])
                    elif field_type == "D":  # Date
                        if isinstance(value, str):
                            # Assume YYYY-MM-DD format
                            parts = value.split("-")
                            if len(parts) == 3:
                                f.write(
                                    f"{parts[0]}{parts[1]}{parts[2]}".encode("ascii")
                                )
                            else:
                                f.write(b" " * 8)
                        else:
                            f.write(b" " * 8)
                    elif field_type == "L":  # Logical
                        f.write(b"T" if value else b"F")

            # EOF marker
            f.write(b"\x1a")


class AnalyticsExportService:
    """Export sales analytics and sync to SALESREP table."""

    def __init__(self, db_config: dict):
        self._cfg = db_config

    def _connect(self):
        return psycopg2.connect(**self._cfg)

    def ensure_salesrep_table(self, conn) -> None:
        """Create SALESREP table if it doesn't exist."""
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS salesrep (
                    salesrep_id SERIAL PRIMARY KEY,
                    employee_number INTEGER NOT NULL UNIQUE,
                    employee_name VARCHAR(100) NOT NULL,
                    total_sales NUMERIC(12,2) DEFAULT 0,
                    invoice_count INTEGER DEFAULT 0,
                    largest_sale NUMERIC(12,2) DEFAULT 0,
                    average_sale NUMERIC(12,2) DEFAULT 0,
                    customer_count INTEGER DEFAULT 0,
                    commission NUMERIC(12,2) DEFAULT 0,
                    ytd_sales NUMERIC(12,2) DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()

    def fetch_analytics(self) -> List[Dict]:
        """Fetch sales analytics from database."""
        conn = self._connect()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT
                    e.employee_number,
                    e.employee_name,
                    COALESCE(SUM(i.total_amount), 0) AS total_sales,
                    COUNT(i.invoice_id) AS invoice_count,
                    COALESCE(MAX(i.total_amount), 0) AS largest_sale,
                    COALESCE(AVG(i.total_amount), 0) AS average_sale,
                    COUNT(DISTINCT i.customer_number) AS customer_count,
                    COALESCE(SUM(i.total_amount), 0) * 0.05 AS commission,
                    COALESCE(SUM(i.total_amount), 0) AS ytd_sales
                FROM employees e
                LEFT JOIN invoices i
                    ON i.employee_number = e.employee_number
                    AND i.date_written >= DATE_TRUNC('year', CURRENT_DATE)::date
                WHERE e.is_active = TRUE
                    AND e.position = 'Sales Rep'
                GROUP BY e.employee_number, e.employee_name
                ORDER BY total_sales DESC, e.employee_name
            """)
            return list(cur.fetchall())
        finally:
            conn.close()

    def export_to_dbf(self, output_path: str = "report1.dbf") -> str:
        """Export analytics to DBF file named report1."""
        analytics = self.fetch_analytics()

        dbf = DBFWriter(output_path)
        dbf.add_field("EMP_NUM", "N", 10, 0)
        dbf.add_field("EMP_NAME", "C", 100)
        dbf.add_field("TOT_SALES", "N", 15, 2)
        dbf.add_field("INV_COUNT", "N", 10, 0)
        dbf.add_field("LARGEST", "N", 15, 2)
        dbf.add_field("AVERAGE", "N", 15, 2)
        dbf.add_field("CUST_COUNT", "N", 10, 0)
        dbf.add_field("COMMISSION", "N", 15, 2)
        dbf.add_field("YTD_SALES", "N", 15, 2)

        for row in analytics:
            record = {
                "EMP_NUM": row["employee_number"],
                "EMP_NAME": row["employee_name"],
                "TOT_SALES": float(row["total_sales"]),
                "INV_COUNT": row["invoice_count"],
                "LARGEST": float(row["largest_sale"]),
                "AVERAGE": float(row["average_sale"]),
                "CUST_COUNT": row["customer_count"],
                "COMMISSION": float(row["commission"]),
                "YTD_SALES": float(row["ytd_sales"]),
            }
            dbf.add_record(record)

        dbf.write()
        return os.path.abspath(output_path)

    def sync_to_salesrep(self) -> int:
        """
        Sync analytics to SALESREP table.
        Returns number of records updated/inserted.
        """
        conn = self._connect()
        try:
            self.ensure_salesrep_table(conn)

            analytics = self.fetch_analytics()
            updated_count = 0

            with conn:
                with conn.cursor() as cur:
                    for row in analytics:
                        cur.execute(
                            """
                            INSERT INTO salesrep (
                                employee_number, employee_name, total_sales,
                                invoice_count, largest_sale, average_sale,
                                customer_count, commission, ytd_sales, last_updated
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                            ON CONFLICT (employee_number)
                            DO UPDATE SET
                                employee_name = EXCLUDED.employee_name,
                                total_sales = EXCLUDED.total_sales,
                                invoice_count = EXCLUDED.invoice_count,
                                largest_sale = EXCLUDED.largest_sale,
                                average_sale = EXCLUDED.average_sale,
                                customer_count = EXCLUDED.customer_count,
                                commission = EXCLUDED.commission,
                                ytd_sales = EXCLUDED.ytd_sales,
                                last_updated = NOW()
                        """,
                            (
                                row["employee_number"],
                                row["employee_name"],
                                float(row["total_sales"]),
                                row["invoice_count"],
                                float(row["largest_sale"]),
                                float(row["average_sale"]),
                                row["customer_count"],
                                float(row["commission"]),
                                float(row["ytd_sales"]),
                            ),
                        )
                        updated_count += 1

            return updated_count
        finally:
            conn.close()
