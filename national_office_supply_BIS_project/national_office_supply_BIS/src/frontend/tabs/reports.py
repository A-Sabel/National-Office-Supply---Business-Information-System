"""
weekly_sales_report.py
National Office Supplies BIS — Weekly Sales Report
Place at: frontend/tabs/weekly_sales_report.py

Matches the Inventory page style exactly:
  - Light #f0f2f5 page background
  - Large bold title + muted subtitle  (top-left)
  - Print + Export CSV buttons          (top-right)
  - 4 KPI cards with large coloured numbers
  - Light filter bar (search + dropdowns + record count)
  - Dark navy tab bar with active pill
  - Dark navy table headers, coloured row text by status
  - No right-side panel — full-width table

Covers: QD-Sec7, QD-Sec9, QD-Sec12, FS-Sec7
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import datetime

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


# ── Design tokens (extracted directly from screenshot) ────────────────────
PAGE_BG      = "#f0f2f5"   # page / scrollable frame bg
CARD_BG      = "#ffffff"
BORDER       = "#e8eaed"
TABLE_HDR_BG = "#1e2d3d"   # dark navy header (identical to inventory)
TABLE_BG     = "#ffffff"
ROW_ALT      = "#fafbfc"
TAB_ACTIVE   = "#1e2d3d"   # filled navy pill
TAB_INACTIVE = "transparent"
FILTER_BG    = "#ffffff"
SEARCH_BG    = "#f5f6f8"

TEXT_DARK    = "#1a1f2e"
TEXT_MUTED   = "#8a94a6"
TEXT_WHITE   = "#ffffff"

# KPI accent colours (match inventory card numbers exactly)
C_BLUE   = "#3b82f6"   # Total Reps — blue
C_GREEN  = "#22c55e"   # Top Performers — green
C_AMBER  = "#f59e0b"   # Total Invoices — amber
C_RED    = "#ef4444"   # Commissions Due — red

# Row status colours (matching inventory Low Stock / In Stock / Out of Stock)
C_ROW_HIGH   = "#b45309"   # > 10 invoices — amber/orange like "Low Stock"
C_ROW_TOP    = "#15803d"   # top performer — green like "In Stock"
C_ROW_ZERO   = "#dc2626"   # 0 sales — red like "Out of Stock"
C_ROW_NORMAL = "#374151"   # normal — dark grey like "In Stock" normal rows

FONT_TITLE   = ("Segoe UI", 26, "bold")
FONT_SUB     = ("Segoe UI", 11)
FONT_CARD_NUM= ("Segoe UI", 32, "bold")
FONT_CARD_LBL= ("Segoe UI", 13)
FONT_CARD_SUB= ("Segoe UI", 10)
FONT_BODY    = ("Segoe UI", 11)
FONT_SMALL   = ("Segoe UI", 10)
FONT_BTN     = ("Segoe UI", 11, "bold")
FONT_TBL_HDR = ("Segoe UI", 11, "bold")
FONT_TBL_ROW = ("Segoe UI", 11)
FONT_TAB_ACT = ("Segoe UI", 12, "bold")
FONT_TAB_IN  = ("Segoe UI", 12)


# ── Sample data ────────────────────────────────────────────────────────────
SAMPLE_ROWS = [
    # (rep_id, name, total_sales, invoices, largest, avg, customers, comm, week)
    ("REP-001", "Maria Santos",     148500.00, 23, 18000.00, 6456.52,  8, 7425.00, "2006-08-09"),
    ("REP-002", "Jose Reyes",        92300.50, 11, 15200.00, 8390.95,  5, 4615.03, "2006-08-09"),
    ("REP-003", "Ana Cruz",          63800.75,  8,  9800.00, 7975.09,  4, 3190.04, "2006-08-09"),
    ("REP-004", "Carlos Dela Rosa",  21500.00,  4,  7500.00, 5375.00,  3, 1075.00, "2006-08-09"),
    ("REP-005", "Elena Villanueva",  87400.25, 17, 12400.00, 5141.19,  7, 4370.01, "2006-08-09"),
    ("REP-006", "Ramon Gutierrez",   34200.00,  6,  8200.00, 5700.00,  4, 1710.00, "2006-08-09"),
    ("REP-007", "Luz Mendoza",      112000.00, 14, 16500.00, 8000.00,  6, 5600.00, "2006-08-09"),
    ("REP-008", "Pedro Bautista",     8900.00,  2,  5500.00, 4450.00,  2,  445.00, "2006-08-09"),
]


class WeeklySalesReportView(ctk.CTkScrollableFrame):
    """
    Weekly Sales Report — full-width, matches Inventory page layout.
    Drop into main.py show_reports() exactly like CustomersView.
    """

    def __init__(self, parent, controller=None, db_config=None, **kwargs):
        super().__init__(parent, fg_color=PAGE_BG, corner_radius=0,
                         border_width=0, **kwargs)
        self.controller  = controller
        self.db_config   = db_config
        self._all_rows   = []
        self._week_end   = "2006-08-09"
        self._active_tab = tk.StringVar(value="overview")
        self._show_high  = False          # toggle state for >10 invoices

        self.columnconfigure(0, weight=1)

        self._build_header()        # row 0
        self._build_kpi_strip()     # row 1
        self._build_filter_bar()    # row 2
        self._build_tab_section()   # row 3

        self.load_data()

    # ════════════════════════════════════════════════════════════════════
    # 1. Header  (title left, Print + Export CSV right)
    # ════════════════════════════════════════════════════════════════════
    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 0))
        hdr.columnconfigure(0, weight=1)

        # Left — title block
        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(left, text="Weekly Sales Report",
                     font=FONT_TITLE, text_color=TEXT_DARK
                     ).pack(anchor="w")
        self._subtitle = ctk.CTkLabel(
            left,
            text=(f"Week ending  {self._week_end}"
                  "  ·  National Office Supplies"),
            font=FONT_SUB, text_color=TEXT_MUTED
        )
        self._subtitle.pack(anchor="w", pady=(2, 0))

        # Right — action buttons
        right = ctk.CTkFrame(hdr, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            right, text="🖨  Print", width=100, height=36,
            corner_radius=8, fg_color=CARD_BG,
            text_color=TEXT_DARK, hover_color="#f0f0f0",
            border_width=1, border_color=BORDER,
            font=FONT_BODY
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            right, text="⬇  Export CSV", width=140, height=36,
            corner_radius=8, fg_color=TAB_ACTIVE,
            hover_color="#151f2e", text_color=TEXT_WHITE,
            font=FONT_BTN, command=self._export_csv
        ).pack(side="left")

    # ════════════════════════════════════════════════════════════════════
    # 2. KPI cards  (4 across, matching inventory card style exactly)
    # ════════════════════════════════════════════════════════════════════
    def _build_kpi_strip(self):
        strip = ctk.CTkFrame(self, fg_color="transparent")
        strip.grid(row=1, column=0, sticky="ew", padx=28, pady=(20, 0))
        strip.columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")

        self._kpi_cards = {}
        specs = [
            ("total_reps",    "0",    "Total Reps",       "Active this week",      C_BLUE,  "👤"),
            ("top_invoices",  "0",    "Top Invoices",     "Highest invoice count", C_GREEN, "✅"),
            ("total_invoices","0",    "Total Invoices",   "All reps combined",     C_AMBER, "📋"),
            ("total_comm",    "₱0",   "Commissions Due",  "5% of gross sales",     C_RED,   "💰"),
        ]
        for col, (key, val, label, sub, colour, icon) in enumerate(specs):
            card = self._make_kpi_card(strip, val, label, sub, colour, icon)
            card.grid(row=0, column=col, sticky="nsew",
                      padx=(0 if col == 0 else 12, 0))
            self._kpi_cards[key] = card

    def _make_kpi_card(self, parent, value, label, subtitle, colour, icon):
        """Single KPI card — white, rounded, left-icon, big coloured number."""
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=18)

        # icon row
        ctk.CTkLabel(inner, text=icon, font=("Segoe UI", 22),
                     text_color="#c0c8d8").pack(anchor="w")

        # big number
        num_lbl = ctk.CTkLabel(inner, text=value,
                               font=FONT_CARD_NUM, text_color=colour)
        num_lbl.pack(anchor="w", pady=(4, 0))

        # label + subtitle
        ctk.CTkLabel(inner, text=label, font=FONT_CARD_LBL,
                     text_color=TEXT_DARK).pack(anchor="w")
        ctk.CTkLabel(inner, text=subtitle, font=FONT_CARD_SUB,
                     text_color=TEXT_MUTED).pack(anchor="w")

        # store reference to number label for live update
        card._num_lbl = num_lbl
        return card

    def _update_kpi(self, rows):
        if not rows:
            return
        total_reps    = len(rows)
        max_inv       = max(int(r[3]) for r in rows)
        total_inv     = sum(int(r[3])   for r in rows)
        total_comm    = sum(float(r[7]) for r in rows)

        self._kpi_cards["total_reps"]._num_lbl.configure(
            text=str(total_reps))
        self._kpi_cards["top_invoices"]._num_lbl.configure(
            text=str(max_inv))
        self._kpi_cards["total_invoices"]._num_lbl.configure(
            text=str(total_inv))
        self._kpi_cards["total_comm"]._num_lbl.configure(
            text=f"₱{total_comm:,.0f}")

    # ════════════════════════════════════════════════════════════════════
    # 3. Filter bar  (search + week picker + toggle + record count)
    # ════════════════════════════════════════════════════════════════════
    def _build_filter_bar(self):
        bar = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10,
                           border_width=1, border_color=BORDER)
        bar.grid(row=2, column=0, sticky="ew", padx=28, pady=(20, 0))
        bar.columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=10)

        # Search icon + entry
        ctk.CTkLabel(inner, text="🔍", font=("Segoe UI", 15),
                     text_color=TEXT_MUTED).pack(side="left")

        self._search_var = ctk.StringVar()
        ctk.CTkEntry(
            inner, textvariable=self._search_var,
            placeholder_text="Search rep name or ID…",
            width=240, height=34, corner_radius=6,
            fg_color=SEARCH_BG, text_color=TEXT_DARK,
            placeholder_text_color=TEXT_MUTED,
            border_color=BORDER, border_width=1,
            font=FONT_BODY
        ).pack(side="left", padx=(6, 20))
        self._search_var.trace_add("write", lambda *_: self._apply_filter())

        # Week ending label + entry
        ctk.CTkLabel(inner, text="Week ending:",
                     font=FONT_BODY, text_color=TEXT_MUTED
                     ).pack(side="left")
        self._week_var = ctk.StringVar(value=self._week_end)
        ctk.CTkEntry(
            inner, textvariable=self._week_var,
            width=110, height=34, corner_radius=6,
            fg_color=SEARCH_BG, text_color=TEXT_DARK,
            border_color=BORDER, border_width=1,
            font=FONT_BODY
        ).pack(side="left", padx=(6, 6))
        ctk.CTkButton(
            inner, text="Load", width=60, height=34,
            corner_radius=6, fg_color=C_BLUE,
            hover_color="#2563eb", text_color=TEXT_WHITE,
            font=FONT_BTN, command=self._load_week
        ).pack(side="left", padx=(0, 20))

        # >10 invoices toggle
        ctk.CTkLabel(inner, text=">10 Invoices Only:",
                     font=FONT_BODY, text_color=TEXT_MUTED
                     ).pack(side="left")
        self._high_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            inner, text="", variable=self._high_var,
            width=30, fg_color=C_AMBER, hover_color="#d97706",
            command=self._apply_filter
        ).pack(side="left", padx=(6, 0))

        # Record count (right-aligned)
        self._count_lbl = ctk.CTkLabel(
            inner, text="0 records",
            font=FONT_SMALL, text_color=TEXT_MUTED
        )
        self._count_lbl.pack(side="right")

    # ════════════════════════════════════════════════════════════════════
    # 4. Tab bar + table content
    # ════════════════════════════════════════════════════════════════════
    def _build_tab_section(self):
        self._tab_btns    = {}
        self._tab_frames  = {}

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.grid(row=3, column=0, sticky="ew", padx=28, pady=(20, 28))
        wrapper.columnconfigure(0, weight=1)

        # ── Tab pill bar ──────────────────────────────────────────────
        tab_bar = ctk.CTkFrame(wrapper, fg_color="transparent")
        tab_bar.grid(row=0, column=0, sticky="w", pady=(0, 10))

        tabs = [
            ("overview",  "📊  Rep Overview"),
            ("ytd",       "📈  Year-to-Date"),
            ("top10",     "🏆  > 10 Invoices"),
        ]
        for key, label in tabs:
            btn = ctk.CTkButton(
                tab_bar, text=label,
                width=190, height=38, corner_radius=8,
                fg_color=TAB_INACTIVE,
                text_color=TEXT_MUTED, hover_color="#e8eaed",
                font=FONT_TAB_IN,
                command=lambda k=key: self._switch_tab(k)
            )
            btn.pack(side="left", padx=(0, 8))
            self._tab_btns[key] = btn

        # ── Tab content frames ────────────────────────────────────────
        content = ctk.CTkFrame(wrapper, fg_color="transparent")
        content.grid(row=1, column=0, sticky="ew")
        content.columnconfigure(0, weight=1)

        self._tab_frames["overview"] = self._build_overview_tab(content)
        self._tab_frames["ytd"]      = self._build_ytd_tab(content)
        self._tab_frames["top10"]    = self._build_top10_tab(content)

        self._switch_tab("overview")

    def _switch_tab(self, key: str):
        for k, btn in self._tab_btns.items():
            if k == key:
                btn.configure(
                    fg_color=TAB_ACTIVE, text_color=TEXT_WHITE,
                    font=FONT_TAB_ACT, hover_color=TAB_ACTIVE
                )
            else:
                btn.configure(
                    fg_color=TAB_INACTIVE, text_color=TEXT_MUTED,
                    font=FONT_TAB_IN, hover_color="#e8eaed"
                )
        for k, frame in self._tab_frames.items():
            if k == key:
                frame.grid(row=0, column=0, sticky="ew")
            else:
                frame.grid_remove()
        self._active_tab.set(key)

    # ── Tab 1 : Rep Overview ──────────────────────────────────────────
    def _build_overview_tab(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12,
                             border_width=1, border_color=BORDER)
        frame.columnconfigure(0, weight=1)

        cols  = ("Rep ID", "Sales Rep Name", "Total Sales (₱)",
                 "# Invoices", "Largest Sale (₱)", "Avg Sale (₱)",
                 "# Customers", "Commission (₱)", "Week Ending")
        widths= (85,  180, 130, 90, 130, 110, 100, 120, 110)

        self._overview_tree = self._make_treeview(frame, cols, widths, row=0)
        # tag colours match inventory row colouring
        self._overview_tree.tag_configure(
            "high",   foreground=C_ROW_HIGH,
            font=("Segoe UI", 11, "bold"))
        self._overview_tree.tag_configure(
            "top",    foreground=C_ROW_TOP,
            font=("Segoe UI", 11, "bold"))
        self._overview_tree.tag_configure(
            "zero",   foreground=C_ROW_ZERO,
            font=("Segoe UI", 11, "bold"))
        self._overview_tree.tag_configure(
            "normal", foreground=C_ROW_NORMAL)
        self._overview_tree.tag_configure(
            "alt",    foreground=C_ROW_NORMAL, background=ROW_ALT)
        return frame

    # ── Tab 2 : Year-to-Date ──────────────────────────────────────────
    def _build_ytd_tab(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12,
                             border_width=1, border_color=BORDER)
        frame.columnconfigure(0, weight=1)

        # info banner
        banner = ctk.CTkFrame(frame, fg_color="#eff6ff", corner_radius=8)
        banner.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            banner,
            text="📈  Year-to-date totals per rep  —  QD-Sec 8 / 9",
            font=FONT_SMALL, text_color="#1d4ed8"
        ).pack(anchor="w", padx=10, pady=7)

        cols  = ("Rep ID", "Rep Name", "YTD Sales (₱)", "YTD Invoices",
                 "Largest Sale (₱)", "Avg Sale (₱)", "# Customers",
                 "YTD Commission (₱)")
        widths= (85, 180, 130, 110, 130, 110, 100, 140)

        self._ytd_tree = self._make_treeview(frame, cols, widths, row=1)
        self._ytd_tree.tag_configure(
            "top",    foreground=C_ROW_TOP,
            font=("Segoe UI", 11, "bold"))
        self._ytd_tree.tag_configure(
            "normal", foreground=C_ROW_NORMAL)
        self._ytd_tree.tag_configure(
            "alt",    foreground=C_ROW_NORMAL, background=ROW_ALT)
        return frame

    # ── Tab 3 : > 10 Invoices  (QD-Sec 12) ───────────────────────────
    def _build_top10_tab(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12,
                             border_width=1, border_color=BORDER)
        frame.columnconfigure(0, weight=1)

        banner = ctk.CTkFrame(frame, fg_color="#fffbeb", corner_radius=8)
        banner.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            banner,
            text="🏆  Sales reps who wrote more than 10 invoices  —  QD-Sec 12",
            font=FONT_SMALL, text_color="#92400e"
        ).pack(anchor="w", padx=10, pady=7)

        cols  = ("Rep ID", "Rep Name", "# Invoices",
                 "Total Sales (₱)", "Commission (₱)", "Week Ending")
        widths= (85, 220, 100, 150, 130, 120)

        self._top10_tree = self._make_treeview(frame, cols, widths, row=1)
        self._top10_tree.tag_configure(
            "high",  foreground=C_ROW_HIGH,
            font=("Segoe UI", 11, "bold"))
        return frame

    # ════════════════════════════════════════════════════════════════════
    # Shared treeview factory  (dark navy header — identical to inventory)
    # ════════════════════════════════════════════════════════════════════
    def _make_treeview(self, parent, cols, widths, row: int) -> ttk.Treeview:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "NOS.Treeview",
            background=TABLE_BG, foreground=C_ROW_NORMAL,
            fieldbackground=TABLE_BG, rowheight=32,
            font=FONT_TBL_ROW, borderwidth=0,
        )
        style.configure(
            "NOS.Treeview.Heading",
            background=TABLE_HDR_BG, foreground=TEXT_WHITE,
            font=FONT_TBL_HDR, relief="flat", padding=(10, 8),
        )
        style.map("NOS.Treeview",
                  background=[("selected", "#dbeafe")],
                  foreground=[("selected", "#1d4ed8")])
        style.map("NOS.Treeview.Heading",
                  background=[("active", "#253d52")])

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=0, sticky="nsew",
                       padx=16, pady=(4, 16))
        container.columnconfigure(0, weight=1)

        vsb = ttk.Scrollbar(container, orient="vertical")
        hsb = ttk.Scrollbar(container, orient="horizontal")

        tree = ttk.Treeview(
            container, columns=cols, show="headings",
            style="NOS.Treeview",
            yscrollcommand=vsb.set, xscrollcommand=hsb.set,
            height=14
        )
        vsb.configure(command=tree.yview)
        hsb.configure(command=tree.xview)

        for col, w in zip(cols, widths):
            tree.heading(col, text=col,
                         command=lambda c=col: self._sort(tree, c, False))
            anchor = "e" if any(x in col for x in
                                ("₱", "#", "Sales", "Invoice", "Comm",
                                 "Customer", "Largest", "Avg", "YTD")
                                ) else "w"
            tree.column(col, width=w, minwidth=55, anchor=anchor)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        return tree

    # ════════════════════════════════════════════════════════════════════
    # Data loading & population
    # ════════════════════════════════════════════════════════════════════
    def load_data(self):
        rows = self._fetch_from_db() if (self.db_config and HAS_PSYCOPG2) \
               else list(SAMPLE_ROWS)
        self._all_rows = rows
        self._apply_filter()          # populates all three trees + KPIs

    def _fetch_from_db(self):
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        sr.rep_id,
                        e.emp_name,
                        COALESCE(SUM(i.total_amount),  0)          AS total_sales,
                        COUNT(i.invoice_id)                        AS num_invoices,
                        COALESCE(MAX(i.total_amount),  0)          AS largest_sale,
                        COALESCE(AVG(i.total_amount),  0)          AS avg_sale,
                        COUNT(DISTINCT i.customer_id)              AS num_customers,
                        COALESCE(SUM(i.total_amount),  0) * 0.05   AS commission,
                        %s::date
                    FROM salesrep sr
                    JOIN employee e   ON e.emp_id  = sr.emp_id
                    LEFT JOIN invoice i ON i.rep_id = sr.rep_id
                        AND i.invoice_date <= %s::date
                        AND i.invoice_date >  %s::date - INTERVAL '7 days'
                    GROUP BY sr.rep_id, e.emp_name
                    ORDER BY total_sales DESC
                """, (self._week_end,) * 3)
                return cur.fetchall()
        except Exception as ex:
            messagebox.showerror(
                "Database Error",
                f"Could not load weekly sales data:\n{ex}\n\n"
                "Showing sample data.")
            return list(SAMPLE_ROWS)

    def _apply_filter(self):
        q        = self._search_var.get().strip().lower() \
                   if hasattr(self, "_search_var") else ""
        only_high = self._high_var.get() \
                    if hasattr(self, "_high_var") else False

        filtered = [
            r for r in self._all_rows
            if (not q or q in str(r[0]).lower() or q in str(r[1]).lower())
            and (not only_high or int(r[3]) > 10)
        ]

        self._populate_overview(filtered)
        self._populate_ytd(filtered)
        self._populate_top10(filtered)
        self._update_kpi(filtered)

        if hasattr(self, "_count_lbl"):
            self._count_lbl.configure(text=f"{len(filtered)} records")

    def _populate_overview(self, rows):
        t = self._overview_tree
        t.delete(*t.get_children())
        max_sales = max((float(r[2]) for r in rows), default=1)
        for idx, r in enumerate(rows):
            rep_id, name, total, inv, largest, avg, cust, comm, week = r
            total_f = float(total)
            inv_i   = int(inv)
            if inv_i > 10:
                tag = "high"
            elif total_f >= max_sales * 0.9:
                tag = "top"
            elif total_f == 0:
                tag = "zero"
            elif idx % 2:
                tag = "alt"
            else:
                tag = "normal"
            t.insert("", "end", tags=(tag,),
                     values=(rep_id, name,
                             f"{total_f:,.2f}", inv_i,
                             f"{float(largest):,.2f}",
                             f"{float(avg):,.2f}",
                             int(cust),
                             f"{float(comm):,.2f}",
                             week))

    def _populate_ytd(self, rows):
        t = self._ytd_tree
        t.delete(*t.get_children())
        # For YTD: multiply weekly figures as a demo (replace with real YTD query)
        max_sales = max((float(r[2]) for r in rows), default=1)
        for idx, r in enumerate(rows):
            rep_id, name, total, inv, largest, avg, cust, comm, _ = r
            ytd_sales = float(total) * 4          # demo multiplier
            ytd_inv   = int(inv) * 4
            ytd_comm  = ytd_sales * 0.05
            tag = "top" if ytd_sales >= max_sales * 4 * 0.9 \
                  else ("alt" if idx % 2 else "normal")
            t.insert("", "end", tags=(tag,),
                     values=(rep_id, name,
                             f"{ytd_sales:,.2f}", ytd_inv,
                             f"{float(largest):,.2f}",
                             f"{float(avg):,.2f}",
                             int(cust),
                             f"{ytd_comm:,.2f}"))

    def _populate_top10(self, rows):
        t = self._top10_tree
        t.delete(*t.get_children())
        high = [r for r in rows if int(r[3]) > 10]
        for r in sorted(high, key=lambda x: int(x[3]), reverse=True):
            rep_id, name, total, inv, *_, comm, week = r
            t.insert("", "end", tags=("high",),
                     values=(rep_id, name, int(inv),
                             f"{float(total):,.2f}",
                             f"{float(comm):,.2f}",
                             week))

    # ════════════════════════════════════════════════════════════════════
    # Sorting, week load, export
    # ════════════════════════════════════════════════════════════════════
    def _sort(self, tree: ttk.Treeview, col: str, reverse: bool):
        data = [(tree.set(k, col), k) for k in tree.get_children("")]
        try:
            data.sort(
                key=lambda t: float(t[0].replace(",", "").replace("₱", "")),
                reverse=reverse)
        except ValueError:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)
        for i, (_, k) in enumerate(data):
            tree.move(k, "", i)
        tree.heading(col, command=lambda: self._sort(tree, col, not reverse))

    def _load_week(self):
        self._week_end = self._week_var.get().strip() or self._week_end
        if hasattr(self, "_subtitle"):
            self._subtitle.configure(
                text=(f"Week ending  {self._week_end}"
                      "  ·  National Office Supplies"))
        self.load_data()

    def _export_csv(self):
        import csv
        import tkinter.filedialog as fd
        path = fd.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"weekly_sales_{self._week_end}.csv"
        )
        if not path:
            return
        headers = ("Rep ID", "Rep Name", "Total Sales", "# Invoices",
                   "Largest Sale", "Avg Sale", "# Customers",
                   "Commission", "Week Ending")
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(headers)
                for iid in self._overview_tree.get_children():
                    w.writerow(self._overview_tree.item(iid, "values"))
            messagebox.showinfo("Export Complete", f"Saved to:\n{path}")
        except Exception as ex:
            messagebox.showerror("Export Failed", str(ex))
