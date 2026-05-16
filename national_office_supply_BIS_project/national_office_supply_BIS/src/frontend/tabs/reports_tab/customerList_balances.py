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
from .csv_tab import export_customer_balances

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


class CustomerListReportView(ctk.CTkFrame):
    """
    Customer List & Balances
    ─────────────────────────
    Tab 1 — Customer List
        Cust No. | Company | Address | Phone | Current Balance | Status
        (Assumption 15 + Assumption 1 balance)

    Tab 2 — Account Balances
        Cust No. | Company | Invoice No. | Invoice Date | Amount Due | Paid? | Shipped?
        (Assumption 1 track payments + Assumption 2 shipped + Assumption 3 paid)
    """

    _SAMPLE_CUSTOMERS = (
        # cust_no | company                   | address                   | phone          | balance   | status
        (
            "C-1001",
            "Horizon School Inc.",
            "12 Mabini St, QC",
            "02-8100-0001",
            15_420.00,
            "Active",
        ),
        (
            "C-1002",
            "Metro Academy",
            "45 Rizal Ave, Manila",
            "02-8100-0002",
            3_800.00,
            "Active",
        ),
        (
            "C-1003",
            "Sunrise Daycare",
            "7 Luna St, Pasig",
            "02-8100-0003",
            0.00,
            "Active",
        ),
        (
            "C-1004",
            "Greenleaf Montessori",
            "88 Katipunan, QC",
            "02-8100-0004",
            31_075.00,
            "New",
        ),
        (
            "C-1005",
            "Capitol College",
            "3 Pres. Quirino, Mla",
            "02-8100-0005",
            0.00,
            "Active",
        ),
        (
            "C-1006",
            "Northern Stars School",
            "21 Baler St, Aurora",
            "044-800-0001",
            9_250.00,
            "Active",
        ),
        (
            "C-1007",
            "Pacific Learning Hub",
            "15 Shaw Blvd, Mandaluyong",
            "02-8100-0006",
            0.00,
            "Inactive",
        ),
    )

    _SAMPLE_INVOICES = (
        # inv_no   | cust_no  | date         | amount     | paid  | shipped
        ("I-2001", "C-1001", "2006-07-15", 8_400.00, True, True),
        ("I-2002", "C-1001", "2006-07-28", 12_000.00, True, True),
        ("I-2003", "C-1001", "2006-08-05", 15_420.00, False, True),
        ("I-2004", "C-1002", "2006-07-20", 3_800.00, False, True),
        ("I-2005", "C-1003", "2006-08-01", 11_500.00, True, True),
        ("I-2006", "C-1004", "2006-08-07", 31_075.00, False, False),
        ("I-2007", "C-1005", "2006-06-10", 34_500.00, True, True),
        ("I-2008", "C-1005", "2006-07-30", 33_400.00, True, True),
        ("I-2009", "C-1006", "2006-07-25", 8_500.00, True, True),
        ("I-2010", "C-1006", "2006-08-03", 16_250.00, True, True),
        ("I-2011", "C-1006", "2006-08-08", 9_250.00, False, True),
        ("I-2012", "C-1007", "2006-05-12", 5_800.00, True, True),
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
        self.invoices = self._load_invoices()

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
        self._build_tabs()

    def set_navigation_visibility(self, visible: bool):
        self._is_navigation_visible = visible
        if hasattr(self, "_nav_toggle_btn"):
            self._nav_toggle_btn.configure(text="◀" if visible else "▶")

    # ── Data loaders ──────────────────────────────────────────────────────────
    def _load_customers(self):
        if not self._report_service or not self.db_config:
            return list(self._SAMPLE_CUSTOMERS)
        try:
            rows = self._report_service.execute_query("""
                SELECT
                    customer_number,
                    company_name,
                    address,
                    phone_number,
                    COALESCE(current_balance, 0) AS balance,
                    CASE WHEN is_active THEN 'Active' ELSE 'Inactive' END AS status
                FROM   customers
                ORDER  BY company_name
            """)
            return rows if rows else list(self._SAMPLE_CUSTOMERS)
        except Exception as e:
            print(f"[CustomerList] _load_customers failed: {e}")
            return list(self._SAMPLE_CUSTOMERS)

    def _load_invoices(self):
        if not self._report_service or not self.db_config:
            return list(self._SAMPLE_INVOICES)
        try:
            rows = self._report_service.execute_query("""
                SELECT
                    invoice_id,
                    customer_number,
                    date_written,
                    COALESCE(total_amount, 0) AS total_amount,
                    CASE WHEN status = 'paid' THEN TRUE ELSE FALSE END AS is_paid,
                    CASE WHEN status IN ('shipped','paid') THEN TRUE ELSE FALSE END AS is_closed
                FROM   invoices
                ORDER  BY date_written DESC
            """)
            return rows if rows else list(self._SAMPLE_INVOICES)
        except Exception as e:
            print(f"[CustomerList] _load_invoices failed: {e}")
            return list(self._SAMPLE_INVOICES)

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
            text="Customer List & Balances",
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
        if callable(self._on_toggle_navigation):
            self._on_toggle_navigation()

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
        company_name = self._row_value(row, "company_name", 1, "")
        address = self._row_value(row, "address", 2, "")
        phone_number = self._row_value(row, "phone_number", 3, "")
        balance = self._row_value(row, "balance", 4, 0)
        status = self._row_value(row, "status", 5, "Active")
        return customer_number, company_name, address, phone_number, balance, status

    def _as_invoice_row(self, row):
        invoice_id = self._row_value(row, "invoice_id", 0)
        customer_number = self._row_value(row, "customer_number", 1)
        invoice_date = self._row_value(row, "date_written", 2)
        amount = self._row_value(row, "total_amount", 3, 0)
        is_paid = self._row_value(row, "is_paid", 4, False)
        is_shipped = self._row_value(row, "is_closed", 5, False)
        return invoice_id, customer_number, invoice_date, amount, is_paid, is_shipped

    # ── KPI strip ─────────────────────────────────────────────────────────────
    def _build_summary_strip(self):
        strip = ctk.CTkFrame(self._body, fg_color="transparent")
        strip.pack(fill="x", padx=30, pady=(18, 0))
        strip.columnconfigure((0, 1, 2, 3), weight=1, pad=12)

        total = len(self.customers)
        active = sum(
            1 for c in self.customers if self._as_customer_row(c)[5] == "Active"
        )
        balance = sum(float(self._as_customer_row(c)[4] or 0) for c in self.customers)
        unpaid = sum(1 for i in self.invoices if not self._as_invoice_row(i)[4])

        SummaryCard(
            strip,
            "Total Customers",
            str(total),
            "All registered accounts",
            "👥",
            BRAND_BLUE,
        ).grid(row=0, column=0, sticky="nsew", padx=6)
        SummaryCard(
            strip,
            "Active Accounts",
            str(active),
            "Currently purchasing",
            "✅",
            ACCENT_GREEN,
        ).grid(row=0, column=1, sticky="nsew", padx=6)
        SummaryCard(
            strip,
            "Total Outstanding",
            f"₱{balance:,.2f}",
            "Unpaid balances",
            "💳",
            ACCENT_AMBER,
        ).grid(row=0, column=2, sticky="nsew", padx=6)
        SummaryCard(
            strip, "Unpaid Invoices", str(unpaid), "Awaiting payment", "🚨", ACCENT_RED
        ).grid(row=0, column=3, sticky="nsew", padx=6)

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
            placeholder_text="Search by customer no., company, or address…",
            width=300,
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
            values=["All", "Active", "Inactive", "New"],
            width=140,
            height=36,
            corner_radius=6,
            fg_color="#f5f7fa",
            button_color=BRAND_BLUE,
            text_color=TEXT_DARK,
            command=lambda _: self._apply_filter(),
        ).pack(side="left", padx=(8, 20))

        ctk.CTkLabel(
            inner, text="With Balance Only:", font=FONT_BODY, text_color=TEXT_MUTED
        ).pack(side="left")
        self._balance_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            inner,
            text="",
            variable=self._balance_var,
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
        self._to_picker.pack(side="left", padx=(4, 0))
        self._to_picker.entry.bind("<KeyRelease>", lambda *_: self._apply_filter())

        self._count_label = ctk.CTkLabel(
            inner,
            text=f"{len(self.customers)} records",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
        )
        self._count_label.pack(side="right")

    # ── Tabs ──────────────────────────────────────────────────────────────────
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
            ("customers", "👤  Customer List"),
            ("balances", "💳  Account Balances"),
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

        self._tab_frames["customers"] = self._build_customers_tab(content)
        self._tab_frames["balances"] = self._build_balances_tab(content)

        self._switch_tab("customers")

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

    # ── TAB 1: Customer List ──────────────────────────────────────────────────
    # Assumption 15: company, address, cust_no
    # Assumption 1:  current balance per account
    def _build_customers_tab(self, parent) -> ctk.CTkFrame:
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
            text="👤  Customer directory — company name, address, customer number, and current balance.",
            font=FONT_SMALL,
            text_color="#1a5276",
        ).pack(anchor="w", padx=10, pady=6)

        cols = ("Cust. No.", "Company", "Address", "Phone", "Current Balance", "Status")
        widths = (95, 230, 260, 140, 130, 90)

        self._customers_tree = self._make_treeview(frame, cols, widths, row=1)
        self._customers_tree.tag_configure("active", foreground="#1e8449")
        self._customers_tree.tag_configure("inactive", foreground=TEXT_MUTED)
        self._customers_tree.tag_configure(
            "new", foreground=BRAND_BLUE, font=("Segoe UI", 11, "bold")
        )
        self._customers_tree.tag_configure("balance", foreground=ACCENT_AMBER)

        self._populate_customers(self.customers)
        return frame

    def _populate_customers(self, data):
        tree = self._customers_tree
        tree.delete(*tree.get_children())
        for c in data:
            cust_no, company, address, phone, balance, status = self._as_customer_row(c)
            # Format customer number nicely
            try:
                cust_label = f"C-{int(cust_no):04d}"
            except Exception:
                cust_label = str(cust_no)
            try:
                balance = float(balance)
            except Exception:
                balance = 0.0
            if balance > 0 and status == "Active":
                tag = "balance"
            else:
                tag = {"Active": "active", "Inactive": "inactive", "New": "new"}.get(
                    status, "active"
                )
            tree.insert(
                "",
                "end",
                values=(
                    cust_label,
                    company,
                    address or "—",
                    phone or "—",
                    f"₱{balance:,.2f}" if balance > 0 else "—",
                    status,
                ),
                tags=(tag,),
            )
        self._count_label.configure(text=f"{len(data)} records")

    # ── TAB 2: Account Balances ───────────────────────────────────────────────
    # Assumption 1: track payments + current balance
    # Assumption 2: has the invoice shipped yet?
    # Assumption 3: which invoices have been paid?
    def _build_balances_tab(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            parent,
            fg_color=BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        frame.columnconfigure(0, weight=1)

        note = ctk.CTkFrame(frame, fg_color="#fef9e7", corner_radius=8)
        note.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            note,
            text="💳  One account per customer — invoice status, payment record, and shipment confirmation.",
            font=FONT_SMALL,
            text_color="#7d6608",
        ).pack(anchor="w", padx=10, pady=6)

        cols = (
            "Cust. No.",
            "Company",
            "Invoice No.",
            "Invoice Date",
            "Amount Due",
            "Paid?",
            "Shipped?",
        )
        widths = (95, 210, 110, 120, 120, 90, 100)

        self._balances_tree = self._make_treeview(frame, cols, widths, row=1)
        self._balances_tree.tag_configure("paid", foreground="#1e8449")
        self._balances_tree.tag_configure(
            "unpaid", foreground=ACCENT_RED, font=("Segoe UI", 11, "bold")
        )
        self._balances_tree.tag_configure("pending", foreground=ACCENT_AMBER)

        self._populate_balances()
        return frame

    def _populate_balances(self, data=None):
        tree = self._balances_tree
        tree.delete(*tree.get_children())
        # Key by int (from DB) so lookup works whether sample or live data
        cust_company = {}
        for c in self.customers:
            cust_no, company, _address, _phone, _balance, _status = (
                self._as_customer_row(c)
            )
            try:
                cust_company[int(cust_no)] = company
            except Exception:
                cust_company[cust_no] = company

        for inv in (data if data is not None else self.invoices):
            inv_no, cust_no, inv_date, amount, is_paid, is_shipped = (
                self._as_invoice_row(inv)
            )

            if isinstance(inv_date, str):
                try:
                    inv_date_str = datetime.date.fromisoformat(inv_date).strftime(
                        "%Y-%m-%d"
                    )
                except ValueError:
                    inv_date_str = inv_date
            elif isinstance(inv_date, (datetime.date, datetime.datetime)):
                d = inv_date if isinstance(inv_date, datetime.date) else inv_date.date()
                inv_date_str = d.strftime("%Y-%m-%d")
            else:
                inv_date_str = str(inv_date)

            if is_paid:
                tag = "paid"
            elif not is_shipped:
                tag = "pending"  # not paid AND not yet shipped
            else:
                tag = "unpaid"  # not paid but already shipped

            try:
                cust_label = f"C-{int(cust_no):04d}"
                cust_key = int(cust_no)
            except Exception:
                cust_label = str(cust_no)
                cust_key = cust_no
            try:
                inv_label = f"INV-{int(inv_no)}"
            except Exception:
                inv_label = str(inv_no)
            try:
                amount = float(amount)
            except Exception:
                amount = 0.0

            tree.insert(
                "",
                "end",
                values=(
                    cust_label,
                    cust_company.get(cust_key, "—"),
                    inv_label,
                    inv_date_str,
                    f"₱{amount:,.2f}",
                    "✅ Yes" if is_paid else "❌ No",
                    "✅ Yes" if is_shipped else "⏳ Pending",
                ),
                tags=(tag,),
            )

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

    # ── Filter (Customer List tab) ────────────────────────────────────────────
    def _apply_filter(self):
        query = self._search_var.get().lower()
        status = self._status_var.get()
        balance_only = self._balance_var.get()

        # ── Customer List tab filter ──────────────────────────────
        filtered_customers = [
            c
            for c in self.customers
            if (
                not query
                or query in str(self._row_value(c, "customer_number", 0)).lower()
                or query in str(self._row_value(c, "company_name", 1)).lower()
                or query in str(self._row_value(c, "address", 2)).lower()
            )
            and (status == "All" or self._row_value(c, "status", 5, "Active") == status)
            and (
                not balance_only or float(self._row_value(c, "balance", 4, 0) or 0) > 0
            )
        ]
        self._populate_customers(filtered_customers)

        # ── Account Balances tab filter ───────────────────────────
        cust_info = {}
        for c in self.customers:
            cust_no, company, _address, _phone, _balance, status = (
                self._as_customer_row(c)
            )
            try:
                key = int(cust_no)
            except Exception:
                key = cust_no
            cust_info[key] = (company, status)

        filtered_invoices = []
        for inv in self.invoices:
            inv_no, cust_no, inv_date, amount, is_paid, is_shipped = (
                self._as_invoice_row(inv)
            )
            try:
                cust_key = int(cust_no)
            except Exception:
                cust_key = cust_no
            cust_label = (
                f"C-{cust_key:04d}" if isinstance(cust_key, int) else str(cust_key)
            )
            company, cust_status = cust_info.get(cust_key, ("", "Active"))

            if query and not any(
                query in str(v).lower() for v in (cust_label, company, str(inv_no))
            ):
                continue
            if status != "All" and cust_status != status:
                continue
            if balance_only and float(amount or 0) <= 0:
                continue
            filtered_invoices.append(inv)

        self._populate_balances(filtered_invoices)

    # ── CSV export ────────────────────────────────────────────────────────────
    def _export_csv(self):
        rows = [
            self._customers_tree.item(iid, "values")
            for iid in self._customers_tree.get_children()
        ]
        export_customer_balances(self, rows)
