import csv
import datetime
import tkinter as tk
import tkinter.filedialog as fd
import tkinter.messagebox as messagebox
from tkinter import ttk

import customtkinter as ctk
import psycopg2

from backend.report_service import ReportService
from frontend.modular.date_picker import DatePickerField
from .csv_tab import export_inventory

# ── Colour palette ────────────────────────────────────────────────────────────
BRAND_NAVY = "#001440"
BRAND_BLUE = "#3498db"
ACCENT_GREEN = "#2ecc71"
ACCENT_RED = "#e74c3c"
ACCENT_AMBER = "#f39c12"
BG_PAGE = "#f0f2f5"
BG_CARD = "#ffffff"
TEXT_DARK = "#2c3e50"
TEXT_MUTED = "#7f8c8d"
TEXT_WHITE = "#ffffff"
BORDER = "#e0e0e0"

# ── Typography ────────────────────────────────────────────────────────────────
FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_BODY = ("Segoe UI", 12)
FONT_BTN = ("Segoe UI", 12, "bold")
FONT_SMALL = ("Segoe UI", 10)
FONT_TABLE = ("Segoe UI", 11)


# ─────────────────────────────────────────────────────────────────────────────
class SummaryCard(ctk.CTkFrame):
    def __init__(self, parent, title, value, subtitle, icon, color, **kwargs):
        super().__init__(
            parent,
            fg_color=BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
            **kwargs,
        )
        ctk.CTkLabel(self, text=icon, font=("Segoe UI", 24)).pack(
            anchor="w", padx=16, pady=(14, 0)
        )
        ctk.CTkLabel(
            self, text=value, font=("Segoe UI", 28, "bold"), text_color=color
        ).pack(anchor="w", padx=16)
        ctk.CTkLabel(self, text=title, font=FONT_BODY, text_color=TEXT_DARK).pack(
            anchor="w", padx=16
        )
        ctk.CTkLabel(self, text=subtitle, font=FONT_SMALL, text_color=TEXT_MUTED).pack(
            anchor="w", padx=16, pady=(0, 14)
        )


# ─────────────────────────────────────────────────────────────────────────────
class InventorySalesReportView(ctk.CTkFrame):

    _SAMPLE_PARTS = (
        ("p-1001", "Bond Paper A4", 185.0, 42, 25, False, "In Stock"),
        ("p-1002", "Ballpen Blue", 18.5, 12, 20, False, "Low Stock"),
        ("p-1003", "Stapler Heavy Duty", 265.0, 0, 5, False, "Out of Stock"),
        ("p-1004", "Correction Tape", 32.0, 6, 10, True, "On Order"),
    )

    _SAMPLE_SUPPLIERS = {
        "p-1002": [("OfficeMart", 15.75, "555-0102"), ("SupplyHub", 16.25, "555-0142")],
        "p-1003": [("Paper & More", 248.0, "555-0188")],
        "p-1004": [("Stationery Pro", 28.5, "555-0167")],
    }

    # ------------------------------------------------------------------
    def __init__(
        self,
        parent,
        controller=None,
        db_config=None,
        on_toggle_navigation=None,  # ← pulled out of **kwargs
        is_navigation_visible=True,  # ← pulled out of **kwargs
        **kwargs,
    ):
        super().__init__(
            parent, fg_color=BG_PAGE, corner_radius=0, border_width=0, **kwargs
        )

        self.controller = controller
        self.db_config = db_config
        self._on_toggle_navigation = on_toggle_navigation
        self._is_navigation_visible = is_navigation_visible
        self._report_service = ReportService(
            self.db_config or {}, getattr(controller, "session_manager", None)
        )

        self.parts = self._load_parts()
        self.suppliers = self._load_suppliers()

        # Outer grid stretches to fill host frame
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Manual-scroll canvas ──────────────────────────────────────
        self._canvas = tk.Canvas(self, bg=BG_PAGE, highlightthickness=0)
        self._vsb = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vsb.set)

        self._vsb.grid(row=0, column=1, sticky="ns")
        self._canvas.grid(row=0, column=0, sticky="nsew")

        # Inner frame that holds all visible content
        self._body = tk.Frame(self._canvas, bg=BG_PAGE)
        self._body_id = self._canvas.create_window(
            (0, 0), window=self._body, anchor="nw"
        )

        self._canvas.bind("<Configure>", self._on_canvas_resize)
        self._body.bind(
            "<Configure>",
            lambda _e: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        self._canvas.bind_all(
            "<MouseWheel>",
            lambda e: self._canvas.yview_scroll(int(-1 * e.delta / 120), "units"),
        )

        # Build UI
        self._build_header()
        self._build_summary_strip()
        self._build_filter_bar()
        self._build_tabs()

    # ── canvas helpers ────────────────────────────────────────────────
    def _on_canvas_resize(self, event):
        self._canvas.itemconfig(self._body_id, width=event.width)

    def _row_value(self, row, key: str, index: int, default=None):
        if isinstance(row, dict):
            return row.get(key, default)
        if row is None:
            return default
        try:
            return row[index]
        except Exception:
            return default

    def _part_label(self, part_number):
        try:
            return f"P-{int(part_number):04d}"
        except Exception:
            return str(part_number)

    # ── called by ReportsHubView when sidebar is toggled externally ───
    def set_navigation_visibility(self, visible: bool):
        self._is_navigation_visible = visible
        if hasattr(self, "_nav_toggle_btn"):
            self._nav_toggle_btn.configure(text="◀" if visible else "▶")

    # ==================================================================
    # Data loaders
    # ==================================================================
    def _load_parts(self):
        if not self._report_service or not self.db_config:
            return list(self._SAMPLE_PARTS)
        try:
            rows = self._report_service.execute_query("""
                    SELECT p.part_number,
                           p.description,
                           p.selling_price,
                           p.stock_count,
                           p.trigger_amount,
                           p.on_order,
                           CASE
                               WHEN p.stock_count = 0               THEN 'Out of Stock'
                               WHEN p.stock_count <= p.trigger_amount  THEN 'Low Stock'
                               ELSE 'In Stock'
                           END AS status
                    FROM parts p ORDER BY p.part_number
                """)
            return [
                (
                    self._part_label(row["part_number"]),
                    row["description"],
                    row["selling_price"],
                    row["stock_count"],
                    row["trigger_amount"],
                    row["on_order"],
                    row["status"],
                )
                for row in rows
            ] or list(self._SAMPLE_PARTS)
        except Exception as e:
            print(f"[Inventory] _load_parts failed: {e}")
            return list(self._SAMPLE_PARTS)

    def _load_suppliers(self):
        if not self._report_service or not self.db_config:
            return dict(self._SAMPLE_SUPPLIERS)
        try:
            result = {}
            rows = self._report_service.execute_query("""
                SELECT p.part_number,
                    s.company_name,
                    s.phone_number,
                    ip.cost
                FROM   parts p
                JOIN   item_parts ip ON ip.part_number = p.part_number
                JOIN   suppliers s  ON s.supplier_id  = ip.supplier_id
                ORDER  BY p.part_number, ip.cost ASC
            """)
            for row in rows:
                key = self._part_label(row["part_number"])
                result.setdefault(key, []).append(
                    (row["company_name"], float(row["cost"]), row["phone_number"])
                )
            # Only fall back to sample if DB itself is empty of any supplier links
            return result if result else dict(self._SAMPLE_SUPPLIERS)
        except Exception as e:
            print(f"[Inventory] _load_suppliers failed: {e}")
            return dict(self._SAMPLE_SUPPLIERS)

    def _load_reorder(self):
        if not self._report_service or not self.db_config:
            return None
        try:
            rows = self._report_service.execute_query("""
                SELECT
                    p.part_number,
                    p.description,
                    p.stock_count,
                    p.trigger_amount,
                    EXISTS (
                        SELECT 1
                        FROM   purchase_orders po
                        WHERE  po.part_number = p.part_number
                        AND    po.received = FALSE
                    ) AS on_order,
                    EXISTS (
                        SELECT 1
                        FROM   invoice_lines il
                        JOIN   invoices i ON i.invoice_id = il.invoice_id
                        WHERE  il.part_number = p.part_number
                        AND    i.status = 'active'
                    ) AS has_unshipped
                FROM parts p
                WHERE p.stock_count <= p.trigger_amount
                ORDER BY p.stock_count ASC, p.part_number
            """)
            if not rows:
                return []  # ← empty list, NOT None — forces the DB branch
            return [
                (
                    self._part_label(row["part_number"]),
                    row["description"],
                    row["stock_count"],
                    row["trigger_amount"],
                    row["on_order"],
                    row["has_unshipped"],
                )
                for row in rows
            ]
        except Exception as e:
            print(f"[Inventory] _load_reorder failed: {e}")
            return None

    # ==================================================================
    # Header
    # ==================================================================
    def _build_header(self):
        hdr = ctk.CTkFrame(self._body, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(25, 0))

        # ── Left: toggle + title ──────────────────────────────────────
        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left")

        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.pack(anchor="w")

        # Sidebar-toggle arrow button
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

        ctk.CTkLabel(
            title_row, text="Inventory Report", font=FONT_TITLE, text_color=TEXT_DARK
        ).pack(side="left")

        ctk.CTkLabel(
            left,
            text=f"As of  {datetime.date.today().strftime('%B %d, %Y')}  ·  National Office Supplies",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # ── Right: action buttons ─────────────────────────────────────
        right = ctk.CTkFrame(hdr, fg_color="transparent")
        right.pack(side="right")

        ctk.CTkButton(
            right,
            text="⬇  Export CSV",
            width=130,
            height=34,
            corner_radius=6,
            fg_color=BRAND_NAVY,
            hover_color="#002a7a",
            text_color=TEXT_WHITE,
            font=FONT_BTN,
            command=self._export_csv,
        ).pack(side="right")

        ctk.CTkButton(
            right,
            text="↺  Refresh",
            width=110,
            height=34,
            corner_radius=6,
            fg_color="transparent",
            hover_color="#e8f4fd",
            text_color=BRAND_BLUE,
            border_width=1,
            border_color=BRAND_BLUE,
            font=FONT_BTN,
            command=self._apply_filter,
        ).pack(side="right", padx=(0, 10))

    def _handle_nav_toggle(self):
        """Tell the parent hub to toggle the sidebar."""
        if callable(self._on_toggle_navigation):
            self._on_toggle_navigation()

    # ==================================================================
    # KPI strip
    # ==================================================================
    def _build_summary_strip(self):
        strip = ctk.CTkFrame(self._body, fg_color="transparent")
        strip.pack(fill="x", padx=30, pady=(18, 0))
        strip.columnconfigure((0, 1, 2, 3), weight=1, pad=12)

        total = len(self.parts)
        in_stock = sum(1 for p in self.parts if p[6] == "In Stock")
        low_stock = sum(1 for p in self.parts if p[6] == "Low Stock")
        out = sum(1 for p in self.parts if p[6] == "Out of Stock")

        SummaryCard(
            strip, "Total Parts", str(total), "All SKUs tracked", "📦", BRAND_BLUE
        ).grid(row=0, column=0, sticky="nsew", padx=6)
        SummaryCard(
            strip, "In Stock", str(in_stock), "Sufficient quantity", "✅", ACCENT_GREEN
        ).grid(row=0, column=1, sticky="nsew", padx=6)
        SummaryCard(
            strip, "Low / Critical", str(low_stock), "Needs reorder", "⚠️", ACCENT_AMBER
        ).grid(row=0, column=2, sticky="nsew", padx=6)
        SummaryCard(
            strip, "Out of Stock", str(out), "Requires urgent action", "🚨", ACCENT_RED
        ).grid(row=0, column=3, sticky="nsew", padx=6)

    # ==================================================================
    # Filter bar
    # ==================================================================
    def _build_filter_bar(self):
        bar = ctk.CTkFrame(
            self._body,
            fg_color=BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        bar.pack(fill="x", padx=30, pady=(18, 0))

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(inner, text="🔍", font=("Segoe UI", 14)).pack(side="left")

        self._search_var = ctk.StringVar()
        ctk.CTkEntry(
            inner,
            textvariable=self._search_var,
            placeholder_text="Search part number or description…",
            width=260,
            height=36,
            corner_radius=6,
            fg_color="#f5f7fa",
            text_color=TEXT_DARK,
            border_color=BORDER,
        ).pack(side="left", padx=(6, 20))
        self._search_var.trace_add("write", lambda *_: self._apply_filter())

        ctk.CTkLabel(inner, text="Status:", font=FONT_BODY, text_color=TEXT_MUTED).pack(
            side="left"
        )
        self._status_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            inner,
            variable=self._status_var,
            values=["All", "In Stock", "Low Stock", "Out of Stock", "On Order"],
            width=150,
            height=36,
            corner_radius=6,
            fg_color="#f5f7fa",
            button_color=BRAND_BLUE,
            text_color=TEXT_DARK,
            command=lambda _: self._apply_filter(),
        ).pack(side="left", padx=(8, 20))

        ctk.CTkLabel(
            inner, text="Trigger Alert Only:", font=FONT_BODY, text_color=TEXT_MUTED
        ).pack(side="left")
        self._trigger_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            inner,
            text="",
            variable=self._trigger_var,
            width=30,
            fg_color=ACCENT_AMBER,
            hover_color="#e67e22",
            command=self._apply_filter,
        ).pack(side="left", padx=(4, 20))

        # Date range filter
        ctk.CTkLabel(
            inner, text="Date Range:", font=FONT_BODY, text_color=TEXT_MUTED
        ).pack(side="left")
        self._from_picker = DatePickerField(inner, width=110, placeholder_text="From")
        self._from_picker.pack(side="left", padx=(6, 4))
        self._from_picker.entry.bind("<KeyRelease>", lambda *_: self._apply_filter())

        ctk.CTkLabel(inner, text="to", font=FONT_BODY, text_color=TEXT_MUTED).pack(
            side="left", padx=(2, 4)
        )
        self._to_picker = DatePickerField(inner, width=110, placeholder_text="To")
        self._to_picker.pack(side="left", padx=(4, 20))
        self._to_picker.entry.bind("<KeyRelease>", lambda *_: self._apply_filter())

        self._count_label = ctk.CTkLabel(
            inner,
            text=f"{len(self.parts)} records",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
        )
        self._count_label.pack(side="right")

    # ==================================================================
    # Tab container
    # ==================================================================
    def _build_tabs(self):
        self._tab_buttons: dict = {}
        self._tab_frames: dict = {}

        wrapper = ctk.CTkFrame(self._body, fg_color="transparent")
        wrapper.pack(fill="x", padx=30, pady=(18, 30))
        wrapper.columnconfigure(0, weight=1)

        tab_bar = ctk.CTkFrame(
            wrapper,
            fg_color=BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
            height=48,
        )
        tab_bar.grid(row=0, column=0, sticky="ew")

        for key, label in [
            ("overview", "📋  Inventory Overview"),
            ("reorder", "⚠️  Low-Stock / Reorder"),
            ("supplier", "🏭  Supplier Sourcing"),
        ]:
            btn = ctk.CTkButton(
                tab_bar,
                text=label,
                width=210,
                height=36,
                corner_radius=8,
                fg_color="transparent",
                text_color=TEXT_MUTED,
                hover_color="#edf2f7",
                font=FONT_BODY,
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(side="left", padx=6, pady=6)
            self._tab_buttons[key] = btn

        content = ctk.CTkFrame(wrapper, fg_color="transparent")
        content.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        content.columnconfigure(0, weight=1)

        self._tab_frames["overview"] = self._build_overview_tab(content)
        self._tab_frames["reorder"] = self._build_reorder_tab(content)
        self._tab_frames["supplier"] = self._build_supplier_tab(content)

        self._switch_tab("overview")

    def _switch_tab(self, key: str):
        for k, btn in self._tab_buttons.items():
            active = k == key
            btn.configure(
                fg_color=BRAND_NAVY if active else "transparent",
                text_color=TEXT_WHITE if active else TEXT_MUTED,
                font=("Segoe UI", 12, "bold") if active else FONT_BODY,
            )
        for k, frame in self._tab_frames.items():
            if k == key:
                frame.grid(row=0, column=0, sticky="ew")
            else:
                frame.grid_remove()

    # ==================================================================
    # TAB 1 — Inventory Overview
    # ==================================================================
    def _build_overview_tab(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            parent,
            fg_color=BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        frame.columnconfigure(0, weight=1)

        cols = (
            "Part No.",
            "Description",
            "Sell Price",
            "In Stock",
            "Trigger",
            "On Order",
            "Status",
        )
        widths = (90, 250, 90, 80, 70, 80, 120)

        self._overview_tree = self._make_treeview(frame, cols, widths, row=0)
        self._overview_tree.tag_configure("ok", foreground="#1e8449")
        self._overview_tree.tag_configure(
            "low", foreground="#b7950b", font=("Segoe UI", 11, "bold")
        )
        self._overview_tree.tag_configure(
            "out", foreground=ACCENT_RED, font=("Segoe UI", 11, "bold")
        )
        self._overview_tree.tag_configure("order", foreground="#1a5276")
        self._populate_overview(self.parts)
        return frame

    def _populate_overview(self, data):
        tree = self._overview_tree
        tree.delete(*tree.get_children())
        tag_map = {
            "In Stock": "ok",
            "Low Stock": "low",
            "Out of Stock": "out",
            "On Order": "order",
        }
        for p in data:
            part_no, desc, price, stock, trigger, on_order, status = p
            tree.insert(
                "",
                "end",
                values=(
                    part_no,
                    desc,
                    f"₱{price:.2f}",
                    stock,
                    trigger,
                    "Yes" if on_order else "No",
                    status,
                ),
                tags=(tag_map.get(status, "ok"),),
            )
        self._count_label.configure(text=f"{len(data)} records")

    # ==================================================================
    # TAB 2 — Low-Stock / Reorder
    # ==================================================================
    def _build_reorder_tab(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            parent,
            fg_color=BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        frame.columnconfigure(0, weight=1)

        legend = ctk.CTkFrame(frame, fg_color="#fef9e7", corner_radius=8)
        legend.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            legend,
            text="⚠️  Parts at or below trigger quantity.  Bold red = out of stock.  QD-Sec 3 / 4 / 5",
            font=FONT_SMALL,
            text_color="#7d6608",
        ).pack(anchor="w", padx=10, pady=6)

        cols = (
            "Part No.",
            "Description",
            "In Stock",
            "Trigger",
            "On Order?",
            "Has Unshipped Orders",
            "Action Required",
        )
        widths = (90, 220, 80, 70, 90, 150, 160)

        self._reorder_tree = self._make_treeview(frame, cols, widths, row=1)
        self._reorder_tree.tag_configure(
            "urgent", foreground=ACCENT_RED, font=("Segoe UI", 11, "bold")
        )
        self._reorder_tree.tag_configure(
            "low", foreground="#b7950b", font=("Segoe UI", 11)
        )
        self._populate_reorder()
        return frame

    def _populate_reorder(self):
        tree = self._reorder_tree
        tree.delete(*tree.get_children())
        db_rows = self._load_reorder()

        if db_rows is not None:  # DB path (includes empty list)
            for part_no, desc, stock, trigger, on_order, has_unshipped in db_rows:
                # QD-Sec 3/4/5 action logic
                if stock == 0 and not on_order:
                    action, tag = "🚨 Urgent – Reorder NOW", "urgent"
                elif stock == 0 and on_order:
                    action, tag = "⏳ Order Pending", "low"
                elif stock <= trigger and not on_order:
                    action, tag = "📦 Place Reorder", "low"
                else:  # low stock but order already placed
                    action, tag = "⏳ Order Pending", "low"

                tree.insert(
                    "",
                    "end",
                    values=(
                        part_no,
                        desc,
                        stock,
                        trigger,
                        "Yes" if on_order else "No",
                        # QD-Sec5: only flag unshipped if there's no open PO
                        (
                            "⚠️ Yes"
                            if (has_unshipped and not on_order)
                            else ("Yes" if has_unshipped else "No")
                        ),
                        action,
                    ),
                    tags=(tag,),
                )

            if not db_rows:
                tree.insert(
                    "",
                    "end",
                    values=(
                        "—",
                        "No parts at or below trigger level",
                        "",
                        "",
                        "",
                        "",
                        "",
                    ),
                    tags=("low",),
                )

        else:  # fallback to sample data
            for p in [p for p in self.parts if p[3] <= p[4]]:
                part_no, desc, _, stock, trigger, on_order, _ = p
                unshipped = "Yes" if (stock <= 1 and not on_order) else "No"
                if stock == 0:
                    action, tag = "🚨 Urgent – Reorder NOW", "urgent"
                elif not on_order:
                    action, tag = "📦 Place Reorder", "low"
                else:
                    action, tag = "⏳ Order Pending", "low"
                tree.insert(
                    "",
                    "end",
                    values=(
                        part_no,
                        desc,
                        stock,
                        trigger,
                        "Yes" if on_order else "No",
                        unshipped,
                        action,
                    ),
                    tags=(tag,),
                )

    def _build_reorder_tab(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            parent,
            fg_color=BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        frame.columnconfigure(0, weight=1)

        # ── legend + refresh row ──────────────────────────────────────────
        legend_row = ctk.CTkFrame(frame, fg_color="transparent")
        legend_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        legend_row.columnconfigure(0, weight=1)

        legend = ctk.CTkFrame(legend_row, fg_color="#fef9e7", corner_radius=8)
        legend.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            legend,
            text="⚠️  Parts at or below trigger quantity.  Bold red = out of stock.  QD-Sec 3 / 4 / 5",
            font=FONT_SMALL,
            text_color="#7d6608",
        ).pack(anchor="w", padx=10, pady=6)

        ctk.CTkButton(
            legend_row,
            text="↻ Refresh",
            width=90,
            height=30,
            corner_radius=6,
            fg_color="#f3f5f8",
            text_color=TEXT_DARK,
            hover_color=BORDER,
            font=FONT_SMALL,
            command=self._populate_reorder,  # re-queries live DB on click
        ).grid(row=0, column=1, padx=(10, 0))

        cols = (
            "Part No.",
            "Description",
            "In Stock",
            "Trigger",
            "On Order?",
            "Has Unshipped Orders",
            "Action Required",
        )
        widths = (90, 220, 80, 70, 90, 150, 160)

        self._reorder_tree = self._make_treeview(frame, cols, widths, row=1)
        self._reorder_tree.tag_configure(
            "urgent", foreground=ACCENT_RED, font=("Segoe UI", 11, "bold")
        )
        self._reorder_tree.tag_configure(
            "low", foreground="#b7950b", font=("Segoe UI", 11)
        )
        self._populate_reorder()
        return frame

    # ==================================================================
    # TAB 3 — Supplier Sourcing
    # ==================================================================
    def _build_supplier_tab(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            parent,
            fg_color=BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        frame.columnconfigure(0, weight=1)

        note = ctk.CTkFrame(frame, fg_color="#eaf4fb", corner_radius=8)
        note.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            note,
            text="🏭  Suppliers for low-stock parts — sorted cheapest first.  QD-Sec 6",
            font=FONT_SMALL,
            text_color="#1a5276",
        ).pack(anchor="w", padx=10, pady=6)

        cols = (
            "Part No.",
            "Description",
            "Supplier Name",
            "Unit Cost",
            "Phone",
            "Best Price?",
        )
        widths = (90, 200, 180, 90, 140, 100)

        self._supplier_tree = self._make_treeview(frame, cols, widths, row=1)
        self._supplier_tree.tag_configure(
            "cheapest", foreground="#1e8449", font=("Segoe UI", 11, "bold")
        )
        self._populate_supplier()
        return frame

    def _populate_supplier(self):
        tree = self._supplier_tree
        tree.delete(*tree.get_children())

        # Determine which parts are currently low-stock for display filtering
        low_stock_parts = [p for p in self.parts if p[3] <= p[4]]

        if not low_stock_parts:
            tree.insert(
                "",
                "end",
                values=(
                    "—",
                    "No parts currently at or below trigger level",
                    "",
                    "",
                    "",
                    "",
                ),
                tags=("cheapest",),
            )
            return

        rows_inserted = 0
        for part in low_stock_parts:
            part_no, desc = part[0], part[1]
            supplier_list = sorted(self.suppliers.get(part_no, []), key=lambda s: s[1])

            if not supplier_list:
                # Part is low-stock but has no suppliers linked — show it anyway
                tree.insert(
                    "",
                    "end",
                    values=(part_no, desc, "⚠ No supplier linked", "—", "—", "—"),
                    tags=(),
                )
                rows_inserted += 1
                continue

            for i, (name, cost, phone) in enumerate(supplier_list):
                tree.insert(
                    "",
                    "end",
                    values=(
                        part_no if i == 0 else "",
                        desc if i == 0 else "",
                        name,
                        f"₱{cost:.2f}",
                        phone,
                        "✅ Yes" if i == 0 else "—",
                    ),
                    tags=("cheapest",) if i == 0 else (),
                )
                rows_inserted += 1

        if rows_inserted == 0:
            tree.insert(
                "",
                "end",
                values=(
                    "—",
                    "No supplier data found for low-stock parts",
                    "",
                    "",
                    "",
                    "",
                ),
                tags=("cheapest",),
            )

    def _build_supplier_tab(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            parent,
            fg_color=BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        frame.columnconfigure(0, weight=1)

        note_row = ctk.CTkFrame(frame, fg_color="transparent")
        note_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        note_row.columnconfigure(0, weight=1)

        note = ctk.CTkFrame(note_row, fg_color="#eaf4fb", corner_radius=8)
        note.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            note,
            text="🏭  Suppliers for low-stock parts — sorted cheapest first.  QD-Sec 6",
            font=FONT_SMALL,
            text_color="#1a5276",
        ).pack(anchor="w", padx=10, pady=6)

        def _refresh_supplier_tab():
            self.suppliers = self._load_suppliers()
            self._populate_supplier()

        ctk.CTkButton(
            note_row,
            text="↻ Refresh",
            width=90,
            height=30,
            corner_radius=6,
            fg_color="#f3f5f8",
            text_color=TEXT_DARK,
            hover_color=BORDER,
            font=FONT_SMALL,
            command=_refresh_supplier_tab,
        ).grid(row=0, column=1, padx=(10, 0))

        cols = (
            "Part No.",
            "Description",
            "Supplier Name",
            "Unit Cost",
            "Phone",
            "Best Price?",
        )
        widths = (90, 200, 180, 90, 140, 100)

        self._supplier_tree = self._make_treeview(frame, cols, widths, row=1)
        self._supplier_tree.tag_configure(
            "cheapest", foreground="#1e8449", font=("Segoe UI", 11, "bold")
        )
        self._populate_supplier()
        return frame

    # ==================================================================
    # Shared treeview factory
    # ==================================================================
    def _make_treeview(self, parent, cols, widths, row: int) -> ttk.Treeview:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "NOS.Treeview",
            background=BG_CARD,
            foreground=TEXT_DARK,
            rowheight=32,
            fieldbackground=BG_CARD,
            font=FONT_TABLE,
            borderwidth=0,
        )
        style.configure(
            "NOS.Treeview.Heading",
            background=BRAND_NAVY,
            foreground="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
        )
        style.map(
            "NOS.Treeview",
            background=[("selected", "#d6e4f7")],
            foreground=[("selected", BRAND_NAVY)],
        )
        style.map("NOS.Treeview.Heading", background=[("active", "#002a7a")])

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=0, sticky="ew", padx=16, pady=(4, 16))
        container.columnconfigure(0, weight=1)

        vsb = ttk.Scrollbar(container, orient="vertical")
        hsb = ttk.Scrollbar(container, orient="horizontal")
        tree = ttk.Treeview(
            container,
            columns=cols,
            show="headings",
            style="NOS.Treeview",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            height=12,
        )
        vsb.configure(command=tree.yview)
        hsb.configure(command=tree.xview)

        for col, w in zip(cols, widths):
            tree.heading(
                col, text=col, command=lambda c=col: self._sort_column(tree, c, False)
            )
            tree.column(col, width=w, minwidth=60, anchor="w")

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        return tree

    # ==================================================================
    # Column sorting
    # ==================================================================
    def _sort_column(self, tree: ttk.Treeview, col: str, reverse: bool):
        data = [(tree.set(iid, col), iid) for iid in tree.get_children("")]
        try:
            data.sort(
                key=lambda t: float(t[0].replace("₱", "").replace(",", "")),
                reverse=reverse,
            )
        except ValueError:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)
        for idx, (_, iid) in enumerate(data):
            tree.move(iid, "", idx)
        tree.heading(col, command=lambda: self._sort_column(tree, col, not reverse))

    # ==================================================================
    # Filter
    # ==================================================================
    def _apply_filter(self):
        query = self._search_var.get().lower()
        status = self._status_var.get()
        only_low = self._trigger_var.get()
        filtered = [
            p
            for p in self.parts
            if (not query or query in p[0].lower() or query in p[1].lower())
            and (status == "All" or p[6] == status)
            and (not only_low or p[3] <= p[4])
        ]
        self._populate_overview(filtered)

    # ==================================================================
    # CSV export  — exports whatever is currently in the Overview table
    # ==================================================================
    def _export_csv(self):
        rows = [
            self._overview_tree.item(iid, "values")
            for iid in self._overview_tree.get_children()
        ]
        export_inventory(self, rows)
