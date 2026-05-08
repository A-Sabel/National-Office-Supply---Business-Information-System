import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import datetime
import psycopg2

BRAND_NAVY   = "#001440"
BRAND_BLUE   = "#3498db"
ACCENT_GREEN = "#2ecc71"
ACCENT_RED   = "#e74c3c"
ACCENT_AMBER = "#f39c12"
BG_PAGE      = "#f0f2f5"
BG_CARD      = "#ffffff"
TEXT_DARK    = "#2c3e50"
TEXT_MUTED   = "#7f8c8d"
BORDER       = "#e0e0e0"

FONT_TITLE   = ("Segoe UI", 22, "bold")
FONT_SECTION = ("Segoe UI", 14, "bold")
FONT_BODY    = ("Segoe UI", 12)
FONT_SMALL   = ("Segoe UI", 10)
FONT_TABLE   = ("Segoe UI", 11)


class SummaryCard(ctk.CTkFrame):
    def __init__(self, parent, title, value, subtitle, icon, color, **kwargs):
        super().__init__(parent, fg_color=BG_CARD, corner_radius=12,
                         border_width=1, border_color=BORDER, **kwargs)
        ctk.CTkLabel(self, text=icon,  font=("Segoe UI", 24)).pack(anchor="w", padx=16, pady=(14, 0))
        ctk.CTkLabel(self, text=value, font=("Segoe UI", 28, "bold"),
                     text_color=color).pack(anchor="w", padx=16)
        ctk.CTkLabel(self, text=title, font=FONT_BODY,
                     text_color=TEXT_DARK).pack(anchor="w", padx=16)
        ctk.CTkLabel(self, text=subtitle, font=FONT_SMALL,
                     text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 14))


# ---------------------------------------------------------------------------
# Scrollable container (replaces CTkScrollableFrame — works inside any parent)
# ---------------------------------------------------------------------------
class _ScrollableBody(tk.Frame):
    """A plain tk.Frame that lives inside a Canvas so it scrolls vertically."""

    def __init__(self, master_canvas: tk.Canvas):
        super().__init__(master_canvas, bg=BG_PAGE)
        self._canvas = master_canvas

    def update_scrollregion(self, _event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))


class InventorySalesReportView(ctk.CTkFrame):
    def __init__(self, parent, controller=None, db_config=None, **kwargs):
        super().__init__(parent, fg_color=BG_PAGE, corner_radius=0,
                         border_width=0, **kwargs)
        self.controller = controller
        self.db_config  = db_config

        self.parts     = self._load_parts()
        self.suppliers = self._load_suppliers()

        # Fill the outer CTkFrame completely
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Manual scroll canvas ────────────────────────────────────────
        self._canvas = tk.Canvas(self, bg=BG_PAGE, highlightthickness=0)
        self._vsb    = ttk.Scrollbar(self, orient="vertical",
                                     command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vsb.set)

        self._vsb.grid   (row=0, column=1, sticky="ns")
        self._canvas.grid(row=0, column=0, sticky="nsew")

        # Inner frame that holds all the content
        self._body = tk.Frame(self._canvas, bg=BG_PAGE)
        self._body_id = self._canvas.create_window(
            (0, 0), window=self._body, anchor="nw"
        )

        # Keep body width = canvas width
        self._canvas.bind("<Configure>", self._on_canvas_resize)
        self._body.bind("<Configure>",
                        lambda e: self._canvas.configure(
                            scrollregion=self._canvas.bbox("all")))

        # Mouse-wheel scrolling
        self._canvas.bind_all("<MouseWheel>",
                              lambda e: self._canvas.yview_scroll(
                                  int(-1 * (e.delta / 120)), "units"))

        # Build content inside self._body
        self._build_header()
        self._build_summary_strip()
        self._build_filter_bar()
        self._build_tabs()

    def _on_canvas_resize(self, event):
        self._canvas.itemconfig(self._body_id, width=event.width)

    # ------------------------------------------------------------------
    # Data loaders
    # ------------------------------------------------------------------
    def _load_parts(self):
        if not self.db_config:
            return list(self._SAMPLE_PARTS)
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                # Uses the part table directly — same as before
                cur.execute("""
                    SELECT part_no, description, sell_price, count_in_stock,
                        trigger_amount,
                        (SELECT COUNT(*) FROM purchase_order_line pol
                            WHERE pol.part_no = p.part_no
                            AND   pol.status  = 'pending') AS on_order,
                        CASE
                            WHEN count_in_stock = 0               THEN 'Out of Stock'
                            WHEN count_in_stock <= trigger_amount THEN 'Low Stock'
                            ELSE 'In Stock'
                        END AS status
                    FROM part p ORDER BY part_no
                """)
                rows = cur.fetchall()
                conn.close()
                return rows if rows else list(self._SAMPLE_PARTS)
        except Exception as e:
            print(f"[Inventory] _load_parts failed: {e}")
            return list(self._SAMPLE_PARTS)

    def _load_suppliers(self):
        if not self.db_config:
            return dict(self._SAMPLE_SUPPLIERS)
        try:
            conn = psycopg2.connect(**self.db_config)
            result = {}
            with conn.cursor() as cur:
                # Uses qd6_low_stock_suppliers view directly
                cur.execute("""
                    SELECT part_no, supplier_name, unit_cost, phone
                    FROM   qd6_low_stock_suppliers
                """)
                for part_no, name, cost, phone in cur.fetchall():
                    result.setdefault(part_no, []).append((name, float(cost), phone))
            conn.close()
            return result if result else dict(self._SAMPLE_SUPPLIERS)
        except Exception as e:
            print(f"[Inventory] _load_suppliers failed: {e}")
            return dict(self._SAMPLE_SUPPLIERS)

    def _load_reorder(self):
        """Load QD-Sec3/4/5 data for the Low-Stock tab."""
        if not self.db_config:
            return None   # falls back to computing from self.parts
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        p.part_no,
                        p.description,
                        p.count_in_stock,
                        p.trigger_amount,
                        -- QD-Sec4: has pending purchase order?
                        EXISTS (
                            SELECT 1 FROM purchase_order_line pol
                            WHERE pol.part_no = p.part_no
                            AND   pol.status  = 'pending'
                        ) AS on_order,
                        -- QD-Sec5: has unshipped customer invoice?
                        EXISTS (
                            SELECT 1 FROM invoice_line il
                            JOIN  invoice i ON i.invoice_no = il.invoice_no
                            WHERE il.part_no    = p.part_no
                            AND   i.is_shipped  = FALSE
                        ) AS has_unshipped
                    FROM qd3_low_stock p
                    ORDER BY p.part_no
                """)
                rows = cur.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print(f"[Inventory] _load_reorder failed: {e}")
            return None

    # ── Helper: CTk widget inside plain tk.Frame parent ─────────────────
    # (CTk widgets work fine inside tk.Frame — just pass self._body as parent)

    # ── Header ──────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = ctk.CTkFrame(self._body, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(25, 0))

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text="Inventory",
                     font=FONT_TITLE, text_color=TEXT_DARK).pack(anchor="w")
        ctk.CTkLabel(left,
                     text=(f"As of  {datetime.date.today().strftime('%B %d, %Y')}"
                           "  ·  National Office Supplies"),
                     font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w")

        ctk.CTkButton(hdr, text="⬇  Export CSV", width=130, height=34,
                      corner_radius=6, fg_color=BRAND_NAVY,
                      hover_color="#002a7a",
                      font=("Segoe UI", 12, "bold"),
                      command=self._export_csv).pack(side="right", padx=(8, 0))
        ctk.CTkButton(hdr, text="🖨  Print", width=100, height=34,
                      corner_radius=6, fg_color="#ecf0f1",
                      text_color=TEXT_DARK, hover_color=BORDER,
                      font=("Segoe UI", 12)).pack(side="right")

    # ── KPI summary strip ───────────────────────────────────────────────
    def _build_summary_strip(self):
        strip = ctk.CTkFrame(self._body, fg_color="transparent")
        strip.pack(fill="x", padx=30, pady=(18, 0))
        strip.columnconfigure((0, 1, 2, 3), weight=1, pad=12)

        total     = len(self.parts)
        in_stock  = sum(1 for p in self.parts if p[6] == "In Stock")
        low_stock = sum(1 for p in self.parts if p[6] == "Low Stock")
        out       = sum(1 for p in self.parts if p[6] == "Out of Stock")

        SummaryCard(strip, "Total Parts",     str(total),
                    "All SKUs tracked",       "📦", BRAND_BLUE
                    ).grid(row=0, column=0, sticky="nsew", padx=6)
        SummaryCard(strip, "In Stock",        str(in_stock),
                    "Sufficient quantity",    "✅", ACCENT_GREEN
                    ).grid(row=0, column=1, sticky="nsew", padx=6)
        SummaryCard(strip, "Low / Critical",  str(low_stock),
                    "Needs reorder",          "⚠️", ACCENT_AMBER
                    ).grid(row=0, column=2, sticky="nsew", padx=6)
        SummaryCard(strip, "Out of Stock",    str(out),
                    "Requires urgent action", "🚨", ACCENT_RED
                    ).grid(row=0, column=3, sticky="nsew", padx=6)

    # ── Filter bar ──────────────────────────────────────────────────────
    def _build_filter_bar(self):
        bar = ctk.CTkFrame(self._body, fg_color=BG_CARD, corner_radius=10,
                           border_width=1, border_color=BORDER)
        bar.pack(fill="x", padx=30, pady=(18, 0))

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(inner, text="🔍", font=("Segoe UI", 14)).pack(side="left")

        self._search_var = ctk.StringVar()
        ctk.CTkEntry(inner, textvariable=self._search_var,
                     placeholder_text="Search part number or description…",
                     width=260, height=36, corner_radius=6,
                     fg_color="#f5f7fa", text_color=TEXT_DARK,
                     border_color=BORDER
                     ).pack(side="left", padx=(6, 20))
        self._search_var.trace_add("write", lambda *_: self._apply_filter())

        ctk.CTkLabel(inner, text="Status:", font=FONT_BODY,
                     text_color=TEXT_MUTED).pack(side="left")
        self._status_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(inner, variable=self._status_var,
                          values=["All", "In Stock", "Low Stock",
                                  "Out of Stock", "On Order"],
                          width=150, height=36, corner_radius=6,
                          fg_color="#f5f7fa", button_color=BRAND_BLUE,
                          text_color=TEXT_DARK,
                          command=lambda _: self._apply_filter()
                          ).pack(side="left", padx=(8, 20))

        ctk.CTkLabel(inner, text="Trigger Alert Only:", font=FONT_BODY,
                     text_color=TEXT_MUTED).pack(side="left")
        self._trigger_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(inner, text="", variable=self._trigger_var,
                        width=30, fg_color=ACCENT_AMBER, hover_color="#e67e22",
                        command=self._apply_filter).pack(side="left", padx=(4, 20))

        self._count_label = ctk.CTkLabel(inner, text=f"{len(self.parts)} records",
                                         font=FONT_SMALL, text_color=TEXT_MUTED)
        self._count_label.pack(side="right")

    # ── Tab container ───────────────────────────────────────────────────
    def _build_tabs(self):
        self._tab_buttons: dict = {}
        self._tab_frames:  dict = {}

        wrapper = ctk.CTkFrame(self._body, fg_color="transparent")
        wrapper.pack(fill="x", padx=30, pady=(18, 30))
        wrapper.columnconfigure(0, weight=1)

        tab_bar = ctk.CTkFrame(wrapper, fg_color=BG_CARD, corner_radius=10,
                               border_width=1, border_color=BORDER, height=48)
        tab_bar.grid(row=0, column=0, sticky="ew")

        for key, label in [("overview", "📋  Inventory Overview"),
                            ("reorder",  "⚠️  Low-Stock / Reorder"),
                            ("supplier", "🏭  Supplier Sourcing")]:
            btn = ctk.CTkButton(tab_bar, text=label, width=210, height=36,
                                corner_radius=8, fg_color="transparent",
                                text_color=TEXT_MUTED, hover_color="#edf2f7",
                                font=FONT_BODY,
                                command=lambda k=key: self._switch_tab(k))
            btn.pack(side="left", padx=6, pady=6)
            self._tab_buttons[key] = btn

        content = ctk.CTkFrame(wrapper, fg_color="transparent")
        content.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        content.columnconfigure(0, weight=1)

        self._tab_frames["overview"] = self._build_overview_tab(content)
        self._tab_frames["reorder"]  = self._build_reorder_tab(content)
        self._tab_frames["supplier"] = self._build_supplier_tab(content)

        self._switch_tab("overview")

    def _switch_tab(self, key: str):
        for k, btn in self._tab_buttons.items():
            active = k == key
            btn.configure(
                fg_color=BRAND_NAVY if active else "transparent",
                text_color="white"  if active else TEXT_MUTED,
                font=("Segoe UI", 12, "bold") if active else FONT_BODY,
            )
        for k, frame in self._tab_frames.items():
            if k == key:
                frame.grid(row=0, column=0, sticky="ew")
            else:
                frame.grid_remove()

    # ── TAB 1 : Inventory Overview ───────────────────────────────────────
    def _build_overview_tab(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10,
                             border_width=1, border_color=BORDER)
        frame.columnconfigure(0, weight=1)

        cols   = ("Part No.", "Description", "Sell Price",
                  "In Stock", "Trigger", "On Order", "Status")
        widths = (90, 250, 90, 80, 70, 80, 120)

        self._overview_tree = self._make_treeview(frame, cols, widths, row=0)
        self._overview_tree.tag_configure("ok",    foreground="#1e8449")
        self._overview_tree.tag_configure("low",   foreground="#b7950b",
                                          font=("Segoe UI", 11, "bold"))
        self._overview_tree.tag_configure("out",   foreground=ACCENT_RED,
                                          font=("Segoe UI", 11, "bold"))
        self._overview_tree.tag_configure("order", foreground="#1a5276")
        self._populate_overview(self.parts)
        return frame

    def _populate_overview(self, data):
        tree = self._overview_tree
        tree.delete(*tree.get_children())
        tag_map = {"In Stock": "ok", "Low Stock": "low",
                   "Out of Stock": "out", "On Order": "order"}
        for p in data:
            part_no, desc, price, stock, trigger, on_order, status = p
            tree.insert("", "end",
                        values=(part_no, desc, f"₱{price:.2f}",
                                stock, trigger,
                                "Yes" if on_order else "No", status),
                        tags=(tag_map.get(status, "ok"),))
        self._count_label.configure(text=f"{len(data)} records")

    # ── TAB 2 : Low-Stock / Reorder ─────────────────────────────────────
    def _build_reorder_tab(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10,
                             border_width=1, border_color=BORDER)
        frame.columnconfigure(0, weight=1)

        legend = ctk.CTkFrame(frame, fg_color="#fef9e7", corner_radius=8)
        legend.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        ctk.CTkLabel(legend,
                     text=("⚠️  Parts at or below trigger quantity.  "
                           "Bold red = out of stock.  QD-Sec 3 / 4 / 5"),
                     font=FONT_SMALL, text_color="#7d6608"
                     ).pack(anchor="w", padx=10, pady=6)

        cols   = ("Part No.", "Description", "In Stock", "Trigger",
                  "On Order?", "Has Unshipped Orders", "Action Required")
        widths = (90, 220, 80, 70, 90, 150, 160)

        self._reorder_tree = self._make_treeview(frame, cols, widths, row=1)
        self._reorder_tree.tag_configure("urgent", foreground=ACCENT_RED,
                                         font=("Segoe UI", 11, "bold"))
        self._reorder_tree.tag_configure("low",    foreground="#b7950b",
                                         font=("Segoe UI", 11))
        self._populate_reorder()
        return frame

    def _populate_reorder(self):
        tree = self._reorder_tree
        tree.delete(*tree.get_children())

        # Try live DB data first, fall back to computing from self.parts
        db_rows = self._load_reorder()

        if db_rows is not None:
            # Live data from qd3/4/5 views
            for part_no, desc, stock, trigger, on_order, has_unshipped in db_rows:
                if stock == 0 and not on_order:
                    action, tag = "🚨 Urgent – Reorder NOW", "urgent"
                elif stock == 0 and on_order:
                    action, tag = "⏳ Order Pending", "low"
                elif not on_order:
                    action, tag = "📦 Place Reorder", "low"
                else:
                    action, tag = "⏳ Order Pending", "low"
                tree.insert("", "end",
                            values=(part_no, desc, stock, trigger,
                                    "Yes" if on_order    else "No",
                                    "Yes" if has_unshipped else "No",
                                    action),
                            tags=(tag,))
        else:
            # Fallback: compute from self.parts (sample data path)
            for p in [p for p in self.parts if p[3] <= p[4]]:
                part_no, desc, _, stock, trigger, on_order, _ = p
                unshipped = "Yes" if (stock <= 1 and not on_order) else "No"
                if stock == 0:
                    action, tag = "🚨 Urgent – Reorder NOW", "urgent"
                elif not on_order:
                    action, tag = "📦 Place Reorder", "low"
                else:
                    action, tag = "⏳ Order Pending", "low"
                tree.insert("", "end",
                            values=(part_no, desc, stock, trigger,
                                    "Yes" if on_order else "No",
                                    unshipped, action),
                            tags=(tag,))

    # ── TAB 3 : Supplier Sourcing ────────────────────────────────────────
    def _build_supplier_tab(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10,
                             border_width=1, border_color=BORDER)
        frame.columnconfigure(0, weight=1)

        note = ctk.CTkFrame(frame, fg_color="#eaf4fb", corner_radius=8)
        note.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        ctk.CTkLabel(note,
                     text="🏭  Suppliers for low-stock parts — sorted cheapest first.  QD-Sec 6",
                     font=FONT_SMALL, text_color="#1a5276"
                     ).pack(anchor="w", padx=10, pady=6)

        cols   = ("Part No.", "Description", "Supplier Name",
                  "Unit Cost", "Phone", "Best Price?")
        widths = (90, 200, 180, 90, 140, 100)

        self._supplier_tree = self._make_treeview(frame, cols, widths, row=1)
        self._supplier_tree.tag_configure("cheapest", foreground="#1e8449",
                                          font=("Segoe UI", 11, "bold"))
        self._populate_supplier()
        return frame

    def _populate_supplier(self):
        tree = self._supplier_tree
        tree.delete(*tree.get_children())
        for part in [p for p in self.parts if p[3] <= p[4]]:
            part_no, desc = part[0], part[1]
            for i, (name, cost, phone) in enumerate(
                    sorted(self.suppliers.get(part_no, []), key=lambda s: s[1])):
                tree.insert("", "end",
                            values=(part_no if i == 0 else "",
                                    desc    if i == 0 else "",
                                    name, f"₱{cost:.2f}", phone,
                                    "✅ Yes" if i == 0 else "—"),
                            tags=("cheapest",) if i == 0 else ())

    # ── Shared treeview factory ──────────────────────────────────────────
    def _make_treeview(self, parent, cols, widths, row: int) -> ttk.Treeview:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("NOS.Treeview",
                        background=BG_CARD, foreground=TEXT_DARK,
                        rowheight=32, fieldbackground=BG_CARD,
                        font=FONT_TABLE, borderwidth=0)
        style.configure("NOS.Treeview.Heading",
                        background=BRAND_NAVY, foreground="white",
                        font=("Segoe UI", 11, "bold"), relief="flat")
        style.map("NOS.Treeview",
                  background=[("selected", "#d6e4f7")],
                  foreground=[("selected", BRAND_NAVY)])
        style.map("NOS.Treeview.Heading",
                  background=[("active", "#002a7a")])

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=0, sticky="ew", padx=16, pady=(4, 16))
        container.columnconfigure(0, weight=1)

        vsb  = ttk.Scrollbar(container, orient="vertical")
        hsb  = ttk.Scrollbar(container, orient="horizontal")
        tree = ttk.Treeview(container, columns=cols, show="headings",
                            style="NOS.Treeview",
                            yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                            height=12)
        vsb.configure(command=tree.yview)
        hsb.configure(command=tree.xview)

        for col, w in zip(cols, widths):
            tree.heading(col, text=col,
                         command=lambda c=col: self._sort_column(tree, c, False))
            tree.column(col, width=w, minwidth=60, anchor="w")

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid (row=0, column=1, sticky="ns")
        hsb.grid (row=1, column=0, sticky="ew")
        return tree

    # ── Column sorting ───────────────────────────────────────────────────
    def _sort_column(self, tree: ttk.Treeview, col: str, reverse: bool):
        data = [(tree.set(iid, col), iid) for iid in tree.get_children("")]
        try:
            data.sort(key=lambda t: float(t[0].replace("₱", "").replace(",", "")),
                      reverse=reverse)
        except ValueError:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)
        for idx, (_, iid) in enumerate(data):
            tree.move(iid, "", idx)
        tree.heading(col, command=lambda: self._sort_column(tree, col, not reverse))

    # ── Filter logic ─────────────────────────────────────────────────────
    def _apply_filter(self):
        query    = self._search_var.get().lower()
        status   = self._status_var.get()
        only_low = self._trigger_var.get()
        filtered = [
            p for p in self.parts
            if (not query or query in p[0].lower() or query in p[1].lower())
            and (status == "All" or p[6] == status)
            and (not only_low or p[3] <= p[4])
        ]
        self._populate_overview(filtered)

    # ── Export stub ──────────────────────────────────────────────────────
    def _export_csv(self):
        import tkinter.messagebox as mb
        mb.showinfo("Export CSV",
                    "CSV export triggered.\n\n"
                    "Wire to controller.export_inventory_csv() to save the file.")


