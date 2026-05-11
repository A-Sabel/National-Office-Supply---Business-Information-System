import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from typing import Any

# ── optional DB import ─────────────────────────────────────────────────────────
try:
    import psycopg2
    import psycopg2.extras

    HAS_DB = True
except ImportError:
    psycopg2 = None
    HAS_DB = False


# ══════════════════════════════════════════════════════════════════════════════
#  COLOUR & FONT TOKENS  (unchanged from original)
# ══════════════════════════════════════════════════════════════════════════════
C = {
    "bg": "#f8f9fa",
    "panel": "#ffffff",
    "border": "#e2e8f0",
    "accent": "#2563eb",
    "accent_h": "#1d4ed8",
    "danger": "#dc2626",
    "warn": "#d97706",
    "success": "#16a34a",
    "shipped": "#7c3aed",
    "paid": "#0d9488",
    "void": "#6b7280",
    "text": "#0f172a",
    "text_muted": "#64748b",
    "text_light": "#94a3b8",
    "row_alt": "#f8fafc",
    "row_hover": "#eff6ff",
    "input_bg": "#f8fafc",
    "input_bdr": "#cbd5e1",
    "red_field": "#fee2e2",
    "red_bdr": "#ef4444",
    "override": "#7c3aed",
    "override_h": "#6d28d9",
    "hdr_bg": "#f1f5f9",
}

FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 10)
FONT_H1 = ("Segoe UI", 20, "bold")
FONT_H3 = ("Segoe UI", 12, "bold")


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
STATUS_CFG = {
    "active":  {"bg": "#dbeafe", "fg": "#1d4ed8", "label": "Active"},
    "shipped": {"bg": "#ede9fe", "fg": "#7c3aed", "label": "Shipped"},
    "paid":    {"bg": "#ccfbf1", "fg": "#0d9488", "label": "Paid"},
    "void":    {"bg": "#f1f5f9", "fg": "#6b7280", "label": "Void"},
}


def status_badge(parent, status, bg_override=None):
    cfg = STATUS_CFG.get(status.lower(), STATUS_CFG["active"])
    bg = bg_override if bg_override else cfg["bg"]
    lbl = tk.Label(
        parent,
        text=cfg["label"],
        bg=bg,
        fg=cfg["fg"],
        font=("Segoe UI", 8, "bold"),
        padx=8,
        pady=3,
        relief="flat",
        bd=0,
    )
    return lbl


def fmt_currency(val):
    try:
        return f"₱{float(val):,.2f}"
    except Exception:
        return str(val)


# ══════════════════════════════════════════════════════════════════════════════
#  DB LAYER  ── all DB calls live here so UI classes stay clean
# ══════════════════════════════════════════════════════════════════════════════

class OrdersDB:
    """Thin data-access layer for the Orders & Invoices tab."""

    def __init__(self, db_config: dict):
        self.cfg = db_config

    def _connect(self):
        """Return a live psycopg2 connection or raise ConnectionError."""
        if not HAS_DB or psycopg2 is None:
            raise ConnectionError("psycopg2 is not installed.")
        try:
            return psycopg2.connect(
                dbname=self.cfg.get("dbname", self.cfg.get("DB_NAME", "postgres")),
                user=self.cfg.get("user", self.cfg.get("DB_USER", "postgres")),
                password=self.cfg.get("password", self.cfg.get("DB_PASS", "")),
                host=self.cfg.get("host", self.cfg.get("DB_HOST", "localhost")),
                port=int(self.cfg.get("port", self.cfg.get("DB_PORT", 5432))),
            )
        except Exception as exc:
            raise ConnectionError(f"Cannot connect to database: {exc}") from exc

    # ------------------------------------------------------------------
    # READ helpers
    # ------------------------------------------------------------------

    def fetch_invoices(self, status_filter: str | None = None) -> list[dict]:
        """Return the 200 most-recent invoices with customer and rep names.
        
        Args:
            status_filter: If provided, only return invoices matching this status
                          (e.g. 'active', 'shipped'). None returns all statuses.
        """
        sql = """
            SELECT
                i.invoice_id,
                i.invoice_id::text           AS invoice_number,
                c.customer_name              AS customer_name,
                c.company_name               AS company_name,
                c.address                    AS customer_address,
                c.customer_number,
                COALESCE(i.total_amount, 0)  AS amount,
                i.status,
                i.date_written::text         AS date,
                e.employee_name              AS sales_rep,
                e.employee_number
            FROM invoices i
            JOIN customers c ON c.customer_number = i.customer_number
            JOIN employees e ON e.employee_number = i.employee_number
        """
        params: tuple = ()
        if status_filter and status_filter.lower() in ("active", "shipped", "paid", "void"):
            sql += " WHERE i.status = %s"
            params = (status_filter.lower(),)
        sql += " ORDER BY i.date_written DESC, i.invoice_id DESC LIMIT 200"

        conn = self._connect()
        try:
            with conn, conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(sql, params)
                rows = [dict(r) for r in cur.fetchall()]
                for r in rows:
                    r["invoice_number"] = f"INV-{r['invoice_id']}"
                return rows
        finally:
            conn.close()

    def fetch_invoice_lines(self, invoice_id: int) -> list[dict]:
        """Return line items for a single invoice."""
        sql = """
            SELECT
                il.part_number,
                p.description,
                il.quantity,
                p.selling_price   AS unit_price,
                il.line_total
            FROM invoice_lines il
            JOIN parts p ON p.part_number = il.part_number
            WHERE il.invoice_id = %s
            ORDER BY p.description
        """
        conn = self._connect()
        try:
            with conn, conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(sql, (invoice_id,))
                return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def fetch_active_customers(self) -> list[dict]:
        """Return id + names for every active customer (for the create-invoice dropdown)."""
        sql = """
            SELECT customer_number, customer_name, company_name, address
            FROM customers
            WHERE is_active = TRUE
            ORDER BY company_name
        """
        conn = self._connect()
        try:
            with conn, conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(sql)
                return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def fetch_parts(self) -> list[dict]:
        """Return all parts with stock and price for the line-item picker."""
        sql = """
            SELECT part_number, description, selling_price, stock_count
            FROM parts
            ORDER BY description
        """
        conn = self._connect()
        try:
            with conn, conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(sql)
                return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # BACKEND VALIDATION
    # ------------------------------------------------------------------

    def validate_order(
        self,
        customer_number: int,
        line_items: list[dict],
        manager_override: bool = False,
    ) -> list[str]:
        """
        Run backend validation rules before submitting an order.
        Returns a list of error strings; empty list means all checks passed.

        Rules checked:
          1. Customer must exist and have is_active = TRUE
          2. Every line item must have quantity >= 1
          3. Every part must exist and have stock >= qty (unless manager_override)
          4. Invoice total must equal SUM(qty * selling_price) per line
        """
        errors: list[str] = []
        conn = self._connect()
        try:
            with conn, conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Rule 1 — customer active check
                cur.execute(
                    "SELECT is_active FROM customers WHERE customer_number = %s",
                    (customer_number,),
                )
                cust_row = cur.fetchone()
                if not cust_row:
                    errors.append(f"Customer #{customer_number} does not exist.")
                elif not cust_row["is_active"]:
                    errors.append(
                        f"Customer #{customer_number} account is inactive and cannot be billed."
                    )

                for item in line_items:
                    pnum = item["part_number"]
                    qty = item["quantity"]
                    unit = item.get("unit_price", 0)

                    # Rule 2 — quantity >= 1
                    if not isinstance(qty, int) or qty < 1:
                        errors.append(
                            f"Part #{pnum}: quantity must be ≥ 1 (got {qty})."
                        )
                        continue  # skip further checks for this line

                    # Rule 3 — part exists and has stock
                    cur.execute(
                        "SELECT description, selling_price, stock_count FROM parts WHERE part_number = %s",
                        (pnum,),
                    )
                    part_row = cur.fetchone()
                    if not part_row:
                        errors.append(f"Part #{pnum} does not exist in inventory.")
                        continue

                    if not manager_override and part_row["stock_count"] < qty:
                        errors.append(
                            f"'{part_row['description']}': requested {qty}, "
                            f"only {part_row['stock_count']} in stock. "
                            "Use Manager Override to proceed."
                        )

                    # Rule 4 — line total integrity  (qty × selling_price)
                    expected_total = round(qty * float(part_row["selling_price"]), 2)
                    actual_total = round(float(item.get("line_total", 0)), 2)
                    if abs(expected_total - actual_total) > 0.01:
                        errors.append(
                            f"'{part_row['description']}': line total ₱{actual_total} "
                            f"does not match qty × price = ₱{expected_total}."
                        )
        finally:
            conn.close()
        return errors

    # ------------------------------------------------------------------
    # WRITE helpers
    # ------------------------------------------------------------------

    def create_invoice(
        self,
        customer_number: int,
        employee_number: int,
        line_items: list[dict],
        total: float,
        manager_override: bool = False,
    ) -> dict:
        """
        Validate then insert invoice + invoice_lines atomically.
        Status is set to 'active' (pending shipment).
        Stock is NOT decremented on creation — only on shipment (Req 13).
        Returns the new invoice row as a dict.
        Raises ValueError with a human-readable message on validation failure.
        """
        # ── Backend validation ──────────────────────────────────────────────
        errors = self.validate_order(customer_number, line_items, manager_override)
        if errors:
            raise ValueError("Order validation failed:\n• " + "\n• ".join(errors))

        # ── Recalculate total server-side to prevent tampering ──────────────
        recalculated_total = sum(
            round(item["quantity"] * item["unit_price"], 2) for item in line_items
        )

        conn = self._connect()
        try:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    # 1. Create the invoice header (status = 'active')
                    cur.execute(
                        """
                        INSERT INTO invoices
                            (employee_number, customer_number, total_amount, status, date_written)
                        VALUES (%s, %s, %s, 'active', CURRENT_DATE)
                        RETURNING invoice_id, date_written::text
                        """,
                        (employee_number, customer_number, recalculated_total),
                    )
                    row = cur.fetchone()
                    invoice_id = row["invoice_id"]
                    date_written = row["date_written"]

                    # 2. Insert each line item (stock NOT decremented here — happens on ship)
                    for item in line_items:
                        cur.execute(
                            """
                            INSERT INTO invoice_lines
                                (invoice_id, part_number, quantity, line_total)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                invoice_id,
                                item["part_number"],
                                item["quantity"],
                                round(item["quantity"] * item["unit_price"], 2),
                            ),
                        )

                    return {
                        "invoice_id": invoice_id,
                        "invoice_number": f"INV-{invoice_id}",
                        "date": date_written,
                        "total": recalculated_total,
                    }
        finally:
            conn.close()

    def ship_invoice(self, invoice_id: int) -> bool:
        """
        Mark an invoice as 'shipped', then for each line item:
          - Decrement parts.stock_count by the ordered quantity (Req 13 / PartService)
          - Add invoice total to customer's current_balance (Req 13 / customer balance)

        Allowed only when current status is 'active'.
        Returns True on success, False if transition is blocked.
        """
        conn = self._connect()
        try:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    # Lock the invoice row and check status
                    cur.execute(
                        "SELECT status, customer_number, total_amount FROM invoices WHERE invoice_id = %s FOR UPDATE",
                        (invoice_id,),
                    )
                    inv_row = cur.fetchone()
                    if not inv_row:
                        return False
                    if inv_row["status"] != "active":
                        return False

                    # Fetch line items
                    cur.execute(
                        "SELECT part_number, quantity FROM invoice_lines WHERE invoice_id = %s",
                        (invoice_id,),
                    )
                    lines = cur.fetchall()

                    # Decrement stock for each line (PartService.update_stock equivalent)
                    for line in lines:
                        cur.execute(
                            """
                            UPDATE parts
                            SET stock_count = GREATEST(stock_count - %s, 0)
                            WHERE part_number = %s
                            """,
                            (line["quantity"], line["part_number"]),
                        )

                    # Update customer balance += invoice total
                    cur.execute(
                        """
                        UPDATE customers
                        SET current_balance = current_balance + %s
                        WHERE customer_number = %s
                        """,
                        (inv_row["total_amount"], inv_row["customer_number"]),
                    )

                    # Advance invoice status to 'shipped'
                    cur.execute(
                        "UPDATE invoices SET status = 'shipped' WHERE invoice_id = %s",
                        (invoice_id,),
                    )
                    return True
        finally:
            conn.close()

    def update_invoice_status(self, invoice_id: int, new_status: str) -> bool:
        """
        Advance an invoice to a new status.
        - active  → shipped : use ship_invoice() which also handles stock + balance
        - active  → void    : handled here; removes line items
        - shipped → paid    : handled here
        Returns True on success, False if the row was not found / transition blocked.
        """
        if new_status == "shipped":
            return self.ship_invoice(invoice_id)

        VALID = {"active": {"void"}, "shipped": {"paid"}}
        conn = self._connect()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT status FROM invoices WHERE invoice_id = %s",
                        (invoice_id,),
                    )
                    row = cur.fetchone()
                    if not row:
                        return False
                    current = row[0]
                    if current == new_status:
                        return True
                    if new_status not in VALID.get(current, set()):
                        return False

                    if new_status == "void":
                        # Remove line items before voiding (cascade not guaranteed for void)
                        cur.execute(
                            "DELETE FROM invoice_lines WHERE invoice_id = %s",
                            (invoice_id,),
                        )

                    cur.execute(
                        "UPDATE invoices SET status = %s WHERE invoice_id = %s",
                        (new_status, invoice_id),
                    )
                    return True
        finally:
            conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  KPI BAR
# ══════════════════════════════════════════════════════════════════════════════
class KPIBar(ctk.CTkFrame):
    def __init__(self, master, invoices, **kw):
        super().__init__(master, fg_color=C["bg"], **kw)
        self.invoices = invoices
        self._build()

    def _build(self):
        totals  = sum(i["amount"] for i in self.invoices)
        active  = sum(1 for i in self.invoices if i["status"] == "active")
        shipped = sum(1 for i in self.invoices if i["status"] == "shipped")
        paid    = sum(1 for i in self.invoices if i["status"] == "paid")

        cards = [
            ("Total Invoices",  str(len(self.invoices)), C["accent"],  "All records"),
            ("Total Revenue",   fmt_currency(totals),    C["success"], "From listed invoices"),
            ("Pending / Active", str(active),            C["warn"],    "Needs action"),
            ("Shipped",         str(shipped),            C["shipped"], "Ready to collect"),
            ("Paid",            str(paid),               C["paid"],    "Settled invoices"),
        ]

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=0, pady=6)
        for i in range(len(cards)):
            container.grid_columnconfigure(i, weight=1)

        for idx, (title, val, clr, sub) in enumerate(cards):
            card = ctk.CTkFrame(
                container, fg_color=C["panel"], corner_radius=12,
                border_width=1, border_color=C["border"], height=108,
            )
            card.grid(row=0, column=idx, sticky="nsew",
                      padx=(0 if idx == 0 else 5), pady=0)
            card.pack_propagate(False)

            ctk.CTkLabel(card, text=title, font=("Segoe UI", 11, "bold"),
                         text_color=C["text_muted"]).pack(anchor="w", padx=14, pady=(12, 0))
            ctk.CTkLabel(card, text=val, font=("Segoe UI", 22, "bold"),
                         text_color="#2c3e50").pack(anchor="w", padx=14, pady=(2, 0))
            ctk.CTkLabel(card, text=sub, font=("Segoe UI", 10),
                         text_color=clr).pack(anchor="w", padx=14, pady=(0, 12))


# ══════════════════════════════════════════════════════════════════════════════
#  INVOICE DETAIL POPUP  (now loads live line-items from DB)
# ══════════════════════════════════════════════════════════════════════════════
class InvoiceDetailDialog(tk.Toplevel):
    def __init__(self, master, invoice, role, on_status_change, db: "OrdersDB | None" = None):
        super().__init__(master)
        self.title(f"Invoice Details — {invoice['invoice_number']}")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.db = db
        inv = invoice

        # ── Header bar ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=C["accent"], height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"Invoice  {inv['invoice_number']}",
                 font=("Segoe UI", 14, "bold"), bg=C["accent"], fg="white"
                 ).pack(side="left", padx=20, pady=14)
        badge = status_badge(hdr, inv["status"], bg_override="white")
        badge.pack(side="right", padx=20, pady=14)

        body = tk.Frame(self, bg=C["bg"], padx=28, pady=18)
        body.pack(fill="both", expand=True)

        def field_row(label, value):
            r = tk.Frame(body, bg=C["bg"])
            r.pack(fill="x", pady=3)
            tk.Label(r, text=label, width=16, anchor="w", font=FONT_BOLD,
                     bg=C["bg"], fg=C["text_muted"]).pack(side="left")
            tk.Label(r, text=value, anchor="w", font=FONT,
                     bg=C["bg"], fg=C["text"]).pack(side="left")

        field_row("Customer:",    inv.get("customer_name", "—"))
        field_row("Company:",     inv.get("company_name", "—"))
        field_row("Address:",     inv.get("customer_address", "—"))
        field_row("Customer #:",  str(inv.get("customer_number", "—")))
        field_row("Date Written:", inv.get("date", "—"))
        field_row("Sales Rep:",   inv.get("sales_rep", "—"))
        field_row("Amount Due:",  fmt_currency(inv.get("amount", 0)))

        tk.Frame(body, bg=C["border"], height=1).pack(fill="x", pady=10)

        # ── Line Items section ────────────────────────────────────────────────
        tk.Label(body, text="Items", font=FONT_BOLD,
                 bg=C["bg"], fg=C["text_muted"]).pack(anchor="w", pady=(0, 4))

        lines_frame = tk.Frame(body, bg=C["bg"])
        lines_frame.pack(fill="x", pady=(0, 8))

        if self.db and inv.get("invoice_id"):
            lines = []
            try:
                lines = self.db.fetch_invoice_lines(inv["invoice_id"])
            except Exception as exc:
                tk.Label(lines_frame, text=f"Could not load line items: {exc}",
                         font=FONT_SMALL, bg=C["bg"], fg=C["danger"]).pack(anchor="w")

            if lines:
                hdr_row = tk.Frame(lines_frame, bg=C["hdr_bg"])
                hdr_row.pack(fill="x")
                for txt, w in [("Item", 22), ("Qty", 5), ("Unit Price", 10), ("Total", 10)]:
                    tk.Label(hdr_row, text=txt, font=FONT_SMALL, bg=C["hdr_bg"],
                             fg=C["text_muted"], width=w, anchor="w",
                             padx=4, pady=3).pack(side="left")

                for i, line in enumerate(lines):
                    bg = C["row_alt"] if i % 2 else C["panel"]
                    lr = tk.Frame(lines_frame, bg=bg)
                    lr.pack(fill="x")
                    tk.Label(lr, text=line["description"][:28], font=FONT_SMALL,
                             bg=bg, fg=C["text"], width=22, anchor="w").pack(side="left", padx=4, pady=3)
                    tk.Label(lr, text=str(line["quantity"]), font=FONT_SMALL,
                             bg=bg, fg=C["text"], width=5, anchor="w").pack(side="left")
                    tk.Label(lr, text=fmt_currency(line["unit_price"]), font=FONT_SMALL,
                             bg=bg, fg=C["text"], width=10, anchor="w").pack(side="left")
                    tk.Label(lr, text=fmt_currency(line["line_total"]), font=FONT_SMALL,
                             bg=bg, fg=C["accent"], width=10, anchor="w").pack(side="left")
            elif not any(isinstance(c, tk.Label) for c in lines_frame.winfo_children()):
                tk.Label(lines_frame, text="No line items on record.", font=FONT_SMALL,
                         bg=C["bg"], fg=C["text_light"]).pack(anchor="w")
        else:
            tk.Label(lines_frame, text="Line item detail unavailable (no DB connection).",
                     font=FONT_SMALL, bg=C["bg"], fg=C["text_light"]).pack(anchor="w")

        tk.Frame(body, bg=C["border"], height=1).pack(fill="x", pady=10)

        # ── Status action buttons ─────────────────────────────────────────────
        status = inv["status"].lower()
        action_frame = tk.Frame(body, bg=C["bg"])
        action_frame.pack(fill="x", pady=4)

        def do_ship():
            on_status_change(inv["invoice_id"], inv["invoice_number"], "shipped")
            self.destroy()

        def do_paid():
            on_status_change(inv["invoice_id"], inv["invoice_number"], "paid")
            self.destroy()

        def do_void():
            if messagebox.askyesno(
                "Confirm Void",
                f"Void invoice {inv['invoice_number']}?\nThis cannot be undone.",
            ):
                on_status_change(inv["invoice_id"], inv["invoice_number"], "void")
                self.destroy()

        if status == "active":
            tk.Label(action_frame, text="Status Actions:", font=FONT_BOLD,
                     bg=C["bg"], fg=C["text_muted"]).pack(anchor="w", pady=(0, 6))
            btn_row = tk.Frame(action_frame, bg=C["bg"])
            btn_row.pack(anchor="w")
            tk.Button(btn_row, text="✓  Mark Shipped", bg=C["shipped"], fg="white",
                      font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                      padx=12, pady=6, cursor="hand2", command=do_ship,
                      ).pack(side="left", padx=(0, 8))
            tk.Button(btn_row, text="✕  Void", bg=C["danger"], fg="white",
                      font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                      padx=12, pady=6, cursor="hand2", command=do_void,
                      ).pack(side="left")

        elif status == "shipped":
            tk.Label(action_frame, text="Status Actions:", font=FONT_BOLD,
                     bg=C["bg"], fg=C["text_muted"]).pack(anchor="w", pady=(0, 6))
            tk.Button(action_frame, text="💳  Mark Paid", bg=C["paid"], fg="white",
                      font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                      padx=12, pady=6, cursor="hand2", command=do_paid,
                      ).pack(anchor="w")

        elif status in ("paid", "void"):
            tk.Label(action_frame,
                     text="🔒  This invoice is fully locked (no further actions).",
                     font=FONT_SMALL, bg=C["bg"], fg=C["text_muted"]).pack(anchor="w")

        tk.Frame(body, bg=C["border"], height=1).pack(fill="x", pady=10)
        ctk.CTkButton(body, text="Close", width=100, height=32,
                      fg_color=C["border"], text_color=C["text"],
                      hover_color="#cbd5e1", command=self.destroy).pack(anchor="e")

        self.update_idletasks()
        w, h = 520, self.winfo_reqheight()
        x = master.winfo_rootx() + (master.winfo_width() - w) // 2
        y = master.winfo_rooty() + 80
        self.geometry(f"{w}x{h}+{x}+{y}")


# ══════════════════════════════════════════════════════════════════════════════
#  MANAGE INVOICES PANEL
# ══════════════════════════════════════════════════════════════════════════════
class ManageInvoicesPanel(ctk.CTkFrame):

    def __init__(self, master, invoices, role, on_status_change, db=None, **kw):
        super().__init__(master, fg_color=C["panel"], corner_radius=12,
                         border_width=1, border_color=C["border"], **kw)
        self.invoices = list(invoices)
        self.filtered = list(invoices)
        self.role = role
        self.on_status_change = on_status_change
        self.db = db
        self._build()

    def _build(self):
        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = tk.Frame(self, bg=C["panel"])
        toolbar.pack(fill="x", padx=16, pady=(14, 8))

        tk.Label(toolbar, text="Manage Invoices", font=("Segoe UI", 13, "bold"),
                 bg=C["panel"], fg=C["text"]).pack(side="left")

        # Filter dropdown
        self.filter_var = tk.StringVar(value="All Status")
        ctk.CTkOptionMenu(
            toolbar,
            variable=self.filter_var,
            values=["All Status", "active", "shipped", "paid", "void"],
            fg_color=C["input_bg"], button_color=C["accent"],
            text_color=C["text"], width=120, height=28,
            command=self._apply_filter,
        ).pack(side="right", padx=(6, 0))

        # Refresh button (to the left of search)
        tk.Button(
            toolbar, text="↻", bg=C["panel"], fg=C["accent"],
            font=("Segoe UI", 12, "bold"), relief="flat", bd=0,
            padx=6, pady=2, cursor="hand2",
            command=self._refresh,
        ).pack(side="right", padx=(0, 4))

        # Search box
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        sb = tk.Frame(toolbar, bg=C["input_bg"],
                      highlightthickness=1, highlightbackground=C["input_bdr"])
        sb.pack(side="right", padx=(0, 4))
        tk.Label(sb, text="🔍", bg=C["input_bg"], font=("Segoe UI", 9)).pack(side="left", padx=(6, 0))
        tk.Entry(sb, textvariable=self.search_var, font=FONT, relief="flat",
                 width=16, bg=C["input_bg"], fg=C["text"],
                 insertbackground=C["text"]).pack(side="left", padx=4, pady=3)

        # ── Column definitions (shared by header + every row) ─────────────────
        # (label, pixel_width, anchor)
        self.COLS = [
            ("Invoice #",     100, "w"),
            ("Company",       150, "w"),
            ("Contact",       160, "w"),
            ("Amount",        110, "e"),
            ("Status",        90,  "center"),
            ("Date",          100, "w"),
            ("Actions",       0,   "w"),   # 0 = fill remaining space
        ]

        # ── Column headers ────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=C["hdr_bg"],
                       highlightthickness=1, highlightbackground=C["border"])
        hdr.pack(fill="x", padx=16, pady=(0, 0))

        for col_idx, (txt, px, anc) in enumerate(self.COLS):
            if px:
                lbl = tk.Label(hdr, text=txt, font=FONT_BOLD, bg=C["hdr_bg"],
                               fg=C["text_muted"], anchor=anc, padx=8, pady=7,
                               width=1)          # width=1 + fixed frame below
                lbl.grid(row=0, column=col_idx, sticky="nsew", ipadx=0)
                hdr.grid_columnconfigure(col_idx, minsize=px, weight=0)
            else:
                lbl = tk.Label(hdr, text=txt, font=FONT_BOLD, bg=C["hdr_bg"],
                               fg=C["text_muted"], anchor="w", padx=8, pady=7)
                lbl.grid(row=0, column=col_idx, sticky="nsew")
                hdr.grid_columnconfigure(col_idx, weight=1)

        # ── Scrollable rows ───────────────────────────────────────────────────
        self.rows_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.rows_frame.pack(fill="both", expand=True, padx=16, pady=(2, 12))
        self._render_rows()

    def _apply_filter(self, _=None):
        q = self.search_var.get().lower()
        status = self.filter_var.get()
        self.filtered = [
            inv for inv in self.invoices
            if (status == "All Status" or inv["status"].lower() == status)
            and (
                q in inv["invoice_number"].lower()
                or q in inv.get("customer_name", "").lower()
                or q in inv.get("company_name", "").lower()
            )
        ]
        self._render_rows()

    def _render_rows(self):
        for w in self.rows_frame.winfo_children():
            w.destroy()

        if not self.filtered:
            tk.Label(self.rows_frame, text="No invoices found.", font=FONT,
                     bg=C["panel"], fg=C["text_muted"]).pack(pady=30)
            return

        for i, inv in enumerate(self.filtered):
            bg = C["row_alt"] if i % 2 else C["panel"]

            # Each row is a Frame that uses the same grid columns as the header
            row = tk.Frame(self.rows_frame, bg=bg)
            row.pack(fill="x")
            tk.Frame(self.rows_frame, bg=C["border"], height=1).pack(fill="x")

            # Mirror the same column weights as the header
            for col_idx, (_, px, __) in enumerate(self.COLS):
                if px:
                    row.grid_columnconfigure(col_idx, minsize=px, weight=0)
                else:
                    row.grid_columnconfigure(col_idx, weight=1)

            def _enter(e, r=row, b=bg): r.configure(bg=C["row_hover"])
            def _leave(e, r=row, b=bg): r.configure(bg=b)
            row.bind("<Enter>", _enter)
            row.bind("<Leave>", _leave)

            inv_ref = inv
            PAD = {"padx": 8, "pady": 8, "sticky": "nsew"}

            # Col 0 — Invoice #
            tk.Label(row, text=inv["invoice_number"], font=FONT_MONO,
                     bg=bg, fg=C["accent"], anchor="w"
                     ).grid(row=0, column=0, **PAD)

            # Col 1 — Company
            tk.Label(row, text=inv.get("company_name", "—"), font=FONT,
                     bg=bg, fg=C["text"], anchor="w"
                     ).grid(row=0, column=1, **PAD)

            # Col 2 — Contact
            tk.Label(row, text=inv.get("customer_name", "—"), font=FONT,
                     bg=bg, fg=C["text_muted"], anchor="w"
                     ).grid(row=0, column=2, **PAD)

            # Col 3 — Amount (right-aligned)
            tk.Label(row, text=fmt_currency(inv["amount"]), font=FONT,
                     bg=bg, fg=C["text"], anchor="e"
                     ).grid(row=0, column=3, padx=8, pady=8, sticky="nse")

            # Col 4 — Status badge (centered)
            cfg = STATUS_CFG.get(inv["status"].lower(), STATUS_CFG["active"])
            badge_wrap = tk.Frame(row, bg=bg)
            badge_wrap.grid(row=0, column=4, padx=6, pady=6, sticky="nsew")
            tk.Label(badge_wrap, text=cfg["label"],
                     bg=cfg["bg"], fg=cfg["fg"],
                     font=("Segoe UI", 8, "bold"),
                     padx=10, pady=3, relief="flat"
                     ).pack(expand=True)

            # Col 5 — Date
            tk.Label(row, text=inv.get("date", ""), font=FONT_SMALL,
                     bg=bg, fg=C["text_muted"], anchor="w"
                     ).grid(row=0, column=5, **PAD)

            # Col 6 — Actions
            act = tk.Frame(row, bg=bg)
            act.grid(row=0, column=6, padx=6, pady=6, sticky="nsew")

            s = inv["status"].lower()

            tk.Button(act, text="View Details", bg=C["accent"], fg="white",
                      font=("Segoe UI", 8, "bold"), relief="flat", bd=0,
                      padx=8, pady=4, cursor="hand2",
                      command=lambda iv=inv_ref: self._open_detail(iv),
                      ).pack(side="left", padx=(0, 4))

            if s == "active":
                tk.Button(act, text="Mark Shipped", bg=C["shipped"], fg="white",
                          font=("Segoe UI", 8, "bold"), relief="flat", bd=0,
                          padx=8, pady=4, cursor="hand2",
                          command=lambda iv=inv_ref: self._quick_action(iv, "shipped"),
                          ).pack(side="left", padx=(0, 4))
                tk.Button(act, text="Void", bg=C["danger"], fg="white",
                          font=("Segoe UI", 8, "bold"), relief="flat", bd=0,
                          padx=8, pady=4, cursor="hand2",
                          command=lambda iv=inv_ref: self._quick_action(iv, "void"),
                          ).pack(side="left")
            elif s == "shipped":
                tk.Button(act, text="Mark Paid", bg=C["paid"], fg="white",
                          font=("Segoe UI", 8, "bold"), relief="flat", bd=0,
                          padx=8, pady=4, cursor="hand2",
                          command=lambda iv=inv_ref: self._quick_action(iv, "paid"),
                          ).pack(side="left")

    def _open_detail(self, inv):
        InvoiceDetailDialog(
            self.winfo_toplevel(), inv, self.role,
            on_status_change=lambda iid, inum, st: self._update_status(iid, inum, st),
            db=self.db,
        )

    def _quick_action(self, inv, new_status):
        if new_status == "void" and not messagebox.askyesno(
            "Confirm", f"Void invoice {inv['invoice_number']}?"
        ):
            return
        self._update_status(inv["invoice_id"], inv["invoice_number"], new_status)

    def _update_status(self, inv_id, inv_number, new_status):
        # ── Persist to DB ──
        if self.db and inv_id:
            try:
                ok = self.db.update_invoice_status(inv_id, new_status)
                if not ok:
                    messagebox.showerror(
                        "Status Error",
                        f"Could not change {inv_number} to '{new_status}'.\n"
                        "The transition may be invalid or the record was modified elsewhere.",
                    )
                    return
            except Exception as exc:
                messagebox.showerror("Database Error", str(exc))
                return

        # ── Update in-memory list ──
        for inv in self.invoices:
            if inv.get("invoice_id") == inv_id:
                inv["status"] = new_status
                break

        self.on_status_change(inv_id, inv_number, new_status)
        self._apply_filter()

    def add_invoice(self, inv):
        self._apply_filter()

    def _refresh(self):
        """Reload invoices from DB and re-render the list."""
        if self.db:
            try:
                self.invoices = self.db.fetch_invoices()
            except Exception as exc:
                from tkinter import messagebox as _mb
                _mb.showerror("Refresh Error", str(exc))
                return
        self._apply_filter()


# ══════════════════════════════════════════════════════════════════════════════
#  CREATE INVOICE PANEL  (now wired to DB)
# ══════════════════════════════════════════════════════════════════════════════
class CreateInvoicePanel(ctk.CTkFrame):
    def __init__(self, master, customers, parts, role, on_create, db=None, **kw):
        super().__init__(master, fg_color=C["panel"], corner_radius=12,
                         border_width=1, border_color=C["border"], **kw)
        # customers is list[dict] with keys: customer_number, company_name
        self.customers_raw = customers
        self.customers = [c["company_name"] for c in customers]
        # parts is list[dict] with keys: part_number, description, selling_price, stock_count
        self.parts = parts
        self.role = role
        self.on_create = on_create
        self.db = db
        self.line_items = []
        self._override_active = False
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=C["panel"])
        hdr.pack(fill="x", padx=20, pady=(16, 8))
        tk.Label(hdr, text="Create Invoice", font=("Segoe UI", 13, "bold"),
                 bg=C["panel"], fg=C["text"]).pack(side="left")

        body = tk.Frame(self, bg=C["panel"])
        body.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        def section(parent, text):
            tk.Label(parent, text=text, font=FONT_BOLD,
                     bg=C["panel"], fg=C["text_muted"]).pack(anchor="w", pady=(10, 2))

        # ── Select Company (dropdown — filters contacts below) ───────────────
        section(body, "Select Company")
        company_names = sorted(set(c["company_name"] for c in self.customers_raw)) if self.customers_raw else ["(No companies)"]
        self.company_var = tk.StringVar(value="Select Company…")
        self.company_menu = ctk.CTkOptionMenu(
            body, variable=self.company_var,
            values=company_names,
            fg_color=C["input_bg"], button_color=C["accent"],
            text_color=C["text"], width=270, height=32,
            command=self._on_company_selected,
        )
        self.company_menu.pack(anchor="w", pady=(0, 6))

        # ── Select Contact (filters based on company, or shows all) ──────────
        section(body, "Select Contact")
        cust_display_names = [c["customer_name"] for c in self.customers_raw] if self.customers_raw else ["(No contacts)"]
        self.cust_var = tk.StringVar(value="Select Contact…")
        self.contact_menu = ctk.CTkOptionMenu(
            body, variable=self.cust_var,
            values=cust_display_names,
            fg_color=C["input_bg"], button_color=C["accent"],
            text_color=C["text"], width=270, height=32,
            command=self._on_contact_selected,
        )
        self.contact_menu.pack(anchor="w", pady=(0, 6))

        # ── Select Item ───────────────────────────────────────────────────────
        section(body, "Select Item")
        part_names = [p["description"] for p in self.parts]
        self.part_var = tk.StringVar(value="Select Item…")
        ctk.CTkOptionMenu(
            body, variable=self.part_var,
            values=part_names if part_names else ["(No parts)"],
            fg_color=C["input_bg"], button_color=C["accent"],
            text_color=C["text"], width=270, height=32,
            command=self._on_part_selected,
        ).pack(anchor="w", pady=(0, 4))

        # ── Quantity ──────────────────────────────────────────────────────────
        section(body, "Quantity")
        qty_row = tk.Frame(body, bg=C["panel"])
        qty_row.pack(anchor="w", pady=(0, 2))

        self.qty_frame = tk.Frame(qty_row, bg=C["panel"],
                                  highlightthickness=1, highlightbackground=C["input_bdr"])
        self.qty_frame.pack(side="left")
        self.qty_entry = tk.Entry(self.qty_frame, width=6, font=FONT, relief="flat",
                                  bg=C["input_bg"], fg=C["text"], insertbackground=C["text"])
        self.qty_entry.insert(0, "1")
        self.qty_entry.pack(padx=8, pady=5)
        self.qty_entry.bind("<KeyRelease>", self._validate_qty)

        self.override_btn = tk.Button(
            qty_row, text="⚡ Manager Override", bg=C["override"], fg="white",
            font=("Segoe UI", 8, "bold"), relief="flat", bd=0,
            padx=10, pady=5, cursor="hand2", command=self._activate_override,
        )
        if self.role == "Manager":
            self.override_btn.pack(side="left", padx=(8, 0))

        self.warn_lbl = tk.Label(body, text="", fg=C["danger"], bg=C["panel"],
                                 font=("Segoe UI", 8, "bold"))
        self.warn_lbl.pack(anchor="w")

        self.stock_lbl = tk.Label(body, text="", fg=C["text_muted"], bg=C["panel"],
                                  font=FONT_SMALL)
        self.stock_lbl.pack(anchor="w", pady=(0, 4))

        # ── Price per Unit ────────────────────────────────────────────────────
        section(body, "Price per Unit")
        self.price_lbl = tk.Label(body, text="—", font=FONT, bg=C["panel"], fg=C["text"])
        self.price_lbl.pack(anchor="w", pady=(0, 4))

        # ── Add Line Item ─────────────────────────────────────────────────────
        ctk.CTkButton(body, text="+ Add Line Item", fg_color=C["border"],
                      text_color=C["text"], hover_color="#cbd5e1",
                      height=30, width=270, command=self._add_line_item,
                      ).pack(anchor="w", pady=(4, 8))

        # ── Items in this Invoice ─────────────────────────────────────────────
        section(body, "Items in this Invoice")
        self.items_frame = tk.Frame(body, bg=C["panel"])
        self.items_frame.pack(fill="x", pady=(2, 6))
        self._refresh_items_list()

        # ── Total ─────────────────────────────────────────────────────────────
        tk.Frame(body, bg=C["border"], height=1).pack(fill="x", pady=6)
        total_row = tk.Frame(body, bg=C["panel"])
        total_row.pack(fill="x")
        tk.Label(total_row, text="Total", font=FONT_BOLD, bg=C["panel"], fg=C["text"]).pack(side="left")
        self.total_lbl = tk.Label(total_row, text="₱0.00", font=("Segoe UI", 13, "bold"),
                                  bg=C["panel"], fg=C["accent"])
        self.total_lbl.pack(side="right")

        # ── Save Invoice ──────────────────────────────────────────────────────
        ctk.CTkButton(body, text="Save Invoice", fg_color=C["accent"],
                      hover_color=C["accent_h"], height=36, width=270,
                      font=ctk.CTkFont("Segoe UI", 11, "bold"), command=self._submit,
                      ).pack(anchor="w", pady=(10, 4))

    # ── helpers ───────────────────────────────────────────────────────────────
    def _get_selected_part(self):
        name = self.part_var.get()
        for p in self.parts:
            if p["description"] == name:
                return p
        return None

    def _get_selected_customer(self):
        name = self.cust_var.get()
        for c in self.customers_raw:
            if c["customer_name"] == name:
                return c
        return None

    def _on_company_selected(self, company_name=None):
        """When company is chosen, filter the contact dropdown to that company's contacts."""
        company = company_name or self.company_var.get()
        contacts = [
            c["customer_name"] for c in self.customers_raw
            if c["company_name"] == company
        ]
        if not contacts:
            contacts = ["(No contacts)"]
        self.contact_menu.configure(values=contacts)
        self.cust_var.set("Select Contact…")

    def _on_contact_selected(self, _=None):
        """When contact is chosen, auto-fill company."""
        c = self._get_selected_customer()
        if c:
            self.company_var.set(c["company_name"])
            # Re-filter contact list to this company's contacts
            contacts = [
                x["customer_name"] for x in self.customers_raw
                if x["company_name"] == c["company_name"]
            ]
            self.contact_menu.configure(values=contacts)

    def _on_customer_selected(self, _=None):
        """Legacy alias — kept for compatibility."""
        self._on_contact_selected()

    def _on_part_selected(self, _=None):
        p = self._get_selected_part()
        if p:
            self.price_lbl.configure(text=fmt_currency(p["selling_price"]))
            self.stock_lbl.configure(text=f"Stock available: {p['stock_count']} units")
            self._override_active = False
            self._set_qty_normal()
            self.warn_lbl.configure(text="")
            self._validate_qty()

    def _validate_qty(self, _=None):
        p = self._get_selected_part()
        if not p:
            return
        try:
            qty = int(self.qty_entry.get())
        except ValueError:
            return
        if qty > p["stock_count"] and not self._override_active:
            self._set_qty_warning()
        else:
            self._set_qty_normal()

    def _set_qty_warning(self):
        self.qty_frame.configure(highlightbackground=C["red_bdr"])
        self.qty_entry.configure(bg=C["red_field"])
        self.warn_lbl.configure(text="⚠ Quantity exceeds current stock!")

    def _set_qty_normal(self):
        self.qty_frame.configure(highlightbackground=C["input_bdr"])
        self.qty_entry.configure(bg=C["input_bg"])
        self.warn_lbl.configure(text="")

    def _activate_override(self):
        if messagebox.askyesno(
            "Manager Override",
            "Override stock validation?\n"
            "This allows the invoice to exceed current stock count.\n\nProceed?",
        ):
            self._override_active = True
            self._set_qty_normal()
            self.warn_lbl.configure(
                text="✓ Override active — stock limit bypassed.", fg=C["override"]
            )

    def _add_line_item(self):
        p = self._get_selected_part()
        if not p:
            messagebox.showwarning("No Item", "Please select an item first.")
            return
        try:
            qty = int(self.qty_entry.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Qty", "Please enter a valid quantity ≥ 1.")
            return

        line_total = qty * float(p["selling_price"])
        self.line_items.append({
            "part_number": p["part_number"],
            "description": p["description"],
            "quantity": qty,
            "unit_price": float(p["selling_price"]),
            "line_total": line_total,
        })
        self._refresh_items_list()
        self._update_total()
        self.part_var.set("Select Item…")
        self.qty_entry.delete(0, "end")
        self.qty_entry.insert(0, "1")
        self.price_lbl.configure(text="—")
        self.stock_lbl.configure(text="")
        self.warn_lbl.configure(text="", fg=C["danger"])
        self._override_active = False
        self._set_qty_normal()

    def _refresh_items_list(self):
        for w in self.items_frame.winfo_children():
            w.destroy()
        if not self.line_items:
            tk.Label(self.items_frame, text="No items added yet.", font=FONT_SMALL,
                     bg=C["panel"], fg=C["text_light"]).pack(anchor="w")
            return

        hdr = tk.Frame(self.items_frame, bg=C["hdr_bg"])
        hdr.pack(fill="x")
        for txt, w in [("Item", 14), ("Qty", 4), ("Unit", 7), ("Total", 8), ("", 2)]:
            tk.Label(hdr, text=txt, font=FONT_SMALL, bg=C["hdr_bg"],
                     fg=C["text_muted"], width=w, anchor="w").pack(side="left", padx=4, pady=2)

        for i, item in enumerate(self.line_items):
            bg = C["row_alt"] if i % 2 else C["panel"]
            row = tk.Frame(self.items_frame, bg=bg)
            row.pack(fill="x")
            tk.Label(row, text=item["description"][:18], font=FONT_SMALL,
                     bg=bg, fg=C["text"], width=14, anchor="w").pack(side="left", padx=4, pady=3)
            tk.Label(row, text=str(item["quantity"]), font=FONT_SMALL,
                     bg=bg, fg=C["text"], width=4, anchor="w").pack(side="left")
            tk.Label(row, text=fmt_currency(item["unit_price"]), font=FONT_SMALL,
                     bg=bg, fg=C["text"], width=7, anchor="w").pack(side="left")
            tk.Label(row, text=fmt_currency(item["line_total"]), font=FONT_SMALL,
                     bg=bg, fg=C["text"], width=8, anchor="w").pack(side="left")
            idx = i
            tk.Button(row, text="✕", bg=bg, fg=C["danger"],
                      font=("Segoe UI", 8, "bold"), relief="flat", bd=0,
                      cursor="hand2", command=lambda ii=idx: self._remove_item(ii),
                      ).pack(side="left")

    def _remove_item(self, idx):
        if 0 <= idx < len(self.line_items):
            self.line_items.pop(idx)
            self._refresh_items_list()
            self._update_total()

    def _update_total(self):
        total = sum(i["line_total"] for i in self.line_items)
        self.total_lbl.configure(text=fmt_currency(total))

    def _submit(self):
        cust = self._get_selected_customer()
        if not cust:
            messagebox.showwarning("Missing Customer", "Please select a customer.")
            return
        if not self.line_items:
            messagebox.showwarning("No Items", "Please add at least one item.")
            return

        # Re-validate all quantities >= 1
        for item in self.line_items:
            if not isinstance(item.get("quantity"), int) or item["quantity"] < 1:
                messagebox.showwarning(
                    "Invalid Quantity",
                    f"Item '{item['description']}' has an invalid quantity. "
                    "All quantities must be >= 1.",
                )
                return

        # Recalculate total client-side (SUM qty * selling_price per line)
        total = round(sum(
            item["quantity"] * item["unit_price"] for item in self.line_items
        ), 2)

        self.on_create({
            "customer_number":  cust["customer_number"],
            "customer_name":    cust["customer_name"],
            "company_name":     cust["company_name"],
            "items":            self.line_items,
            "total":            total,
            "manager_override": self._override_active,
        })


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN VIEW
# ══════════════════════════════════════════════════════════════════════════════
class OrdersView(ctk.CTkFrame):
    """Tab 3 – Orders & Invoices"""

    def __init__(self, master, controller, db_config=None, role="Manager", **kw):
        super().__init__(master, fg_color=C["bg"], **kw)
        self.controller = controller
        self.db_config = db_config
        self.role = getattr(controller, "session", None) and controller.session.role or role

        self.invoices: list[dict] = []
        self.customers_raw: list[dict] = []
        self.parts: list[dict] = []

        # Build the DB access object (None if no config / no psycopg2)
        self.db: "OrdersDB | None" = None
        if HAS_DB and db_config:
            try:
                self.db = OrdersDB(db_config)
            except Exception as exc:
                print(f"[OrdersView] Could not create OrdersDB: {exc}")

        self._load_data()
        self._build()

    # ------------------------------------------------------------------
    # DATA LOADING
    # ------------------------------------------------------------------

    def _load_data(self):
        """Fetch live data from PostgreSQL; fall back to demo data on any error."""
        if self.db:
            try:
                self.invoices = self.db.fetch_invoices()
                self.customers_raw = self.db.fetch_active_customers()
                self.parts = self.db.fetch_parts()
                print(f"[OrdersView] Loaded {len(self.invoices)} invoices, "
                      f"{len(self.customers_raw)} customers, {len(self.parts)} parts from DB.")
                return
            except Exception as exc:
                print(f"[OrdersView] DB load failed: {exc} — using demo data.")

        # ── Demo fallback ─────────────────────────────────────────────────────
        self.invoices = DEMO_INVOICES[:]
        # Wrap demo customers to match the {customer_number, company_name} shape
        self.customers_raw = [
            {"customer_number": i + 1, "company_name": name}
            for i, name in enumerate(DEMO_CUSTOMERS)
        ]
        self.parts = DEMO_PARTS[:]

    # ------------------------------------------------------------------
    # BUILD
    # ------------------------------------------------------------------

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Title bar ─────────────────────────────────────────────────────────
        title_bar = tk.Frame(self, bg=C["bg"])
        title_bar.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 4))

        tk.Label(title_bar, text="Orders & Invoices", font=FONT_H1,
                 bg=C["bg"], fg=C["text"]).pack(side="left")
        tk.Label(title_bar,
                 text=f"  ·  {date.today().strftime('%B %d, %Y')}",
                 font=("Segoe UI", 11), bg=C["bg"], fg=C["text_muted"]
                 ).pack(side="left", pady=4)

        # DB connection indicator
        db_indicator = "🟢 Live DB" if self.db else "🟡 Demo Mode"
        tk.Label(title_bar, text=db_indicator, font=("Segoe UI", 9),
                 bg=C["bg"], fg=C["success"] if self.db else C["warn"]
                 ).pack(side="right", pady=4)

        # ── KPI Bar ───────────────────────────────────────────────────────────
        self.kpi_bar = KPIBar(self, self.invoices)
        self.kpi_bar.grid(row=1, column=0, sticky="ew", padx=24, pady=(4, 0))

        # ── 2-column split ────────────────────────────────────────────────────
        split = tk.Frame(self, bg=C["bg"])
        split.grid(row=2, column=0, sticky="nsew", padx=24, pady=10)
        split.grid_columnconfigure(0, weight=1)
        split.grid_columnconfigure(1, minsize=310, weight=0)
        split.grid_rowconfigure(0, weight=1)

        # Left: Manage Invoices
        self.manage_panel = ManageInvoicesPanel(
            split,
            invoices=self.invoices,
            role=self.role,
            on_status_change=self._on_status_change,
            db=self.db,
        )
        self.manage_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Right: Create Invoice
        self.create_panel = CreateInvoicePanel(
            split,
            customers=self.customers_raw,
            parts=self.parts,
            role=self.role,
            on_create=self._on_invoice_created,
            db=self.db,
            width=310,
        )
        self.create_panel.grid(row=0, column=1, sticky="nsew")
        self.create_panel.grid_propagate(False)

    # ------------------------------------------------------------------
    # EVENT HANDLERS
    # ------------------------------------------------------------------

    def _on_invoice_created(self, data: dict):
        """Persist new invoice to DB, then update the UI."""
        employee_number = (
            getattr(self.controller.session, "employee_number", None)
            if hasattr(self.controller, "session") else None
        )

        if self.db and employee_number:
            try:
                result = self.db.create_invoice(
                    customer_number=data["customer_number"],
                    employee_number=employee_number,
                    line_items=data["items"],
                    total=data["total"],
                    manager_override=data.get("manager_override", False),
                )
                new_inv = {
                    "invoice_id":     result["invoice_id"],
                    "invoice_number": result["invoice_number"],
                    "customer_name":  data["customer_name"],
                    "company_name":   data["company_name"],
                    "customer_address": data.get("customer_address", "—"),
                    "customer_number": data["customer_number"],
                    "amount":         result["total"],
                    "status":         "active",
                    "date":           result["date"],
                    "sales_rep":      getattr(self.controller.session, "employee_name", "—"),
                    "employee_number": employee_number,
                }
            except ValueError as exc:
                # Validation errors from OrdersDB.validate_order
                messagebox.showerror("Order Validation Failed", str(exc))
                return
            except Exception as exc:
                messagebox.showerror("Database Error",
                                     f"Could not save invoice to database:\n{exc}")
                return
        else:
            # Demo / no-session fallback
            fallback_id = len(self.invoices) + 1300
            new_inv = {
                "invoice_id":     fallback_id,
                "invoice_number": f"INV-{fallback_id}",
                "customer_name":  data["customer_name"],
                "company_name":   data.get("company_name", "—"),
                "customer_address": data.get("customer_address", "—"),
                "customer_number": data["customer_number"],
                "amount":         data["total"],
                "status":         "active",
                "date":           date.today().isoformat(),
                "sales_rep":      getattr(
                    getattr(self.controller, "session", None),
                    "employee_name", "Current User"
                ),
            }

        self.invoices.insert(0, new_inv)
        self.manage_panel.invoices = self.invoices
        self.manage_panel.add_invoice(new_inv)

        # Rebuild KPI bar
        self.kpi_bar.destroy()
        self.kpi_bar = KPIBar(self, self.invoices)
        self.kpi_bar.grid(row=1, column=0, sticky="ew", padx=24, pady=(4, 0))

        messagebox.showinfo(
            "Invoice Created",
            f"Invoice {new_inv['invoice_number']} saved successfully!\n"
            f"Customer: {data['customer_name']}\n"
            f"Total: {fmt_currency(data['total'])}\n"
            f"Items: {len(data['items'])}",
        )

        # Reset the create panel
        self.create_panel.line_items.clear()
        self.create_panel._refresh_items_list()
        self.create_panel._update_total()
        self.create_panel.cust_var.set("Select Contact…")
        self.create_panel.company_var.set("Select Company…")
        self.create_panel.company_lbl.configure(text="—", fg=C["text_muted"])
        self.create_panel.part_var.set("Select Item…")
        self.create_panel.price_lbl.configure(text="—")
        self.create_panel.stock_lbl.configure(text="")

    def _on_status_change(self, inv_id, inv_number, new_status):
        """Rebuild KPI after any status transition (DB write already done in ManagePanel)."""
        print(f"[OrdersView] Status change: {inv_number} (id={inv_id}) → {new_status}")
        self.kpi_bar.destroy()
        self.kpi_bar = KPIBar(self, self.invoices)
        self.kpi_bar.grid(row=1, column=0, sticky="ew", padx=24, pady=(4, 0))


# ══════════════════════════════════════════════════════════════════════════════
#  DEMO DATA  (fallback when DB is unavailable)
# ══════════════════════════════════════════════════════════════════════════════
DEMO_INVOICES = [
    {"invoice_id": 1201, "invoice_number": "INV-1201", "customer_name": "Maria Santos", "company_name": "ABC Solutions",
     "amount": 1450.00, "status": "active",  "date": "2006-08-07", "sales_rep": "Maria G.", "customer_number": 1},
    {"invoice_id": 1202, "invoice_number": "INV-1202", "customer_name": "John Dela Cruz", "company_name": "Global Corp",
     "amount": 3230.00, "status": "shipped", "date": "2006-08-06", "sales_rep": "John D.",  "customer_number": 2},
    {"invoice_id": 1203, "invoice_number": "INV-1203", "customer_name": "Ana Reyes", "company_name": "Enterprise Inc.",
     "amount": 1550.00, "status": "active",  "date": "2006-08-05", "sales_rep": "Maria G.", "customer_number": 3},
    {"invoice_id": 1204, "invoice_number": "INV-1204", "customer_name": "Maria Santos", "company_name": "ABC Solutions",
     "amount": 1450.00, "status": "paid",    "date": "2006-08-04", "sales_rep": "Ken C.",   "customer_number": 1},
    {"invoice_id": 1205, "invoice_number": "INV-1205", "customer_name": "John Dela Cruz", "company_name": "Global Corp",
     "amount": 1250.00, "status": "active",  "date": "2006-08-03", "sales_rep": "John D.",  "customer_number": 2},
]

DEMO_CUSTOMERS = [
    "Acme Corp", "ABC Solutions", "Global Corp", "Enterprise Inc.",
    "Beta Solutions", "Global Logistics", "Springfield Inc.",
    "Gamma Co.", "Delta Ltd.", "Omega Holdings",
]

DEMO_PARTS = [
    {"part_number": 1,  "description": "NOS Copy Paper A4 - 500 Sheets",   "selling_price": 12.99,  "stock_count": 1500},
    {"part_number": 2,  "description": "Standard Pens Box (Blue, 12pk)",    "selling_price": 4.50,   "stock_count": 420},
    {"part_number": 3,  "description": "Manila Folders Pack (25pk)",         "selling_price": 8.00,   "stock_count": 960},
    {"part_number": 4,  "description": "Heavy Duty Stapler",                 "selling_price": 25.00,  "stock_count": 2},
    {"part_number": 5,  "description": "USB-C Cables 6ft",                   "selling_price": 15.50,  "stock_count": 210},
    {"part_number": 6,  "description": "Ergonomic Task Chair",               "selling_price": 299.00, "stock_count": 0},
    {"part_number": 7,  "description": "Whiteboard Markers (8pk)",           "selling_price": 6.75,   "stock_count": 85},
    {"part_number": 8,  "description": "Executive Gel Pen Black 12pk",       "selling_price": 18.50,  "stock_count": 450},
    {"part_number": 9,  "description": "Wireless Keyboard Ultra-Compact",    "selling_price": 89.00,  "stock_count": 8},
    {"part_number": 10, "description": "Monitor Mount Arm Dual Screen",      "selling_price": 145.00, "stock_count": 15},
]
