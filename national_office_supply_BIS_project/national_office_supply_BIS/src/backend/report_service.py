"""
backend/report_service.py
-------------------------
Base service class for all report queries with reusable filter/sort/export logic.
"""

import psycopg2
import psycopg2.extras
import csv
import json
from io import StringIO
from typing import List, Dict, Optional, Any, Callable
from backend.session_manager import SessionManager


class ReportService:
    """
    Base class for report generation with common filter/sort/export patterns.

    Methods
    -------
    execute_query(sql, params) → list of dicts
    apply_filter(data, column, value, operator='eq') → filtered data
    apply_sort(data, column, ascending=True) → sorted data
    export_csv(data, filename) → str (CSV content)
    export_json(data) → str (JSON content)
    """

    def __init__(self, db_config: dict, session_manager: SessionManager | None = None):
        self._cfg = db_config
        self._session_manager = session_manager

    def _connect(self):
        return psycopg2.connect(**self._cfg)

    def execute_query(self, sql: str, params=()) -> List[Dict]:
        """
        Execute a SQL query and return results as list of dicts.
        """
        conn = self._connect()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, params)
            result = cur.fetchall()
            cur.close()
            return list(result) if result else []
        finally:
            conn.close()

    @staticmethod
    def apply_filter(
        data: List[Dict], column: str, value: Any, operator: str = "eq"
    ) -> List[Dict]:
        """
        Filter a list of dicts by column and value.
        Operators: 'eq', 'ne', 'gt', 'lt', 'gte', 'lte', 'in', 'contains'
        """
        if not data or not column:
            return data

        filtered = []
        for row in data:
            if column not in row:
                continue

            col_val = row[column]

            if operator == "eq":
                if col_val == value:
                    filtered.append(row)
            elif operator == "ne":
                if col_val != value:
                    filtered.append(row)
            elif operator == "gt":
                if col_val > value:
                    filtered.append(row)
            elif operator == "lt":
                if col_val < value:
                    filtered.append(row)
            elif operator == "gte":
                if col_val >= value:
                    filtered.append(row)
            elif operator == "lte":
                if col_val <= value:
                    filtered.append(row)
            elif operator == "in":
                if col_val in value:
                    filtered.append(row)
            elif operator == "contains":
                if value.lower() in str(col_val).lower():
                    filtered.append(row)

        return filtered

    @staticmethod
    def apply_sort(data: List[Dict], column: str, ascending: bool = True) -> List[Dict]:
        """
        Sort a list of dicts by a column.
        """
        if not data or not column or column not in data[0]:
            return data

        return sorted(data, key=lambda x: x.get(column, ""), reverse=not ascending)

    @staticmethod
    def apply_multi_sort(data: List[Dict], sorts: List[tuple]) -> List[Dict]:
        """
        Apply multiple sorts. sorts = [('column1', True), ('column2', False)]
        True = ascending, False = descending.
        """
        for column, ascending in reversed(sorts):
            data = ReportService.apply_sort(data, column, ascending)
        return data

    @staticmethod
    def export_csv(data: List[Dict], filename: str = None) -> str:
        """
        Export list of dicts to CSV format.
        Returns CSV string or writes to file if filename provided.
        """
        if not data:
            return ""

        output = StringIO()
        fieldnames = data[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(data)

        csv_str = output.getvalue()
        output.close()

        if filename:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                f.write(csv_str)

        return csv_str

    @staticmethod
    def export_json(data: List[Dict], filename: str = None) -> str:
        """
        Export list of dicts to JSON format.
        Handles Decimal and date objects.
        """
        from decimal import Decimal
        from datetime import date, datetime

        def json_serializer(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, (date, datetime)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        json_str = json.dumps(data, indent=2, default=json_serializer)

        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(json_str)

        return json_str

    @staticmethod
    def aggregate(
        data: List[Dict], group_column: str, agg_column: str, agg_func: str = "sum"
    ) -> List[Dict]:
        """
        Aggregate data by grouping on group_column and applying agg_func to agg_column.
        agg_func: 'sum', 'avg', 'count', 'min', 'max'
        Returns list of dicts with group_column and aggregated value.
        """
        if not data:
            return []

        groups = {}
        for row in data:
            key = row.get(group_column)
            if key not in groups:
                groups[key] = []
            groups[key].append(row.get(agg_column))

        result = []
        for key, values in groups.items():
            agg_row = {group_column: key}

            if agg_func == "sum":
                agg_row["aggregated"] = sum(v for v in values if v is not None)
            elif agg_func == "avg":
                valid_vals = [v for v in values if v is not None]
                agg_row["aggregated"] = (
                    sum(valid_vals) / len(valid_vals) if valid_vals else 0
                )
            elif agg_func == "count":
                agg_row["aggregated"] = len(values)
            elif agg_func == "min":
                valid_vals = [v for v in values if v is not None]
                agg_row["aggregated"] = min(valid_vals) if valid_vals else None
            elif agg_func == "max":
                valid_vals = [v for v in values if v is not None]
                agg_row["aggregated"] = max(valid_vals) if valid_vals else None

            result.append(agg_row)

        return result

    @staticmethod
    def limit_rows(data: List[Dict], limit: int, offset: int = 0) -> List[Dict]:
        """
        Apply limit and offset (pagination).
        """
        return data[offset : offset + limit]
