"""
stock_ordering.py
National Office Supplies BIS — Stock Ordering Report
Covers: QD-Sec6, QD-Sec13
"""

import csv
import customtkinter as ctk
import tkinter as tk
import tkinter.filedialog as fd
from tkinter import ttk, messagebox
import datetime
from typing import Literal, TypedDict

try:
    import psycopg2

    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

from backend.report_service import ReportService
from .csv_tab import export_stock_ordering

# ── Design tokens ────────────────────────────────────────────────────────────
PAGE_BG = "#f0f2f5"
CARD_BG = "#ffffff"
BORDER = "#e8eaed"
TABLE_HDR_BG = "#1e2d3d"
TABLE_BG = "#ffffff"
ROW_ALT = "#fafbfc"

TEXT_DARK = "#1a1f2e"
TEXT_MUTED = "#8a94a6"
TEXT_WHITE = "#ffffff"

C_BLUE = "#3b82f6"
C_RED = "#ef4444"
C_AMBER = "#f59e0b"
C_GREEN = "#22c55e"

C_PENDING = "#b45309"
C_CONFIRMED = "#1d4ed8"
C_NONE = "#dc2626"

FONT_TITLE = ("Segoe UI", 26, "bold")
FONT_CARD_N = ("Segoe UI", 32, "bold")
FONT_CARD_L = ("Segoe UI", 13)
FONT_CARD_S = ("Segoe UI", 10)
FONT_BODY = ("Segoe UI", 11)
FONT_BTN = ("Segoe UI", 12, "bold")
FONT_TBL_HDR = ("Segoe UI", 11, "bold")
FONT_TBL_ROW = ("Segoe UI", 11)


class DBConfig(TypedDict):
    dbname: str
    user: str
    password: str
    host: str
    port: int


TreeAnchor = Literal["nw", "n", "ne", "w", "center", "e", "sw", "s", "se"]


SAMPLE_ROWS = [
    (
        "P-1002",
        "Ballpen Blue (box/12)",
        3,
        10,
        7,
        "Ace Supplies PH",
        "02-8234-5678",
        1.00,
        "Pending Order",
    ),
    (
        "P-1003",
        "Correction Fluid",
        0,
        5,
        5,
        "Metro Stationery",
        "02-8345-6789",
        1.10,
        "Pending Order",
    ),
    (
        "P-1005",
        "Scotch Tape 1 inch",
        1,
        8,
        7,
        "Prime Paper Goods",
        "02-8567-2233",
        0.40,
        "Pending Order",
    ),
    (
        "P-1007",
        "Paper Clips (100pcs)",
        0,
        5,
        5,
        "OfficeHub Manila",
        "02-8789-4455",
        0.20,
        "Pending Order",
    ),
    (
        "P-1008",
        "Folder Long (Plastic)",
        7,
        15,
        8,
        "PaperLine Trading",
        "02-8890-5566",
        0.18,
        "Pending Order",
    ),
    (
        "P-1010",
        "Pencil #2 (box/12)",
        2,
        10,
        8,
        "Rapid Office Solutions",
        "02-9012-7788",
        0.70,
        "Not Ordered",
    ),
    (
        "P-1015",
        "Scissors Office Medium",
        4,
        8,
        4,
        "MetroPaper Trading",
        "02-9567-3233",
        1.90,
        "Pending Order",
    ),
    (
        "P-1016",
        "Correction Tape",
        1,
        10,
        9,
        "CityWide Office Supply",
        "02-9678-4344",
        0.95,
        "Pending Order",
    ),
    (
        "P-1019",
        "Index Cards (100pcs)",
        3,
        10,
        7,
        "NorthStar Stationery",
        "02-9901-7677",
        0.90,
        "Pending Order",
    ),
    (
        "P-1020",
        "Staple Wire No.35",
        0,
        5,
        5,
        "SouthGate Office Mart",
        "02-9012-8788",
        0.45,
        "Pending Order",
    ),
    (
        "P-1023",
        "Calculator Basic Model",
        2,
        5,
        3,
        "SupplyMax Trading",
        "02-9345-1112",
        4.80,
        "Not Ordered",
    ),
    (
        "P-1024",
        "Paper Cutter Small",
        3,
        5,
        2,
        "OfficeLand Depot",
        "02-9456-1213",
        5.90,
        "Not Ordered",
    ),
    (
        "P-1026",
        "Ink Refill Black",
        1,
        5,
        4,
        "BrightOffice Supplies",
        "02-9678-1415",
        1.80,
        "Not Ordered",
    ),
    (
        "P-1028",
        "Correction Pen Metal Tip",
        0,
        5,
        5,
        "ProPaper Solutions",
        "02-9890-1617",
        0.70,
        "Pending Order",
    ),
]


# ── KPI card ─────────────────────────────────────────────────────────────────
class _KpiCard(ctk.CTkFrame):
    def __init__(self, parent, icon, label, value, sub, accent, **kw):
        super().__init__(
            parent,
            fg_color=CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
            **kw,
        )
        ctk.CTkLabel(self, text=icon, font=("Segoe UI", 22)).pack(
            anchor="w", padx=16, pady=(14, 0)
        )
        ctk.CTkLabel(self, text=value, font=FONT_CARD_N, text_color=accent).pack(
            anchor="w", padx=16
        )
        ctk.CTkLabel(self, text=label, font=FONT_CARD_L, text_color=TEXT_DARK).pack(
            anchor="w", padx=16
        )
        ctk.CTkLabel(self, text=sub, font=FONT_CARD_S, text_color=TEXT_MUTED).pack(
            anchor="w", padx=16, pady=(0, 14)
        )


# ── Main view ─────────────────────────────────────────────────────────────────
class StockOrderingReportView(ctk.CTkFrame):

    COLUMNS: tuple[tuple[str, str, int, TreeAnchor], ...] = (
        ("part_no", "Part No.", 90, "w"),
        ("description", "Description", 220, "w"),
        ("stock", "Stock", 70, "center"),
        ("trigger", "Trigger", 70, "center"),
        ("shortage", "Shortage", 80, "center"),
        ("supplier", "Best Supplier", 180, "w"),
        ("phone", "Phone", 130, "w"),
        ("unit_cost", "Unit Cost (₱)", 110, "e"),
        ("order_status", "Order Status", 140, "center"),
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
        super().__init__(
            parent, fg_color=PAGE_BG, corner_radius=0, border_width=0, **kw
        )
        self.controller = controller
        self.db_config = db_config
        self._on_toggle_navigation = on_toggle_navigation
        self._is_navigation_visible = is_navigation_visible
        self._all_rows = []
        self._filter_var = tk.StringVar()
        self._filter_var.trace_add("write", self._on_filter_change)
        self._status_var = tk.StringVar(value="All Statuses")
        self._sort_col = ""
        self._sort_asc = True
        self._report_service = ReportService(
            self.db_config or {}, getattr(controller, "session_manager", None)
        )

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Use CTkScrollableFrame — eliminates all manual canvas/scrollregion bugs
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

    def set_navigation_visibility(self, visible: bool):
        self._is_navigation_visible = visible
        if hasattr(self, "_nav_toggle_btn"):
            self._nav_toggle_btn.configure(text="◀" if visible else "▶")

    def _handle_nav_toggle(self):
        if self._on_toggle_navigation:
            self._on_toggle_navigation()

    def _part_label(self, part_number):
        try:
            return f"P-{int(part_number):04d}"
        except Exception:
            return str(part_number)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_body(self):
        body = self._scroll
        # Title row
        title_row = tk.Frame(body, bg=PAGE_BG)
        title_row.pack(fill="x", padx=28, pady=(8, 0))

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
            text="Stock Ordering Report",
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
            corner_radius=8,
            fg_color="transparent",
            hover_color="#e8f4fd",
            text_color=C_BLUE,
            border_width=1,
            border_color=C_BLUE,
            font=FONT_BTN,
            command=self._load_data,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="⬇  Export CSV",
            width=140,
            height=36,
            corner_radius=8,
            fg_color=TABLE_HDR_BG,
            hover_color="#2d3f52",
            text_color=TEXT_WHITE,
            font=FONT_BTN,
            command=self._export_csv,
        ).pack(side="left")

        # Subtitle
        self._subtitle_lbl = tk.Label(
            body,
            text="QD-Sec6, 13  \u00b7  Generated: \u2014",
            font=("Segoe UI", 11),
            bg=PAGE_BG,
            fg=TEXT_MUTED,
        )
        self._subtitle_lbl.pack(anchor="w", padx=28, pady=(2, 14))

        # KPI cards
        kpi_frame = ctk.CTkFrame(body, fg_color=PAGE_BG, corner_radius=0)
        kpi_frame.pack(fill="x", padx=28, pady=(0, 16))
        for i in range(4):
            kpi_frame.columnconfigure(i, weight=1, uniform="kpi")

        kpi_defs = [
            (
                "\U0001f4e6",
                "Reorder Candidates",
                "\u2014",
                "Low stock or already ordered",
                C_RED,
            ),
            ("\U0001f6a8", "Out of Stock", "\u2014", "Zero units remaining", C_AMBER),
            (
                "\U0001f6d2",
                "Pending Orders",
                "\u2014",
                "Purchase orders in progress",
                C_BLUE,
            ),
            ("\u274c", "Not Yet Ordered", "\u2014", "No PO placed yet", C_GREEN),
        ]
        self._kpi_cards = []
        for col, (icon, lbl, val, sub, accent) in enumerate(kpi_defs):
            card = _KpiCard(
                kpi_frame, icon=icon, label=lbl, value=val, sub=sub, accent=accent
            )
            card.grid(row=0, column=col, sticky="ew", padx=(0, 12) if col < 3 else 0)
            self._kpi_cards.append(card)

        # Filter bar
        filter_card = ctk.CTkFrame(
            body,
            fg_color=CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        filter_card.pack(fill="x", padx=28, pady=(0, 10))
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
            placeholder_text="Search part or supplier\u2026",
            width=220,
            height=30,
            border_width=0,
            fg_color="#f5f6f8",
            font=FONT_BODY,
            text_color=TEXT_DARK,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkOptionMenu(
            filter_inner,
            variable=self._status_var,
            values=["All Statuses", "Pending Order", "Confirmed Order", "Not Ordered"],
            width=160,
            height=32,
            font=FONT_BODY,
            fg_color=CARD_BG,
            button_color="#e5e7eb",
            button_hover_color="#d1d5db",
            text_color=TEXT_DARK,
            dropdown_text_color=TEXT_DARK,
            command=lambda _: self._apply_filter(),
        ).pack(side="left", padx=10)

        self._count_lbl = tk.Label(
            filter_inner, text="\u2014 items", font=FONT_BODY, bg=CARD_BG, fg=TEXT_MUTED
        )
        self._count_lbl.pack(side="right")

        # Table — pack fill="x" so Treeview width follows the window,
        # and the outer CTkScrollableFrame handles vertical scrolling.
        table_card = ctk.CTkFrame(
            body,
            fg_color=CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        table_card.pack(fill="x", padx=28, pady=(0, 24))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "SOR.Treeview",
            background=TABLE_BG,
            fieldbackground=TABLE_BG,
            foreground=TEXT_DARK,
            font=FONT_TBL_ROW,
            rowheight=34,
            borderwidth=0,
        )
        style.configure(
            "SOR.Treeview.Heading",
            background=TABLE_HDR_BG,
            foreground=TEXT_WHITE,
            font=FONT_TBL_HDR,
            relief="flat",
            borderwidth=0,
        )
        style.map(
            "SOR.Treeview",
            background=[("selected", "#dbeafe")],
            foreground=[("selected", TEXT_DARK)],
        )
        style.map("SOR.Treeview.Heading", background=[("active", "#2d3f52")])
        style.layout("SOR.Treeview", [("SOR.Treeview.treearea", {"sticky": "nswe"})])

        col_ids = [c[0] for c in self.COLUMNS]
        self._tree = ttk.Treeview(
            table_card,
            columns=col_ids,
            show="headings",
            style="SOR.Treeview",
            selectmode="browse",
        )

        for col_id, heading, width, anchor in self.COLUMNS:
            self._tree.heading(
                col_id, text=heading, command=lambda c=col_id: self._sort_by(c)
            )
            self._tree.column(
                col_id,
                width=width,
                minwidth=50,
                anchor=anchor,
                stretch=(col_id == "description"),
            )

        self._tree.tag_configure("pending", foreground=C_PENDING)
        self._tree.tag_configure("confirmed", foreground=C_CONFIRMED)
        self._tree.tag_configure("none", foreground=C_NONE)
        self._tree.tag_configure("alt", background=ROW_ALT)

        xsb = ttk.Scrollbar(table_card, orient="horizontal", command=self._tree.xview)
        self._tree.configure(xscrollcommand=xsb.set)
        self._tree.pack(fill="x", padx=0, pady=0)
        xsb.pack(fill="x")

    # ── Data ─────────────────────────────────────────────────────────────────

    def _load_data(self):
        rows = self._fetch_from_db()
        # If _fetch_from_db returned None it means an error occurred while
        # querying the database. When a DB config is present we show an
        # explicit error to the user instead of silently displaying mock data.
        if rows is None:
            if self.db_config:
                err = getattr(self, "_last_db_error", None)
                message = (
                    f"Stock Ordering query failed: {err}"
                    if err
                    else "Stock Ordering query failed (see console)."
                )
                messagebox.showerror("Stock Ordering — DB Error", message)
                rows = []
            else:
                rows = SAMPLE_ROWS[:]
        self._all_rows = rows
        self._subtitle_lbl.configure(
            text=f"QD-Sec6, 13  \u00b7  Generated: "
            f"{datetime.datetime.now().strftime('%b %d, %Y  %I:%M %p')}"
        )
        self._apply_filter()
        self._update_kpis(rows)
        # Jump scroll back to top after refresh
        self.after(50, lambda: self._scroll._parent_canvas.yview_moveto(0.0))

    def _fetch_from_db(self):
        if not self._report_service or not self.db_config:
            return None
        try:
            rows = self._report_service.execute_query("""
                WITH low_stock AS (
                    SELECT
                        p.part_number,
                        p.description,
                        p.stock_count,
                        p.trigger_amount,
                        GREATEST(p.trigger_amount - p.stock_count, 0) AS shortage
                    FROM parts p
                ),
                best_supplier AS (
                    SELECT DISTINCT ON (ip.part_number)
                        ip.part_number,
                        s.company_name,
                        s.phone_number,
                        ip.cost
                    FROM item_parts ip
                    JOIN suppliers s ON s.supplier_id = ip.supplier_id
                    ORDER BY ip.part_number, ip.cost ASC, s.company_name ASC
                ),
                order_status AS (
                    SELECT
                        po.part_number,
                        CASE
                            WHEN COUNT(*) FILTER (WHERE COALESCE(po.received, FALSE)) > 0 THEN 'Confirmed Order'
                            WHEN COUNT(*) > 0 THEN 'Pending Order'
                            ELSE 'Not Ordered'
                        END AS latest_status
                    FROM purchase_orders po
                    GROUP BY po.part_number
                )
                SELECT
                    ls.part_number,
                    ls.description,
                    ls.stock_count,
                    ls.trigger_amount,
                    ls.shortage,
                    COALESCE(bs.company_name, '—') AS company_name,
                    COALESCE(bs.phone_number, '—') AS phone_number,
                    COALESCE(bs.cost, 0) AS cost,
                    COALESCE(os.latest_status, 'Not Ordered') AS order_status
                FROM low_stock ls
                LEFT JOIN best_supplier bs ON bs.part_number = ls.part_number
                LEFT JOIN order_status os ON os.part_number = ls.part_number
                WHERE ls.stock_count <= ls.trigger_amount
                   OR COALESCE(os.latest_status, 'Not Ordered') <> 'Not Ordered'
                ORDER BY ls.stock_count ASC, ls.part_number;
            """)
            return [
                (
                    self._part_label(r["part_number"]),
                    r["description"],
                    r["stock_count"],
                    r["trigger_amount"],
                    r["shortage"],
                    r["company_name"],
                    r["phone_number"],
                    float(r["cost"]),
                    r["order_status"],
                )
                for r in rows
            ]
        except Exception as exc:
            # store last error for UI reporting and print to console
            self._last_db_error = str(exc)
            print(f"[StockOrderingReport] DB error: {exc}")
            return None

    # ── Filter / render ───────────────────────────────────────────────────────

    def _on_filter_change(self, *_):
        self._apply_filter()

    def _apply_filter(self):
        query = self._filter_var.get().strip().lower()
        status = self._status_var.get()
        filtered = []
        for row in self._all_rows:
            (
                part_no,
                desc,
                stock,
                trig,
                shortage,
                supplier,
                phone,
                cost,
                order_status,
            ) = row
            if query and query not in (part_no + desc + (supplier or "")).lower():
                continue
            if status != "All Statuses" and order_status != status:
                continue
            filtered.append(row)
        self._render_rows(filtered)
        self._count_lbl.configure(text=f"{len(filtered)} items")

    def _render_rows(self, rows):
        self._tree.delete(*self._tree.get_children())
        for idx, row in enumerate(rows):
            (
                part_no,
                desc,
                stock,
                trig,
                shortage,
                supplier,
                phone,
                cost,
                order_status,
            ) = row
            values = (
                part_no,
                desc,
                str(stock),
                str(trig),
                str(shortage),
                supplier or "—",
                phone or "—",
                f"\u20b1{float(cost or 0):.2f}",
                order_status,
            )
            tag = (
                "pending"
                if order_status == "Pending Order"
                else "confirmed" if order_status == "Confirmed Order" else "none"
            )
            tags = (tag, "alt") if idx % 2 else (tag,)
            self._tree.insert("", "end", values=values, tags=tags)

        self._tree.configure(height=max(1, len(rows)))

    # ── KPI cards ─────────────────────────────────────────────────────────────

    def _update_kpis(self, rows):
        total = len(rows)
        out_of = sum(1 for r in rows if r[2] == 0)
        pending = sum(1 for r in rows if r[8] == "Pending Order")
        not_ord = sum(1 for r in rows if r[8] == "Not Ordered")
        vals = [str(total), str(out_of), str(pending), str(not_ord)]

        kpi_meta = [
            (
                "\U0001f4e6",
                "Reorder Candidates",
                vals[0],
                "Low stock or already ordered",
                C_RED,
            ),
            ("\U0001f6a8", "Out of Stock", vals[1], "Zero units remaining", C_AMBER),
            (
                "\U0001f6d2",
                "Pending Orders",
                vals[2],
                "Purchase orders in progress",
                C_BLUE,
            ),
            ("\u274c", "Not Yet Ordered", vals[3], "No PO placed yet", C_GREEN),
        ]
        for card, (icon, lbl, val, sub, accent) in zip(self._kpi_cards, kpi_meta):
            for w in card.winfo_children():
                w.destroy()
            ctk.CTkLabel(card, text=icon, font=("Segoe UI", 22)).pack(
                anchor="w", padx=16, pady=(14, 0)
            )
            ctk.CTkLabel(card, text=val, font=FONT_CARD_N, text_color=accent).pack(
                anchor="w", padx=16
            )
            ctk.CTkLabel(card, text=lbl, font=FONT_CARD_L, text_color=TEXT_DARK).pack(
                anchor="w", padx=16
            )
            ctk.CTkLabel(card, text=sub, font=FONT_CARD_S, text_color=TEXT_MUTED).pack(
                anchor="w", padx=16, pady=(0, 14)
            )

    # ── CSV export ────────────────────────────────────────────────────────────

    def _export_csv(self):
        items = self._tree.get_children()
        if not items:
            return
        rows = [self._tree.item(iid, "values") for iid in items]
        headers = [self._tree.heading(c[0])["text"] for c in self.COLUMNS]
        export_stock_ordering(self, rows, headers)

    # ── Column sort ───────────────────────────────────────────────────────────

    def _sort_by(self, col_id: str):
        if self._sort_col == col_id:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col_id
            self._sort_asc = True

        col_idx = [c[0] for c in self.COLUMNS].index(col_id)

        def _key(row):
            v = self._tree.item(row)["values"][col_idx]
            if isinstance(v, str) and v.startswith(("\u20b1", "$")):
                try:
                    return float(v[1:])
                except ValueError:
                    pass
            try:
                return int(v)
            except (ValueError, TypeError):
                return str(v).lower()

        items = list(self._tree.get_children())
        items.sort(key=_key, reverse=not self._sort_asc)
        for i, item in enumerate(items):
            self._tree.move(item, "", i)