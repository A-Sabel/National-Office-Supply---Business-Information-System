"""
orders_and_invoices.py  –  Tab 3: Orders & Invoices
National Office Supplies BIS
──────────────────────────────────────
Drop this file in:  frontend/tabs/orders_and_invoices.py

Wire it up in __main__.py:
    from frontend.tabs.orders_and_invoices import OrdersView

    def show_orders(self):
        self._clear_content()
        db_config = {
            "dbname": "nos_stockdb",
            "user":   "postgres",
            "password": "maomao220",
            "host":   "localhost",
            "port":   5432,
        }
        self.current_view = OrdersView(
            self.content_container, controller=self, db_config=db_config
        )
        self.current_view.grid(row=0, column=0, sticky="nsew")
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from datetime import date

# ── optional DB import ─────────────────────────────────────────────────────────
try:
    import psycopg2
    import psycopg2.extras
    HAS_DB = True
except ImportError:
    HAS_DB = False


# ══════════════════════════════════════════════════════════════════════════════
#  COLOUR & FONT TOKENS
# ══════════════════════════════════════════════════════════════════════════════
C = {
    "bg":          "#f8f9fa",
    "panel":       "#ffffff",
    "border":      "#e2e8f0",
    "accent":      "#2563eb",
    "accent_h":    "#1d4ed8",
    "danger":      "#dc2626",
    "warn":        "#d97706",
    "success":     "#16a34a",
    "shipped":     "#7c3aed",
    "paid":        "#0d9488",
    "void":        "#6b7280",
    "text":        "#0f172a",
    "text_muted":  "#64748b",
    "text_light":  "#94a3b8",
    "row_alt":     "#f8fafc",
    "row_hover":   "#eff6ff",
    "input_bg":    "#f8fafc",
    "input_bdr":   "#cbd5e1",
    "red_field":   "#fee2e2",
    "red_bdr":     "#ef4444",
    "override":    "#7c3aed",
    "override_h":  "#6d28d9",
    "hdr_bg":      "#f1f5f9",
}

FONT        = ("Segoe UI", 10)
FONT_BOLD   = ("Segoe UI", 10, "bold")
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 10)
FONT_H1     = ("Segoe UI", 20, "bold")
FONT_H3     = ("Segoe UI", 12, "bold")


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
    bg  = bg_override if bg_override else cfg["bg"]
    lbl = tk.Label(parent, text=cfg["label"],
                   bg=bg, fg=cfg["fg"],
                   font=("Segoe UI", 8, "bold"),
                   padx=8, pady=3, relief="flat", bd=0)
    return lbl

def fmt_currency(val):
    try:
        return f"₱{float(val):,.2f}"
    except Exception:
        return str(val)


# ══════════════════════════════════════════════════════════════════════════════
#  KPI BAR
# ══════════════════════════════════════════════════════════════════════════════
class KPIBar(tk.Frame):
    def __init__(self, master, invoices, **kw):
        super().__init__(master, bg=C["bg"], **kw)
        self.invoices = invoices
        self._build()

    def _build(self):
        totals  = sum(i["amount"] for i in self.invoices)
        active  = sum(1 for i in self.invoices if i["status"] == "active")
        shipped = sum(1 for i in self.invoices if i["status"] == "shipped")
        paid    = sum(1 for i in self.invoices if i["status"] == "paid")

        cards = [
            ("Total Invoices",   str(len(self.invoices)), C["accent"]),
            ("Total Revenue",    fmt_currency(totals),    C["success"]),
            ("Pending / Active", str(active),             C["warn"]),
            ("Shipped",          str(shipped),            C["shipped"]),
            ("Paid",             str(paid),               C["paid"]),
        ]
        for title, val, clr in cards:
            card = tk.Frame(self, bg=C["panel"],
                            highlightthickness=1,
                            highlightbackground=C["border"])
            card.pack(side="left", padx=(0, 10), pady=6, ipadx=14, ipady=8)
            tk.Frame(card, bg=clr, width=4).pack(side="left", fill="y")
            inner = tk.Frame(card, bg=C["panel"])
            inner.pack(side="left", padx=10, pady=4)
            tk.Label(inner, text=title, font=FONT_SMALL,
                     bg=C["panel"], fg=C["text_muted"]).pack(anchor="w")
            tk.Label(inner, text=val,
                     font=("Segoe UI", 15, "bold"),
                     bg=C["panel"], fg=clr).pack(anchor="w")


# ══════════════════════════════════════════════════════════════════════════════
#  INVOICE DETAIL POPUP
# ══════════════════════════════════════════════════════════════════════════════
class InvoiceDetailDialog(tk.Toplevel):
    def __init__(self, master, invoice, role, on_status_change):
        super().__init__(master)
        self.title(f"Invoice Details — {invoice['invoice_number']}")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        inv = invoice

        # Header bar
        hdr = tk.Frame(self, bg=C["accent"], height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"Invoice  {inv['invoice_number']}",
                 font=("Segoe UI", 14, "bold"),
                 bg=C["accent"], fg="white").pack(side="left", padx=20, pady=14)
        badge = status_badge(hdr, inv["status"], bg_override="white")
        badge.pack(side="right", padx=20, pady=14)

        body = tk.Frame(self, bg=C["bg"], padx=28, pady=18)
        body.pack(fill="both", expand=True)

        def field_row(label, value):
            r = tk.Frame(body, bg=C["bg"])
            r.pack(fill="x", pady=3)
            tk.Label(r, text=label, width=16, anchor="w",
                     font=FONT_BOLD, bg=C["bg"], fg=C["text_muted"]).pack(side="left")
            tk.Label(r, text=value, anchor="w",
                     font=FONT, bg=C["bg"], fg=C["text"]).pack(side="left")

        field_row("Customer:",    inv.get("customer_name", "—"))
        field_row("Date Written:", inv.get("date", "—"))
        field_row("Sales Rep:",   inv.get("sales_rep", "—"))
        field_row("Amount Due:",  fmt_currency(inv.get("amount", 0)))

        tk.Frame(body, bg=C["border"], height=1).pack(fill="x", pady=10)

        status = inv["status"].lower()
        action_frame = tk.Frame(body, bg=C["bg"])
        action_frame.pack(fill="x", pady=4)

        def do_ship():
            on_status_change(inv["invoice_number"], "shipped")
            self.destroy()

        def do_paid():
            on_status_change(inv["invoice_number"], "paid")
            self.destroy()

        def do_void():
            if messagebox.askyesno("Confirm Void",
                                   f"Void invoice {inv['invoice_number']}?\nThis cannot be undone."):
                on_status_change(inv["invoice_number"], "void")
                self.destroy()

        if status == "active":
            tk.Label(action_frame, text="Status Actions:", font=FONT_BOLD,
                     bg=C["bg"], fg=C["text_muted"]).pack(anchor="w", pady=(0, 6))
            btn_row = tk.Frame(action_frame, bg=C["bg"])
            btn_row.pack(anchor="w")
            tk.Button(btn_row, text="✓  Mark Shipped",
                      bg=C["shipped"], fg="white", font=("Segoe UI", 10, "bold"),
                      relief="flat", bd=0, padx=12, pady=6,
                      cursor="hand2", command=do_ship).pack(side="left", padx=(0, 8))
            tk.Button(btn_row, text="✕  Void",
                      bg=C["danger"], fg="white", font=("Segoe UI", 10, "bold"),
                      relief="flat", bd=0, padx=12, pady=6,
                      cursor="hand2", command=do_void).pack(side="left")

        elif status == "shipped":
            tk.Label(action_frame, text="Status Actions:", font=FONT_BOLD,
                     bg=C["bg"], fg=C["text_muted"]).pack(anchor="w", pady=(0, 6))
            tk.Button(action_frame, text="💳  Mark Paid",
                      bg=C["paid"], fg="white", font=("Segoe UI", 10, "bold"),
                      relief="flat", bd=0, padx=12, pady=6,
                      cursor="hand2", command=do_paid).pack(anchor="w")

        elif status in ("paid", "void"):
            tk.Label(action_frame,
                     text="🔒  This invoice is fully locked (no further actions).",
                     font=FONT_SMALL, bg=C["bg"], fg=C["text_muted"]).pack(anchor="w")

        tk.Frame(body, bg=C["border"], height=1).pack(fill="x", pady=10)
        ctk.CTkButton(body, text="Close", width=100, height=32,
                      fg_color=C["border"], text_color=C["text"],
                      hover_color="#cbd5e1",
                      command=self.destroy).pack(anchor="e")

        self.update_idletasks()
        w, h = 460, self.winfo_reqheight()
        x = master.winfo_rootx() + (master.winfo_width() - w) // 2
        y = master.winfo_rooty() + 80
        self.geometry(f"{w}x{h}+{x}+{y}")


# ══════════════════════════════════════════════════════════════════════════════
#  MANAGE INVOICES PANEL
# ══════════════════════════════════════════════════════════════════════════════
class ManageInvoicesPanel(ctk.CTkFrame):


    def __init__(self, master, invoices, role, on_status_change, **kw):
        super().__init__(master, fg_color=C["panel"],
                         corner_radius=12, border_width=1,
                         border_color=C["border"], **kw)
        self.invoices         = list(invoices)
        self.filtered         = list(invoices)
        self.role             = role
        self.on_status_change = on_status_change
        self._build()

    def _build(self):
        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = tk.Frame(self, bg=C["panel"])
        toolbar.pack(fill="x", padx=16, pady=(14, 8))

        tk.Label(toolbar, text="Manage Invoices",
                 font=("Segoe UI", 13, "bold"),
                 bg=C["panel"], fg=C["text"]).pack(side="left")

        # Filter dropdown
        self.filter_var = tk.StringVar(value="All Status")
        filter_menu = ctk.CTkOptionMenu(
            toolbar, variable=self.filter_var,
            values=["All Status", "active", "shipped", "paid", "void"],
            fg_color=C["input_bg"], button_color=C["accent"],
            text_color=C["text"], width=120, height=28,
            command=self._apply_filter)
        filter_menu.pack(side="right", padx=(6, 0))

        # Search box
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        sb = tk.Frame(toolbar, bg=C["input_bg"],
                      highlightthickness=1,
                      highlightbackground=C["input_bdr"])
        sb.pack(side="right", padx=(0, 8))
        tk.Label(sb, text="🔍", bg=C["input_bg"],
                 font=("Segoe UI", 9)).pack(side="left", padx=(6, 0))
        tk.Entry(sb, textvariable=self.search_var,
                 font=FONT, relief="flat", width=16,
                 bg=C["input_bg"], fg=C["text"],
                 insertbackground=C["text"]).pack(side="left", padx=4, pady=3)

        # ── Column headers ────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=C["hdr_bg"],
                       highlightthickness=1,
                       highlightbackground=C["border"])
        hdr.pack(fill="x", padx=16, pady=(0, 0))
        col_defs = [
            ("Invoice #",     13),
            ("Customer Name", 24),
            ("Amount",        14),
            ("Status",        14),
            ("Date",          13),
            ("Actions",        0),  # fills remaining space
        ]
        for txt, w in col_defs:
            kw = dict(font=FONT_BOLD, bg=C["hdr_bg"], fg=C["text_muted"],
                      anchor="w", padx=8, pady=7)
            if w:
                tk.Label(hdr, text=txt, width=w, **kw).pack(side="left")
            else:
                tk.Label(hdr, text=txt, **kw).pack(side="left", fill="x", expand=True)

        # ── Scrollable rows ───────────────────────────────────────────────────
        self.rows_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.rows_frame.pack(fill="both", expand=True, padx=16, pady=(2, 12))
        self._render_rows()

    def _apply_filter(self, _=None):
        q      = self.search_var.get().lower()
        status = self.filter_var.get()
        self.filtered = [
            inv for inv in self.invoices
            if (status == "All Status" or inv["status"].lower() == status)
            and (q in inv["invoice_number"].lower()
                 or q in inv["customer_name"].lower())
        ]
        self._render_rows()

    def _render_rows(self):
        for w in self.rows_frame.winfo_children():
            w.destroy()

        if not self.filtered:
            tk.Label(self.rows_frame, text="No invoices found.",
                     font=FONT, bg=C["panel"],
                     fg=C["text_muted"]).pack(pady=30)
            return

        for i, inv in enumerate(self.filtered):
            bg = C["row_alt"] if i % 2 else C["panel"]
            row = tk.Frame(self.rows_frame, bg=bg)
            row.pack(fill="x", pady=0)

            # separator line
            tk.Frame(self.rows_frame, bg=C["border"], height=1).pack(fill="x")

            # hover
            def _enter(e, r=row, b=bg): r.configure(bg=C["row_hover"])
            def _leave(e, r=row, b=bg): r.configure(bg=b)
            row.bind("<Enter>", _enter)
            row.bind("<Leave>", _leave)

            inv_ref = inv

            # ── Invoice # ──
            tk.Label(row, text=inv["invoice_number"],
                     font=FONT_MONO, bg=bg, fg=C["text"],
                     width=13, anchor="w").pack(side="left", padx=(12, 4), pady=9)

            # ── Customer Name ──
            tk.Label(row, text=inv["customer_name"],
                     font=FONT, bg=bg, fg=C["text"],
                     width=24, anchor="w").pack(side="left", padx=8, pady=9)

            # ── Amount ──
            tk.Label(row, text=fmt_currency(inv["amount"]),
                     font=FONT, bg=bg, fg=C["text"],
                     width=14, anchor="w").pack(side="left", padx=8, pady=9)

            # ── Status badge ──
            badge_cell = tk.Frame(row, bg=bg, width=100)
            badge_cell.pack(side="left", padx=8, pady=6)
            badge_cell.pack_propagate(False)
            status_badge(badge_cell, inv["status"]).pack(anchor="w", pady=3)

            # ── Date ──
            tk.Label(row, text=inv.get("date", ""),
                     font=FONT_SMALL, bg=bg, fg=C["text_muted"],
                     width=13, anchor="w").pack(side="left", padx=8, pady=9)

            # ── Actions (fills remaining space) ──
            act = tk.Frame(row, bg=bg)
            act.pack(side="left", fill="x", expand=True, padx=8, pady=6)

            s = inv["status"].lower()

            # View Details — always visible
            tk.Button(act, text="View Details",
                      bg=C["accent"], fg="white",
                      font=("Segoe UI", 8, "bold"),
                      relief="flat", bd=0, padx=10, pady=5,
                      cursor="hand2",
                      command=lambda iv=inv_ref: self._open_detail(iv)
                      ).pack(side="left", padx=(0, 4))

            # Status transition buttons
            if s == "active":
                tk.Button(act, text="Mark Shipped",
                          bg=C["shipped"], fg="white",
                          font=("Segoe UI", 8, "bold"),
                          relief="flat", bd=0, padx=10, pady=5,
                          cursor="hand2",
                          command=lambda iv=inv_ref: self._quick_action(iv, "shipped")
                          ).pack(side="left", padx=(0, 4))
                tk.Button(act, text="Void",
                          bg=C["danger"], fg="white",
                          font=("Segoe UI", 8, "bold"),
                          relief="flat", bd=0, padx=10, pady=5,
                          cursor="hand2",
                          command=lambda iv=inv_ref: self._quick_action(iv, "void")
                          ).pack(side="left")
            elif s == "shipped":
                tk.Button(act, text="Mark Paid",
                          bg=C["paid"], fg="white",
                          font=("Segoe UI", 8, "bold"),
                          relief="flat", bd=0, padx=10, pady=5,
                          cursor="hand2",
                          command=lambda iv=inv_ref: self._quick_action(iv, "paid")
                          ).pack(side="left")
            # paid / void → fully locked, no extra buttons

    def _open_detail(self, inv):
        InvoiceDetailDialog(self.winfo_toplevel(), inv, self.role,
                            lambda num, st: self._update_status(num, st))

    def _quick_action(self, inv, new_status):
        if new_status == "void" and not messagebox.askyesno(
                "Confirm", f"Void invoice {inv['invoice_number']}?"):
            return
        self._update_status(inv["invoice_number"], new_status)

    def _update_status(self, inv_number, new_status):
        for inv in self.invoices:
            if inv["invoice_number"] == inv_number:
                inv["status"] = new_status
                break
        self.on_status_change(inv_number, new_status)
        self._apply_filter()

    def add_invoice(self, inv):
        # inv is already inserted into self.invoices by OrdersView._on_invoice_created
        # so we just refresh the filter/render
        self._apply_filter()


# ══════════════════════════════════════════════════════════════════════════════
#  CREATE INVOICE PANEL
# ══════════════════════════════════════════════════════════════════════════════
class CreateInvoicePanel(ctk.CTkFrame):
    def __init__(self, master, customers, parts, role, on_create, **kw):
        super().__init__(master, fg_color=C["panel"],
                         corner_radius=12, border_width=1,
                         border_color=C["border"], **kw)
        self.customers        = customers
        self.parts            = parts
        self.role             = role
        self.on_create        = on_create
        self.line_items       = []
        self._override_active = False
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=C["panel"])
        hdr.pack(fill="x", padx=20, pady=(16, 8))
        tk.Label(hdr, text="Create Invoice",
                 font=("Segoe UI", 13, "bold"),
                 bg=C["panel"], fg=C["text"]).pack(side="left")

        # Regular frame — no scrollbar needed
        body = tk.Frame(self, bg=C["panel"])
        body.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        def section(parent, text):
            tk.Label(parent, text=text, font=FONT_BOLD,
                     bg=C["panel"], fg=C["text_muted"]).pack(anchor="w", pady=(10, 2))

        # ── Select Customer ───────────────────────────────────────────────────
        section(body, "Select Customer")
        self.cust_var = tk.StringVar(value="Select Customer…")
        ctk.CTkOptionMenu(body, variable=self.cust_var,
                          values=self.customers,
                          fg_color=C["input_bg"],
                          button_color=C["accent"],
                          text_color=C["text"],
                          width=270, height=32
                          ).pack(anchor="w", pady=(0, 4))

        # ── Select Item ───────────────────────────────────────────────────────
        section(body, "Select Item")
        part_names = [p["description"] for p in self.parts]
        self.part_var = tk.StringVar(value="Select Item…")
        ctk.CTkOptionMenu(body, variable=self.part_var,
                          values=part_names,
                          fg_color=C["input_bg"],
                          button_color=C["accent"],
                          text_color=C["text"],
                          width=270, height=32,
                          command=self._on_part_selected
                          ).pack(anchor="w", pady=(0, 4))

        # ── Quantity ──────────────────────────────────────────────────────────
        section(body, "Quantity")
        qty_row = tk.Frame(body, bg=C["panel"])
        qty_row.pack(anchor="w", pady=(0, 2))

        self.qty_frame = tk.Frame(qty_row, bg=C["panel"],
                                  highlightthickness=1,
                                  highlightbackground=C["input_bdr"])
        self.qty_frame.pack(side="left")
        self.qty_entry = tk.Entry(self.qty_frame, width=6,
                                  font=FONT, relief="flat",
                                  bg=C["input_bg"], fg=C["text"],
                                  insertbackground=C["text"])
        self.qty_entry.insert(0, "1")
        self.qty_entry.pack(padx=8, pady=5)
        self.qty_entry.bind("<KeyRelease>", self._validate_qty)

        # Manager Override
        self.override_btn = tk.Button(qty_row, text="⚡ Manager Override",
                                      bg=C["override"], fg="white",
                                      font=("Segoe UI", 8, "bold"),
                                      relief="flat", bd=0, padx=10, pady=5,
                                      cursor="hand2",
                                      command=self._activate_override)
        if self.role == "Manager":
            self.override_btn.pack(side="left", padx=(8, 0))

        # Warnings
        self.warn_lbl = tk.Label(body, text="", fg=C["danger"],
                                 bg=C["panel"], font=("Segoe UI", 8, "bold"))
        self.warn_lbl.pack(anchor="w")

        self.stock_lbl = tk.Label(body, text="", fg=C["text_muted"],
                                  bg=C["panel"], font=FONT_SMALL)
        self.stock_lbl.pack(anchor="w", pady=(0, 4))

        # ── Price per Unit ────────────────────────────────────────────────────
        section(body, "Price per Unit")
        self.price_lbl = tk.Label(body, text="—", font=FONT,
                                  bg=C["panel"], fg=C["text"])
        self.price_lbl.pack(anchor="w", pady=(0, 4))

        # ── Add Line Item ─────────────────────────────────────────────────────
        ctk.CTkButton(body, text="+ Add Line Item",
                      fg_color=C["border"], text_color=C["text"],
                      hover_color="#cbd5e1",
                      height=30, width=270,
                      command=self._add_line_item
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
        tk.Label(total_row, text="Total", font=FONT_BOLD,
                 bg=C["panel"], fg=C["text"]).pack(side="left")
        self.total_lbl = tk.Label(total_row, text="₱0.00",
                                  font=("Segoe UI", 13, "bold"),
                                  bg=C["panel"], fg=C["accent"])
        self.total_lbl.pack(side="right")

        # ── Save Invoice ──────────────────────────────────────────────────────
        ctk.CTkButton(body, text="Save Invoice",
                      fg_color=C["accent"], hover_color=C["accent_h"],
                      height=36, width=270,
                      font=ctk.CTkFont("Segoe UI", 11, "bold"),
                      command=self._submit
                      ).pack(anchor="w", pady=(10, 4))

    # ── helpers ───────────────────────────────────────────────────────────────
    def _get_selected_part(self):
        name = self.part_var.get()
        for p in self.parts:
            if p["description"] == name:
                return p
        return None

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
        if messagebox.askyesno("Manager Override",
                               "Override stock validation?\n"
                               "This allows the invoice to exceed current stock count.\n\nProceed?"):
            self._override_active = True
            self._set_qty_normal()
            self.warn_lbl.configure(
                text="✓ Override active — stock limit bypassed.",
                fg=C["override"])

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
            "quantity":    qty,
            "unit_price":  float(p["selling_price"]),
            "line_total":  line_total,
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
            tk.Label(self.items_frame, text="No items added yet.",
                     font=FONT_SMALL, bg=C["panel"],
                     fg=C["text_light"]).pack(anchor="w")
            return

        hdr = tk.Frame(self.items_frame, bg=C["hdr_bg"])
        hdr.pack(fill="x")
        for txt, w in [("Item", 14), ("Qty", 4), ("Unit", 7), ("Total", 8), ("", 2)]:
            tk.Label(hdr, text=txt, font=FONT_SMALL,
                     bg=C["hdr_bg"], fg=C["text_muted"],
                     width=w, anchor="w").pack(side="left", padx=4, pady=2)

        for i, item in enumerate(self.line_items):
            bg = C["row_alt"] if i % 2 else C["panel"]
            row = tk.Frame(self.items_frame, bg=bg)
            row.pack(fill="x")
            tk.Label(row, text=item["description"][:18],
                     font=FONT_SMALL, bg=bg, fg=C["text"],
                     width=14, anchor="w").pack(side="left", padx=4, pady=3)
            tk.Label(row, text=str(item["quantity"]),
                     font=FONT_SMALL, bg=bg, fg=C["text"],
                     width=4, anchor="w").pack(side="left")
            tk.Label(row, text=fmt_currency(item["unit_price"]),
                     font=FONT_SMALL, bg=bg, fg=C["text"],
                     width=7, anchor="w").pack(side="left")
            tk.Label(row, text=fmt_currency(item["line_total"]),
                     font=FONT_SMALL, bg=bg, fg=C["text"],
                     width=8, anchor="w").pack(side="left")
            idx = i
            tk.Button(row, text="✕", bg=bg, fg=C["danger"],
                      font=("Segoe UI", 8, "bold"),
                      relief="flat", bd=0, cursor="hand2",
                      command=lambda ii=idx: self._remove_item(ii)
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
        if self.cust_var.get() == "Select Customer…":
            messagebox.showwarning("Missing Customer", "Please select a customer.")
            return
        if not self.line_items:
            messagebox.showwarning("No Items", "Please add at least one item.")
            return
        total = sum(i["line_total"] for i in self.line_items)
        self.on_create({
            "customer": self.cust_var.get(),
            "items":    self.line_items,
            "total":    total,
        })


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN VIEW
# ══════════════════════════════════════════════════════════════════════════════
class OrdersView(ctk.CTkFrame):
    """Tab 3 – Orders & Invoices"""

    def __init__(self, master, controller, db_config=None, role="Manager", **kw):
        super().__init__(master, fg_color=C["bg"], **kw)
        self.controller = controller
        self.db_config  = db_config
        self.role       = getattr(controller, "role", role)

        self.invoices  = []
        self.customers = []
        self.parts     = []

        self._load_data()
        self._build()

    def _load_data(self):
        if HAS_DB and self.db_config:
            try:
                conn = psycopg2.connect(**self.db_config)
                cur  = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

                cur.execute("""
                    SELECT i.invoice_number::text AS invoice_number,
                           c.company_name         AS customer_name,
                           i.total_amount         AS amount,
                           i.status,
                           i.date_written::text   AS date,
                           e.employee_name        AS sales_rep
                    FROM invoices i
                    JOIN customers c ON c.customer_number = i.customer_number
                    JOIN employees e ON e.employee_number = i.employee_number
                    ORDER BY i.date_written DESC
                    LIMIT 200
                """)
                self.invoices = [dict(r) for r in cur.fetchall()]

                cur.execute(
                    "SELECT company_name FROM customers WHERE is_active ORDER BY company_name")
                self.customers = [r[0] for r in cur.fetchall()]

                cur.execute(
                    "SELECT part_number, description, selling_price, stock_count "
                    "FROM parts ORDER BY description")
                self.parts = [dict(r) for r in cur.fetchall()]

                conn.close()
                return
            except Exception as exc:
                print(f"[OrdersView] DB error: {exc}")

        # Fallback demo data
        self.invoices  = DEMO_INVOICES[:]
        self.customers = DEMO_CUSTOMERS[:]
        self.parts     = DEMO_PARTS[:]

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Title bar ─────────────────────────────────────────────────────────
        title_bar = tk.Frame(self, bg=C["bg"])
        title_bar.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 4))

        tk.Label(title_bar, text="Orders & Invoices",
                 font=FONT_H1, bg=C["bg"], fg=C["text"]).pack(side="left")
        tk.Label(title_bar,
                 text=f"  ·  {date.today().strftime('%B %d, %Y')}",
                 font=("Segoe UI", 11), bg=C["bg"],
                 fg=C["text_muted"]).pack(side="left", pady=4)



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
        )
        self.manage_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Right: Create Invoice
        self.create_panel = CreateInvoicePanel(
            split,
            customers=self.customers,
            parts=self.parts,
            role=self.role,
            on_create=self._on_invoice_created,
            width=310,
        )
        self.create_panel.grid(row=0, column=1, sticky="nsew")
        self.create_panel.grid_propagate(False)

    def _on_invoice_created(self, data):
        inv_num = f"INV-{len(self.invoices) + 1300}"
        new_inv = {
            "invoice_number": inv_num,
            "customer_name":  data["customer"],
            "amount":         data["total"],
            "status":         "active",
            "date":           date.today().isoformat(),
            "sales_rep":      getattr(self.controller, "username", "Current User"),
        }
        # Insert into master list first, then sync the panel reference
        self.invoices.insert(0, new_inv)
        self.manage_panel.invoices = self.invoices
        self.manage_panel.add_invoice(new_inv)

        # Rebuild KPI bar so the counters update immediately
        self.kpi_bar.destroy()
        self.kpi_bar = KPIBar(self, self.invoices)
        self.kpi_bar.grid(row=1, column=0, sticky="ew", padx=24, pady=(4, 0))

        messagebox.showinfo(
            "Invoice Created",
            f"Invoice {inv_num} created successfully!\n"
            f"Customer: {data['customer']}\n"
            f"Total: {fmt_currency(data['total'])}\n"
            f"Items: {len(data['items'])}"
        )

    def _on_status_change(self, inv_number, new_status):
        print(f"[OrdersView] Status change: {inv_number} → {new_status}")

# ══════════════════════════════════════════════════════════════════════════════
#  DEMO DATA
# ══════════════════════════════════════════════════════════════════════════════
DEMO_INVOICES = [
    {"invoice_number": "INV-1201", "customer_name": "ABC Solutions",   "amount": 1450.00, "status": "active",  "date": "2006-08-07", "sales_rep": "Maria G."},
    {"invoice_number": "INV-1202", "customer_name": "Global Corp",     "amount": 3230.00, "status": "shipped", "date": "2006-08-06", "sales_rep": "John D."},
    {"invoice_number": "INV-1203", "customer_name": "Enterprise Inc.", "amount": 1550.00, "status": "active",  "date": "2006-08-05", "sales_rep": "Maria G."},
    {"invoice_number": "INV-1204", "customer_name": "ABC Solutions",   "amount": 1450.00, "status": "paid",    "date": "2006-08-04", "sales_rep": "Ken C."},
    {"invoice_number": "INV-1205", "customer_name": "Global Corp",     "amount": 1250.00, "status": "active",  "date": "2006-08-03", "sales_rep": "John D."},
    {"invoice_number": "INV-1207", "customer_name": "Enterprise Inc.", "amount": 3200.00, "status": "paid",    "date": "2006-08-02", "sales_rep": "Maria G."},
    {"invoice_number": "INV-1208", "customer_name": "Global Corp",     "amount": 1800.00, "status": "void",    "date": "2006-08-01", "sales_rep": "Ken C."},
    {"invoice_number": "INV-1209", "customer_name": "Enterprise Inc.", "amount": 1450.00, "status": "active",  "date": "2006-07-31", "sales_rep": "John D."},
    {"invoice_number": "INV-1210", "customer_name": "Enterprise Inc.", "amount": 2900.00, "status": "shipped", "date": "2006-07-30", "sales_rep": "Maria G."},
    {"invoice_number": "INV-1211", "customer_name": "Global Corp",     "amount": 1350.00, "status": "paid",    "date": "2006-07-29", "sales_rep": "Ken C."},
    {"invoice_number": "INV-1212", "customer_name": "Enterprise Inc.", "amount": 1490.00, "status": "shipped", "date": "2006-07-28", "sales_rep": "John D."},
]

DEMO_CUSTOMERS = [
    "Acme Corp", "ABC Solutions", "Global Corp",
    "Enterprise Inc.", "Beta Solutions", "Global Logistics",
    "Springfield Inc.", "Gamma Co.", "Delta Ltd.", "Omega Holdings",
]

DEMO_PARTS = [
    {"part_number": 1,  "description": "NOS Copy Paper A4 - 500 Sheets", "selling_price": 12.99,  "stock_count": 1500},
    {"part_number": 2,  "description": "Standard Pens Box (Blue, 12pk)", "selling_price": 4.50,   "stock_count": 420},
    {"part_number": 3,  "description": "Manila Folders Pack (25pk)",      "selling_price": 8.00,   "stock_count": 960},
    {"part_number": 4,  "description": "Heavy Duty Stapler",              "selling_price": 25.00,  "stock_count": 2},
    {"part_number": 5,  "description": "USB-C Cables 6ft",               "selling_price": 15.50,  "stock_count": 210},
    {"part_number": 6,  "description": "Ergonomic Task Chair",           "selling_price": 299.00, "stock_count": 0},
    {"part_number": 7,  "description": "Whiteboard Markers (8pk)",       "selling_price": 6.75,   "stock_count": 85},
    {"part_number": 8,  "description": "Executive Gel Pen Black 12pk",   "selling_price": 18.50,  "stock_count": 450},
    {"part_number": 9,  "description": "Wireless Keyboard Ultra-Compact","selling_price": 89.00,  "stock_count": 8},
    {"part_number": 10, "description": "Monitor Mount Arm Dual Screen",  "selling_price": 145.00, "stock_count": 15},
]
