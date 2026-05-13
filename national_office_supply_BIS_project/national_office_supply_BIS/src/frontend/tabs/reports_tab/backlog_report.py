"""
frontend/tabs/reports_tab/backlog_report.py
--------------------------------------------
Backlog Tracking Report: Ordered parts not yet shipped (QD-Sec10)
"""

import csv
import customtkinter as ctk
import tkinter as tk
import tkinter.filedialog as fd
from tkinter import ttk, messagebox
import datetime
from typing import TypedDict, Optional, List, Dict

from .csv_tab import export_backlog

try:
    import psycopg2
    import psycopg2.extras

    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

from backend.report_service import ReportService

# ── Design tokens ────────────────────────────────────────────────────────────
PAGE_BG = "#f0f2f5"
CARD_BG = "#ffffff"
BORDER = "#e8eaed"
TEXT_DARK = "#1a1f2e"
TEXT_MUTED = "#8a94a6"
TEXT_WHITE = "#ffffff"
ACCENT_RED = "#ef4444"
ACCENT_BLUE = "#3b82f6"

FONT_TITLE = ("Segoe UI", 26, "bold")
FONT_BODY = ("Segoe UI", 11)
FONT_BTN = ("Segoe UI", 12, "bold")
FONT_TBL_HDR = ("Segoe UI", 11, "bold")
FONT_TBL_ROW = ("Segoe UI", 11)


class DBConfig(TypedDict):
    host: str
    port: int
    database: str
    user: str
    password: str


SAMPLE_BACKLOG = [
    (
        "INV-1001",
        "2006-08-09",
        "CUST-APX-0015",
        "Ace Parts Ltd",
        "P-1002",
        "Ballpen Blue (box/12)",
        5,
        "active",
    ),
    (
        "INV-1002",
        "2006-08-09",
        "CUST-BIC-0008",
        "BIC Supplies",
        "P-1005",
        "Scotch Tape 1 inch",
        3,
        "active",
    ),
    (
        "INV-1003",
        "2006-08-08",
        "CUST-MET-0012",
        "Metro Trading",
        "P-1007",
        "Paper Clips (100pcs)",
        10,
        "active",
    ),
]


class BacklogReportView(ctk.CTkFrame):
    """Backlog tracking report: ordered parts not yet shipped."""

    COLUMNS = (
        ("invoice_id", "Invoice", 100, "w"),
        ("date_written", "Order Date", 120, "w"),
        ("customer_number", "Cust #", 80, "center"),
        ("company_name", "Company", 180, "w"),
        ("part_number", "Part", 80, "center"),
        ("description", "Description", 250, "w"),
        ("quantity", "Qty", 70, "center"),
        ("status", "Status", 100, "center"),
    )

    def __init__(
        self,
        parent,
        controller=None,
        db_config=None,
        on_toggle_navigation=None,
        is_navigation_visible=True,
        **kw,
    ):
        # consume navigation-related kwargs so they aren't passed to CTkFrame
        self._on_toggle_navigation = on_toggle_navigation
        self._is_navigation_visible = is_navigation_visible

        super().__init__(
            parent, fg_color=PAGE_BG, corner_radius=0, border_width=0, **kw
        )

        self.controller = controller
        self.db_config = db_config
        self._report_service = ReportService(
            self.db_config or {}, getattr(controller, "session_manager", None)
        )
        # rows are tuples representing table columns (invoice_id, date, ...)
        self._all_rows: List[tuple] = []
        self._filter_var = tk.StringVar()
        self._filter_var.trace_add("write", self._on_filter_change)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=PAGE_BG,
            corner_radius=0,
            scrollbar_button_color="#c8cdd6",
            scrollbar_button_hover_color="#a0a8b5",
        )
        self._scroll.grid(row=0, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

        self._build_body()
        self._load_data()

    def _build_body(self):
        body = self._scroll
        pad_x = 28

        # Title row
        title_row = tk.Frame(body, bg=PAGE_BG)
        title_row.pack(fill="x", padx=pad_x, pady=(8, 0))

        self._nav_toggle_btn = ctk.CTkButton(
            title_row,
            text="◀" if self._is_navigation_visible else "▶",
            width=30,
            height=30,
            corner_radius=8,
            fg_color="#2f9e44",
            hover_color="#2b8a3e",
            text_color=TEXT_WHITE,
            border_width=0,
            font=("Segoe UI", 12, "bold"),
            command=self._handle_nav_toggle,
        )
        self._nav_toggle_btn.pack(side="left", padx=(0, 10))

        tk.Label(
            title_row,
            text="Backlog Tracking",
            font=FONT_TITLE,
            bg=PAGE_BG,
            fg=TEXT_DARK,
        ).pack(side="left")

        btn_frame = tk.Frame(title_row, bg=PAGE_BG)
        btn_frame.pack(side="right", anchor="s")

        ctk.CTkButton(
            btn_frame,
            text="↺  Refresh",
            width=110,
            height=36,
            font=FONT_BTN,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#e8f4fd",
            text_color=ACCENT_BLUE,
            border_width=1,
            border_color=ACCENT_BLUE,
            command=self._load_data,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="⬇  Export CSV",
            width=140,
            height=36,
            font=FONT_BTN,
            corner_radius=8,
            fg_color="#1e2d3d",
            hover_color="#2d3f52",
            text_color=TEXT_WHITE,
            command=self._export_csv,
        ).pack(side="left")

        # Subtitle
        self._subtitle_lbl = tk.Label(
            body,
            text="QD-Sec10  \u00b7  Generated: \u2014",
            font=("Segoe UI", 11),
            bg=PAGE_BG,
            fg=TEXT_MUTED,
        )
        self._subtitle_lbl.pack(anchor="w", padx=pad_x, pady=(2, 14))

        # Stats
        stats_frame = ctk.CTkFrame(
            body,
            fg_color=CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        stats_frame.pack(fill="x", padx=pad_x, pady=(0, 14))
        for i in range(3):
            stats_frame.grid_columnconfigure(i, weight=1)

        self._total_orders_lbl = ctk.CTkLabel(
            stats_frame, text="—", font=("Segoe UI", 32, "bold"), text_color=ACCENT_BLUE
        )
        self._total_orders_lbl.grid(row=0, column=0, padx=16, pady=(12, 4))
        ctk.CTkLabel(
            stats_frame,
            text="Active Orders",
            font=("Segoe UI", 11),
            text_color=TEXT_MUTED,
        ).grid(row=1, column=0, padx=16, pady=(0, 12))

        self._total_lines_lbl = ctk.CTkLabel(
            stats_frame, text="—", font=("Segoe UI", 32, "bold"), text_color=ACCENT_RED
        )
        self._total_lines_lbl.grid(row=0, column=1, padx=16, pady=(12, 4))
        ctk.CTkLabel(
            stats_frame,
            text="Open Line Items",
            font=("Segoe UI", 11),
            text_color=TEXT_MUTED,
        ).grid(row=1, column=1, padx=16, pady=(0, 12))

        self._total_qty_lbl = ctk.CTkLabel(
            stats_frame, text="—", font=("Segoe UI", 32, "bold"), text_color="#22c55e"
        )
        self._total_qty_lbl.grid(row=0, column=2, padx=16, pady=(12, 4))
        ctk.CTkLabel(
            stats_frame,
            text="Total Qty Pending",
            font=("Segoe UI", 11),
            text_color=TEXT_MUTED,
        ).grid(row=1, column=2, padx=16, pady=(0, 12))

        # Filter bar
        filter_card = ctk.CTkFrame(
            body,
            fg_color=CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        filter_card.pack(fill="x", padx=pad_x, pady=(0, 10))
        filter_inner = tk.Frame(filter_card, bg=CARD_BG)
        filter_inner.pack(fill="x", padx=14, pady=10)

        search_wrap = ctk.CTkFrame(
            filter_inner,
            fg_color="#f5f6f8",
            corner_radius=7,
            border_width=1,
            border_color=BORDER,
        )
        search_wrap.pack(side="left")
        tk.Label(search_wrap, text="\U0001f50d", bg="#f5f6f8", font=FONT_BODY).pack(
            side="left", padx=(8, 2)
        )
        ctk.CTkEntry(
            search_wrap,
            textvariable=self._filter_var,
            placeholder_text="Search invoice, part, or customer\u2026",
            width=350,
            height=30,
            border_width=0,
            fg_color="#f5f6f8",
            font=FONT_BODY,
            text_color=TEXT_DARK,
        ).pack(side="left", padx=(0, 6))

        self._count_lbl = tk.Label(
            filter_inner, text="\u2014 items", font=FONT_BODY, bg=CARD_BG, fg=TEXT_MUTED
        )
        self._count_lbl.pack(side="right")

        # Table
        table_card = ctk.CTkFrame(
            body,
            fg_color=CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        table_card.pack(fill="x", padx=pad_x, pady=(0, 24))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Backlog.Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground=TEXT_DARK,
            font=FONT_TBL_ROW,
            rowheight=34,
            borderwidth=0,
        )
        style.configure(
            "Backlog.Treeview.Heading",
            background="#1e2d3d",
            foreground=TEXT_WHITE,
            font=FONT_TBL_HDR,
            relief="flat",
            borderwidth=0,
        )
        style.map(
            "Backlog.Treeview",
            background=[("selected", "#dbeafe")],
            foreground=[("selected", TEXT_DARK)],
        )
        style.map("Backlog.Treeview.Heading", background=[("active", "#2d3f52")])

        col_ids = [c[0] for c in self.COLUMNS]
        self._tree = ttk.Treeview(
            table_card,
            columns=col_ids,
            show="headings",
            style="Backlog.Treeview",
            selectmode="browse",
        )

        for col_id, heading, width, anchor in self.COLUMNS:
            self._tree.heading(col_id, text=heading)
            self._tree.column(
                col_id,
                width=width,
                minwidth=50,
                anchor=anchor,  # type: ignore[arg-type]
                stretch=(col_id == "description"),
            )

        xsb = ttk.Scrollbar(table_card, orient="horizontal", command=self._tree.xview)
        self._tree.configure(xscrollcommand=xsb.set)
        self._tree.pack(fill="x", padx=0, pady=0)
        xsb.pack(fill="x")

    def set_navigation_visibility(self, visible: bool):
        self._is_navigation_visible = visible
        if hasattr(self, "_nav_toggle_btn"):
            self._nav_toggle_btn.configure(text="◀" if visible else "▶")

    def _handle_nav_toggle(self):
        if self._on_toggle_navigation:
            self._on_toggle_navigation()

    def _load_data(self):
        """Load backlog data from database."""
        rows = self._fetch_from_db() or SAMPLE_BACKLOG[:]
        self._all_rows = rows
        self._subtitle_lbl.configure(
            text=f"QD-Sec10  \u00b7  Generated: {datetime.datetime.now().strftime('%b %d, %Y  %I:%M %p')}"
        )
        self._apply_filter()
        self._update_stats(rows)
        self.after(50, lambda: self._scroll._parent_canvas.yview_moveto(0.0))

    def _fetch_from_db(self) -> Optional[List[tuple]]:
        """Fetch ordered but unshipped parts from database."""
        if not self._report_service or not self.db_config:
            return None
        try:
            rows = self._report_service.execute_query("""
                SELECT DISTINCT
                    i.invoice_id::text,
                    i.date_written::text,
                    c.customer_number,
                    c.company_name,
                    p.part_number,
                    p.description,
                    il.quantity,
                    i.status
                FROM invoices i
                JOIN customers c ON c.customer_number = i.customer_number
                JOIN invoice_lines il ON il.invoice_id = i.invoice_id
                JOIN parts p ON p.part_number = il.part_number
                WHERE i.status IN ('active', 'pending')
                ORDER BY i.invoice_id DESC, p.part_number
            """)
            return [
                (
                    row["invoice_id"],
                    row["date_written"],
                    row["customer_number"],
                    row["company_name"],
                    row["part_number"],
                    row["description"],
                    row["quantity"],
                    row["status"],
                )
                for row in rows
            ]
        except Exception as exc:
            print(f"[BacklogReport] DB error: {exc}")
            return None

    def _apply_filter(self):
        """Apply search filter to backlog rows."""
        query = self._filter_var.get().strip().lower()
        filtered = []
        for row in self._all_rows:
            inv_id, date, cust_num, cust_name, part_num, desc, qty, status = row
            if (
                query
                and query
                not in (str(inv_id) + str(part_num) + desc + cust_name).lower()
            ):
                continue
            filtered.append(row)
        self._render_rows(filtered)
        self._count_lbl.configure(text=f"{len(filtered)} items")

    def _render_rows(self, rows):
        """Render backlog rows in table."""
        self._tree.delete(*self._tree.get_children())
        for idx, row in enumerate(rows):
            inv_id, date, cust_num, cust_name, part_num, desc, qty, status = row
            values = (inv_id, date, cust_num, cust_name, part_num, desc, qty, status)
            self._tree.insert("", "end", values=values)

    def _update_stats(self, rows):
        """Update summary statistics."""
        unique_orders = len(set(row[0] for row in rows))  # invoice_id
        total_lines = len(rows)
        total_qty = sum(row[6] for row in rows)  # quantity

        self._total_orders_lbl.configure(text=str(unique_orders))
        self._total_lines_lbl.configure(text=str(total_lines))
        self._total_qty_lbl.configure(text=str(total_qty))

    def _export_csv(self):
        rows = [self._tree.item(iid, "values") for iid in self._tree.get_children()]
        export_backlog(self, rows)

    def _on_filter_change(self, *args):
        """Called when filter text changes."""
        self._apply_filter()