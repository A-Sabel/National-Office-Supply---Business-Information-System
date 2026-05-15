"""
export_csv_dialog.py
────────────────────
Reusable CSV export dialog for National Office Supplies BIS.

Provides a popup window that:
  1. Asks the user for a date range (From / To)
  2. Filters rows to that range using a caller-supplied date extractor
  3. Sorts the filtered rows by date (ascending)
  4. Saves to a UTF-8-sig CSV (opens cleanly in Excel)

Usage
-----
Call `open_export_dialog(...)` from any report view's _export_csv method.

    from export_csv_dialog import open_export_dialog

    def _export_csv(self):
        # Collect raw rows from treeview
        rows = [
            self._tree.item(iid, "values")
            for iid in self._tree.get_children()
        ]
        headers = ["Invoice", "Order Date", "Company", "Part", "Qty", "Status"]

        open_export_dialog(
            parent        = self,
            title         = "Backlog Report",
            default_name  = "backlog_report",
            headers       = headers,
            rows          = rows,
            # tell the dialog which column index holds the date value
            date_col_index = 1,          # 0-based index inside each row tuple
            date_label    = "Order Date",
        )

Parameters
----------
parent        : tk widget — used as the dialog's parent window
title         : str       — shown in the dialog title bar
default_name  : str       — base name for the suggested save file
headers       : list[str] — column headers for the CSV
rows          : list[tuple|list] — raw row data (values from treeview or dicts)
date_col_index: int | None — which column in each row contains the date.
                             If None, date filtering is disabled (all rows exported).
date_label    : str       — human-readable name for that date column (shown in UI)
dict_date_key : str | None— if rows are dicts, use this key instead of date_col_index
"""

from __future__ import annotations

import csv
import datetime
import tkinter as tk
import tkinter.filedialog as fd
import tkinter.messagebox as messagebox
from typing import Callable, Sequence

import customtkinter as ctk
from frontend.modular.date_picker import DatePickerField

# ── palette (matches the rest of the app) ────────────────────────────────────
BG_PAGE = "#f0f2f5"
BG_CARD = "#ffffff"
BORDER = "#e0e0e0"
TEXT_DARK = "#2c3e50"
TEXT_MUTED = "#7f8c8d"
ACCENT_BLUE = "#3498db"
ACCENT_GREEN = "#2ecc71"
BRAND_NAVY = "#001f5b"


# ── helpers ───────────────────────────────────────────────────────────────────


def _parse_date(value) -> datetime.date | None:
    """Try to coerce *value* to a date.  Returns None on failure."""
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if value is None:
        return None
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%b %d, %Y"):
        try:
            return datetime.datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    return None


def _get_date_from_row(row, date_col_index: int | None, dict_date_key: str | None):
    """Extract the date value from a row (tuple/list OR dict)."""
    if isinstance(row, dict):
        key = dict_date_key or "date"
        return _parse_date(row.get(key))
    if date_col_index is not None and date_col_index < len(row):
        return _parse_date(row[date_col_index])
    return None


def _row_values(row) -> list:
    """Return a flat list of values regardless of whether row is dict or sequence."""
    if isinstance(row, dict):
        return list(row.values())
    return list(row)


# ── main public function ──────────────────────────────────────────────────────


def open_export_dialog(
    parent,
    title: str,
    default_name: str,
    headers: list[str],
    rows: list,
    date_col_index: int | None = None,
    date_label: str = "Date",
    dict_date_key: str | None = None,
) -> None:
    """Open a modal date-range export dialog."""

    dialog = _ExportDialog(
        parent=parent,
        report_title=title,
        default_name=default_name,
        headers=headers,
        rows=rows,
        date_col_index=date_col_index,
        date_label=date_label,
        dict_date_key=dict_date_key,
    )
    dialog.grab_set()  # modal
    parent.wait_window(dialog)


# ── dialog class ─────────────────────────────────────────────────────────────


class _ExportDialog(ctk.CTkToplevel):
    """Internal modal window — use open_export_dialog() instead."""

    def __init__(
        self,
        parent,
        report_title: str,
        default_name: str,
        headers: list[str],
        rows: list,
        date_col_index: int | None,
        date_label: str,
        dict_date_key: str | None,
    ):
        super().__init__(parent)
        self.title(f"Export — {report_title}")
        self.resizable(False, False)
        self.configure(fg_color=BG_PAGE)

        self._report_title = report_title
        self._default_name = default_name
        self._headers = headers
        self._rows = rows
        self._date_col_idx = date_col_index
        self._date_label = date_label
        self._dict_date_key = dict_date_key

        self._has_date_filter = date_col_index is not None or dict_date_key is not None

        self._build()
        self._center()

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self):
        pad = {"padx": 24, "pady": 0}

        # ── title ──────────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text=f"Export  ·  {self._report_title}",
            font=("Segoe UI", 17, "bold"),
            text_color=TEXT_DARK,
        ).pack(anchor="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            self,
            text="Choose a date range to filter records before exporting.",
            font=("Segoe UI", 11),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=24, pady=(0, 16))

        # ── separator ─────────────────────────────────────────────────────────
        sep = ctk.CTkFrame(self, fg_color=BORDER, height=1)
        sep.pack(fill="x", padx=24, pady=(0, 16))

        # ── date card ─────────────────────────────────────────────────────────
        card = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        card.pack(fill="x", padx=24, pady=(0, 16))
        card.grid_columnconfigure((0, 1), weight=1)

        if self._has_date_filter:
            ctk.CTkLabel(
                card,
                text=f"Filter by {self._date_label}",
                font=("Segoe UI", 12, "bold"),
                text_color=TEXT_DARK,
            ).grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 6))

            self._from_picker = DatePickerField(
                card,
                label="From",
                width=160,
            )
            self._from_picker.grid(
                row=1, column=0, sticky="ew", padx=(14, 6), pady=(0, 14)
            )

            self._to_picker = DatePickerField(
                card,
                label="To",
                width=160,
            )
            self._to_picker.grid(
                row=1, column=1, sticky="ew", padx=(6, 14), pady=(0, 14)
            )

            self._from_var = self._from_picker.variable
            self._to_var = self._to_picker.variable

            ctk.CTkLabel(
                card,
                text="💡  Leave both blank to export all records.",
                font=("Segoe UI", 10),
                text_color=TEXT_MUTED,
            ).grid(row=3, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 12))

        else:
            # No date column available — just confirm
            self._from_var = ctk.StringVar()
            self._to_var = ctk.StringVar()
            ctk.CTkLabel(
                card,
                text="ℹ  This report has no date column — all visible rows will be exported.",
                font=("Segoe UI", 11),
                text_color=TEXT_MUTED,
                wraplength=380,
            ).pack(padx=14, pady=16)

        # ── sort note ──────────────────────────────────────────────────────────
        if self._has_date_filter:
            sort_note = ctk.CTkFrame(
                self,
                fg_color="#eaf4fb",
                corner_radius=8,
            )
            sort_note.pack(fill="x", padx=24, pady=(0, 16))
            ctk.CTkLabel(
                sort_note,
                text="🗂  Records will be sorted by date (oldest → newest) in the exported file.",
                font=("Segoe UI", 10),
                text_color="#1a6a9a",
            ).pack(anchor="w", padx=12, pady=8)

        # ── preview label ─────────────────────────────────────────────────────
        self._preview_lbl = ctk.CTkLabel(
            self,
            text=f"{len(self._rows)} records available.",
            font=("Segoe UI", 11),
            text_color=TEXT_MUTED,
        )
        self._preview_lbl.pack(anchor="w", padx=24, pady=(0, 14))

        if self._has_date_filter:
            self._from_var.trace_add("write", lambda *_: self._update_preview())
            self._to_var.trace_add("write", lambda *_: self._update_preview())

        # ── buttons ───────────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(0, 20))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            width=110,
            height=38,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#f0f0f0",
            text_color=TEXT_DARK,
            border_width=1,
            border_color=BORDER,
            font=("Segoe UI", 12),
            command=self.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text="⬇  Export CSV",
            width=150,
            height=38,
            corner_radius=8,
            fg_color=BRAND_NAVY,
            hover_color="#002a7a",
            text_color="white",
            font=("Segoe UI", 12, "bold"),
            command=self._do_export,
        ).pack(side="right")

    # ── logic ─────────────────────────────────────────────────────────────────

    def _filtered_rows(self) -> list:
        """Return rows matching the chosen date range, sorted by date asc."""
        from_date = (
            _parse_date(self._from_var.get().strip()) if self._has_date_filter else None
        )
        to_date = (
            _parse_date(self._to_var.get().strip()) if self._has_date_filter else None
        )

        result = []
        for row in self._rows:
            if self._has_date_filter and (from_date or to_date):
                d = _get_date_from_row(row, self._date_col_idx, self._dict_date_key)
                if from_date and d and d < from_date:
                    continue
                if to_date and d and d > to_date:
                    continue
            result.append(row)

        # sort by date column ascending (rows without dates go to the end)
        if self._has_date_filter:

            def _sort_key(row):
                d = _get_date_from_row(row, self._date_col_idx, self._dict_date_key)
                return d or datetime.date.max

            result.sort(key=_sort_key)

        return result

    def _update_preview(self):
        try:
            n = len(self._filtered_rows())
            self._preview_lbl.configure(
                text=f"{n} record{'s' if n != 1 else ''} match the selected range."
            )
        except Exception:
            pass

    def _do_export(self):
        rows = self._filtered_rows()
        if not rows:
            messagebox.showinfo(
                "Export", "No records match the selected date range.", parent=self
            )
            return

        today = datetime.date.today().strftime("%Y-%m-%d")
        filepath = fd.asksaveasfilename(
            parent=self,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"{self._default_name}_{today}.csv",
            title=f"Save {self._report_title}",
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(self._headers)
                for row in rows:
                    writer.writerow(_row_values(row))

            messagebox.showinfo(
                "Export Complete",
                f"✅  {len(rows)} records exported to:\n{filepath}",
                parent=self,
            )
            self.destroy()
        except Exception as ex:
            messagebox.showerror("Export Failed", str(ex), parent=self)

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")


# ── convenience wrappers (one per report) ─────────────────────────────────────


def export_weekly_sales(parent, rows: list):
    """Weekly Sales — date field: 'Week Ending' (index 8)."""
    open_export_dialog(
        parent=parent,
        title="Weekly Sales Report",
        default_name="weekly_sales",
        headers=[
            "Rep ID",
            "Rep Name",
            "Total Sales",
            "# Invoices",
            "Largest Sale",
            "Avg Sale",
            "# Customers",
            "Commission",
            "Week Ending",
        ],
        rows=rows,
        date_col_index=8,
        date_label="Week Ending",
    )


def export_inventory(parent, rows: list):
    """Inventory Report — no date column; exports all visible rows."""
    open_export_dialog(
        parent=parent,
        title="Inventory Report",
        default_name="inventory_report",
        headers=[
            "Part No.",
            "Description",
            "Sell Price",
            "In Stock",
            "Trigger",
            "On Order",
            "Status",
        ],
        rows=rows,
        date_col_index=None,
        date_label="",
    )


def export_stock_ordering(parent, rows: list, headers: list[str]):
    """Stock Ordering Report — no date column; exports all visible rows."""
    open_export_dialog(
        parent=parent,
        title="Stock Ordering Report",
        default_name="stock_ordering",
        headers=headers,
        rows=rows,
        date_col_index=None,
        date_label="",
    )


def export_backlog(parent, rows: list):
    """Backlog Report — date field: 'Order Date' (index 1)."""
    open_export_dialog(
        parent=parent,
        title="Backlog Report",
        default_name="backlog_report",
        headers=[
            "Invoice",
            "Order Date",
            "Cust #",
            "Company",
            "Part",
            "Description",
            "Qty",
            "Status",
        ],
        rows=rows,
        date_col_index=1,
        date_label="Order Date",
    )


def export_customer_balances(parent, rows: list):
    """Customer List & Balances — no date column."""
    open_export_dialog(
        parent=parent,
        title="Customer List & Balances",
        default_name="customer_list",
        headers=[
            "Cust. No.",
            "Company",
            "Address",
            "Phone",
            "Current Balance",
            "Status",
        ],
        rows=rows,
        date_col_index=None,
        date_label="",
    )


def export_customer_payments(parent, rows: list, headers: list[str]):
    """Customer Payment History — date field: 'Payment Date' (index 3)."""
    open_export_dialog(
        parent=parent,
        title="Customer Payment History",
        default_name="payment_history",
        headers=headers,
        rows=rows,
        date_col_index=3,
        date_label="Payment Date",
    )


def export_audit_log(parent, rows: list[dict]):
    """Audit Log — date field: 'timestamp' dict key."""
    open_export_dialog(
        parent=parent,
        title="Audit Log",
        default_name="audit_log",
        headers=[
            "Log ID",
            "Timestamp",
            "Action",
            "Actor",
            "Target Table",
            "Target ID",
            "Details",
        ],
        rows=rows,
        date_col_index=None,
        dict_date_key="timestamp",
        date_label="Timestamp",
    )
