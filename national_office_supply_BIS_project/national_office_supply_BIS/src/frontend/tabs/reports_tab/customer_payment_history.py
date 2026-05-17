"""
customer_payment_history.py
National Office Supplies BIS — Customer Payment History Report
Tracks payment timeline and amount changes per customer account.

Columns:
    Payment ID | Customer No. | Company | Invoice No. | Payment Date
    | Amount Paid | Method | Balance After
"""

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
from .csv_tab import export_customer_payments

# ── Shared colour palette ─────────────────────────────────────────────────────
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

FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_BODY = ("Segoe UI", 12)
FONT_BTN = ("Segoe UI", 12, "bold")
FONT_SMALL = ("Segoe UI", 10)
FONT_TABLE = ("Segoe UI", 11)


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


class CustomerPaymentHistoryView(ctk.CTkFrame):
    """
    Customer Payment History
    ─────────────────────────
    Single table — every row in customer_payments:
        Payment ID | Customer No. | Company | Invoice No. | Payment Date
        | Amount Paid | Method | Balance After
    """

    # ── Sample data (used when db_config is None) ────────────────────────────
    _SAMPLE_CUSTOMERS = {
        1: ("C-1001", "Horizon School Inc."),
        2: ("C-1002", "Metro Academy"),
        3: ("C-1003", "Sunrise Daycare"),
        4: ("C-1004", "Greenleaf Montessori"),
        5: ("C-1005", "Capitol College"),
        6: ("C-1006", "Northern Stars School"),
        7: ("C-1007", "Pacific Learning Hub"),
    }

    _SAMPLE_PAYMENTS = (
        # pay_id | cust_no | inv_id      | pay_date       | amount     | method     | bal_after
        (1, 1, "INV-2001", "2006-07-20", 8_400.00, "check", 15_420.00),
        (2, 1, "INV-2002", "2006-08-01", 12_000.00, "transfer", 15_420.00),
        (3, 2, "INV-2004", "2006-08-10", 3_800.00, "cash", 0.00),
        (4, 3, "INV-2005", "2006-08-12", 11_500.00, "check", 0.00),
        (5, 4, None, "2006-08-15", 5_000.00, "transfer", 26_075.00),
        (6, 5, "INV-2007", "2006-07-01", 34_500.00, "check", 0.00),
        (7, 5, "INV-2008", "2006-08-05", 33_400.00, "check", 0.00),
        (8, 6, "INV-2009", "2006-08-02", 8_500.00, "cash", 9_250.00),
        (9, 6, "INV-2010", "2006-08-09", 16_250.00, "transfer", 9_250.00),
        (10, 7, "INV-2012", "2006-06-01", 5_800.00, "check", 0.00),
        (11, 1, None, "2006-08-20", 2_000.00, "cash", 13_420.00),
        (12, 4, "INV-2006", "2006-08-22", 10_000.00, "transfer", 16_075.00),
    )

    def __init__(
        self,
        parent,
        controller=None,
        db_config=None,
        on_toggle_navigation=None,
        is_navigation_visible=True,
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

        self.customers = self._load_customers()
        self.payments = self._load_payments()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(self, bg=BG_PAGE, highlightthickness=0)
        self._vsb = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vsb.set)
        self._vsb.grid(row=0, column=1, sticky="ns")
        self._canvas.grid(row=0, column=0, sticky="nsew")

        self._body = tk.Frame(self._canvas, bg=BG_PAGE)
        self._body_id = self._canvas.create_window(
            (0, 0), window=self._body, anchor="nw"
        )

        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfig(self._body_id, width=e.width),
        )
        self._body.bind(
            "<Configure>",
            lambda _e: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        self._canvas.bind_all(
            "<MouseWheel>",
            lambda e: self._canvas.yview_scroll(int(-1 * e.delta / 120), "units"),
        )

        self._build_header()
        self._build_summary_strip()
        self._build_filter_bar()
        self._build_table()

    def set_navigation_visibility(self, visible: bool):
        self._is_navigation_visible = visible
        if hasattr(self, "_nav_toggle_btn"):
            self._nav_toggle_btn.configure(text="◀" if visible else "▶")

    def _row_value(self, row, key: str, index: int, default=None):
        if isinstance(row, dict):
            return row.get(key, default)
        if row is None:
            return default
        try:
            return row[index]
        except Exception:
            return default

    def _as_customer_row(self, row):
        customer_number = self._row_value(row, "customer_number", 0)
        customer_label = self._row_value(row, "cust_no", 1)
        company_name = self._row_value(row, "company_name", 2, "")
        return customer_number, customer_label, company_name

    def _as_payment_row(self, row):
        payment_id = self._row_value(row, "payment_id", 0)
        customer_number = self._row_value(row, "customer_number", 1)
        invoice_id = self._row_value(row, "invoice_id", 2)
        payment_date = self._row_value(row, "payment_date", 3)
        amount_paid = self._row_value(row, "amount_paid", 4, 0)
        payment_method = self._row_value(row, "payment_method", 5, "")
        balance_after = self._row_value(row, "balance_after", 6, None)
        return (
            payment_id,
            customer_number,
            invoice_id,
            payment_date,
            amount_paid,
            payment_method,
            balance_after,
        )

    # ── Data loaders ──────────────────────────────────────────────────────────
    def _load_customers(self) -> dict:
        if not self._report_service or not self.db_config:
            return dict(self._SAMPLE_CUSTOMERS)
        try:
            rows = self._report_service.execute_query("""
                SELECT customer_number,
                       LPAD(customer_number::text, 4, '0') AS cust_no,
                       company_name
                FROM   customers
                ORDER  BY customer_number
            """)
            return (
                {
                    r["customer_number"]: (f"C-{r['cust_no']}", r["company_name"])
                    for r in rows
                }
                if rows
                else dict(self._SAMPLE_CUSTOMERS)
            )
        except Exception as e:
            print(f"[CustomerPaymentHistory] _load_customers failed: {e}")
            return dict(self._SAMPLE_CUSTOMERS)

    def _load_payments(self) -> list:
        if not self._report_service or not self.db_config:
            return list(self._SAMPLE_PAYMENTS)
        try:
            rows = self._report_service.execute_query("""
                SELECT
                    cp.payment_id,
                    cp.customer_number,
                    cp.invoice_id,
                    cp.payment_date,
                    cp.amount_paid,
                    cp.payment_method,
                    c.current_balance + COALESCE(
                        SUM(cp.amount_paid) OVER (
                            PARTITION BY cp.customer_number
                            ORDER BY cp.payment_date ASC, cp.payment_id ASC
                            ROWS BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING
                        ), 0
                    ) AS balance_after
                FROM   customer_payments cp
                JOIN   customers c ON c.customer_number = cp.customer_number
                ORDER  BY cp.payment_date DESC, cp.payment_id DESC
            """)
            return rows if rows else list(self._SAMPLE_PAYMENTS)
        except Exception as e:
            print(f"[CustomerPaymentHistory] _load_payments failed: {e}")
            return list(self._SAMPLE_PAYMENTS)

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = ctk.CTkFrame(self._body, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(25, 0))

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left")

        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.pack(anchor="w")

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
            title_row,
            text="Customer Payment History",
            font=FONT_TITLE,
            text_color=TEXT_DARK,
        ).pack(side="left")

        ctk.CTkLabel(
            left,
            text=f"As of  {datetime.date.today().strftime('%B %d, %Y')}  ·  National Office Supplies",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        right = ctk.CTkFrame(hdr, fg_color="transparent")
        right.pack(side="right")

        ctk.CTkButton(
            right,
            text="⬇  Export CSV",
            width=140,
            height=36,
            corner_radius=8,
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
            height=36,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#e8f4fd",
            text_color=BRAND_BLUE,
            border_width=1,
            border_color=BRAND_BLUE,
            font=FONT_BODY,
            command=self._refresh_data,
        ).pack(side="right", padx=(0, 10))

    def _handle_nav_toggle(self):
        if self._on_toggle_navigation:
            self._on_toggle_navigation()

    # ── Summary strip ─────────────────────────────────────────────────────────
    def _build_summary_strip(self):
        strip = ctk.CTkFrame(self._body, fg_color="transparent")
        strip.pack(fill="x", padx=30, pady=(20, 0))

        total_received = sum(
            float(self._as_payment_row(p)[4] or 0) for p in self.payments
        )
        payment_count = len(self.payments)
        check_count = sum(
            1 for p in self.payments if self._as_payment_row(p)[5] == "check"
        )
        general_count = sum(
            1 for p in self.payments if self._as_payment_row(p)[2] is None
        )

        cards = [
            (
                "Total Received",
                f"₱{total_received:,.2f}",
                "All payments on record",
                "💰",
                ACCENT_GREEN,
            ),
            (
                "Payments Logged",
                str(payment_count),
                "Individual transactions",
                "📋",
                BRAND_BLUE,
            ),
            (
                "Paid by Check",
                str(check_count),
                "Check payment transactions",
                "🖊️",
                BRAND_NAVY,
            ),
            (
                "General Credits",
                str(general_count),
                "Not tied to a specific invoice",
                "💳",
                ACCENT_AMBER,
            ),
        ]

        for i, (title, value, sub, icon, color) in enumerate(cards):
            card = SummaryCard(strip, title, value, sub, icon, color)
            card.pack(side="left", fill="x", expand=True, padx=(0 if i == 0 else 12, 0))

    # ── Filter bar ────────────────────────────────────────────────────────────
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
            placeholder_text="Search by customer, invoice no., or method…",
            width=300,
            height=36,
            corner_radius=6,
            fg_color="#f5f7fa",
            text_color=TEXT_DARK,
            border_color=BORDER,
        ).pack(side="left", padx=(6, 20))
        self._search_var.trace_add("write", lambda *_: self._apply_filter())

        ctk.CTkLabel(inner, text="Method:", font=FONT_BODY, text_color=TEXT_MUTED).pack(
            side="left"
        )
        self._method_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            inner,
            variable=self._method_var,
            values=["All", "check", "cash", "transfer"],
            width=130,
            height=36,
            corner_radius=6,
            fg_color="#f5f7fa",
            button_color=BRAND_BLUE,
            text_color=TEXT_DARK,
            command=lambda _: self._apply_filter(),
        ).pack(side="left", padx=(8, 20))

        ctk.CTkLabel(
            inner, text="Date From:", font=FONT_BODY, text_color=TEXT_MUTED
        ).pack(side="left")
        self._date_from_picker = DatePickerField(inner, width=110)
        self._date_from_picker.pack(side="left", padx=(6, 12))
        self._date_from_picker.entry.bind(
            "<KeyRelease>", lambda *_: self._apply_filter()
        )

        ctk.CTkLabel(inner, text="To:", font=FONT_BODY, text_color=TEXT_MUTED).pack(
            side="left"
        )
        self._date_to_picker = DatePickerField(inner, width=110)
        self._date_to_picker.pack(side="left", padx=(6, 0))
        self._date_to_picker.entry.bind("<KeyRelease>", lambda *_: self._apply_filter())

        self._count_label = ctk.CTkLabel(
            inner,
            text=f"{len(self.payments)} records",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
        )
        self._count_label.pack(side="right")

    def _build_table(self):
        card = ctk.CTkFrame(
            self._body,
            fg_color=BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        card.pack(fill="x", padx=30, pady=(20, 16))
        card.columnconfigure(0, weight=1)

        note = ctk.CTkFrame(card, fg_color="#eaf4fb", corner_radius=8)
        note.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            note,
            text="💰  Chronological log of every payment received — linked to customer and invoice, with balance before and after each transaction.",
            font=FONT_SMALL,
            text_color="#1a5276",
        ).pack(anchor="w", padx=10, pady=6)

        cols = (
            "Pay. ID",
            "Customer No.",
            "Company",
            "Invoice No.",
            "Payment Date",
            "Balance Before",
            "Amount Paid",
            "Method",
            "Balance After",
        )
        widths = (70, 110, 220, 110, 120, 130, 120, 90, 130)

        self._tree = self._make_treeview(card, cols, widths, row=1)
        self._tree.tag_configure("check", foreground=BRAND_NAVY)
        self._tree.tag_configure("cash", foreground="#1e8449")
        self._tree.tag_configure("transfer", foreground=BRAND_BLUE)
        self._tree.tag_configure("general", foreground=ACCENT_AMBER)

        self._populate(self.payments)

    def _populate(self, data: list):
        self._tree.delete(*self._tree.get_children())
        for p in data:
            pay_id, cust_no, inv_id, pay_date, amount, method, bal_after = (
                self._as_payment_row(p)
            )
            cust_label, company = self.customers.get(cust_no, (f"C-{cust_no:04d}", "—"))

            amount_value = float(amount) if amount is not None else 0.0
            balance_after_value = float(bal_after) if bal_after is not None else None

            if isinstance(pay_date, str):
                pay_date_str = pay_date
            elif isinstance(pay_date, (datetime.date, datetime.datetime)):
                d = pay_date if isinstance(pay_date, datetime.date) else pay_date.date()
                pay_date_str = d.strftime("%Y-%m-%d")
            else:
                pay_date_str = str(pay_date)

            inv_label = str(inv_id) if inv_id else "— (General)"
            tag = method if method in ("check", "cash", "transfer") else "general"
            if inv_id is None:
                tag = "general"

            bal_before = (
                (balance_after_value + amount_value)
                if balance_after_value is not None
                else None
            )
            self._tree.insert(
                "",
                "end",
                values=(
                    f"#{pay_id}",
                    cust_label,
                    company,
                    inv_label,
                    pay_date_str,
                    f"₱{bal_before:,.2f}" if bal_before is not None else "—",
                    f"₱{amount_value:,.2f}",
                    method.title() if method else "—",
                    (
                        f"₱{balance_after_value:,.2f}"
                        if balance_after_value is not None
                        else "—"
                    ),
                ),
                tags=(tag,),
            )
        self._count_label.configure(text=f"{len(data)} records")

    # ── Shared treeview factory ───────────────────────────────────────────────
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
            height=14,
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

    # ── Column sorting ────────────────────────────────────────────────────────
    def _sort_column(self, tree: ttk.Treeview, col: str, reverse: bool):
        data = [(tree.set(iid, col), iid) for iid in tree.get_children("")]
        try:
            data.sort(
                key=lambda t: float(t[0].replace("₱", "").replace(",", "").strip()),
                reverse=reverse,
            )
        except ValueError:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)
        for idx, (_, iid) in enumerate(data):
            tree.move(iid, "", idx)
        tree.heading(col, command=lambda: self._sort_column(tree, col, not reverse))

    # ── Filter ────────────────────────────────────────────────────────────────
    def _apply_filter(self):
        query = self._search_var.get().lower()
        method = self._method_var.get()
        d_from = self._date_from_picker.get_value().strip()
        d_to = self._date_to_picker.get_value().strip()

        def parse_date(s: str):
            try:
                return datetime.date.fromisoformat(s)
            except ValueError:
                return None

        dt_from = parse_date(d_from)
        dt_to = parse_date(d_to)

        filtered = []
        for p in self.payments:
            pay_id, cust_no, inv_id, pay_date, amount, pmeth, bal = (
                self._as_payment_row(p)
            )
            cust_label, company = self.customers.get(cust_no, (str(cust_no), ""))

            if isinstance(pay_date, str):
                try:
                    pay_dt = datetime.date.fromisoformat(pay_date)
                except ValueError:
                    pay_dt = None
            elif isinstance(pay_date, (datetime.date, datetime.datetime)):
                pay_dt = (
                    pay_date if isinstance(pay_date, datetime.date) else pay_date.date()
                )
            else:
                pay_dt = None

            if query and not any(
                query in str(v).lower()
                for v in (cust_label, company, inv_id or "", pmeth or "")
            ):
                continue
            if method != "All" and pmeth != method:
                continue
            if dt_from and pay_dt and pay_dt < dt_from:
                continue
            if dt_to and pay_dt and pay_dt > dt_to:
                continue
            filtered.append(p)

        self._populate(filtered)

    # ── Refresh ───────────────────────────────────────────────────────────────
    def _refresh_data(self):
        self.payments = self._load_payments()
        self._populate(self.payments)

    # ── CSV export ────────────────────────────────────────────────────────────
    def _export_csv(self):
        headers = [self._tree.heading(c)["text"] for c in self._tree["columns"]]
        rows = [self._tree.item(iid, "values") for iid in self._tree.get_children()]
        export_customer_payments(self, rows, headers)
