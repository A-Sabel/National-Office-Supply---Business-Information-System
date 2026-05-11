import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk

# ── Design tokens (matching Inventory page exactly) ──────────────────────
PAGE_BG = "#f0f2f5"
CARD_BG = "#ffffff"
BORDER = "#e0e0e0"
BRAND_NAVY = "#001440"
BRAND_BLUE = "#3498db"
ACCENT_GREEN = "#2ecc71"
ACCENT_RED = "#e74c3c"
ACCENT_AMBER = "#f39c12"

TEXT_DARK = "#2c3e50"
TEXT_MUTED = "#7f8c8d"
TEXT_WHITE = "#ffffff"

FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_SECTION = ("Segoe UI", 14, "bold")
FONT_BODY = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 10)
FONT_TABLE = ("Segoe UI", 11)


# ══════════════════════════════════════════════════════════════════════════════
#  KPI BAR
# ══════════════════════════════════════════════════════════════════════════════
class InventoryKPIBar(ctk.CTkFrame):
    """Inventory metrics dashboard at top of page."""

    def __init__(self, master, parts_data, **kw):
        super().__init__(master, fg_color=PAGE_BG, **kw)
        self.parts_data = parts_data
        self._build()

    def _build(self):
        # Calculate metrics from parts data
        total_parts = len(self.parts_data)
        total_value = 0
        low_stock_count = 0
        out_of_stock_count = 0

        for (
            sku,
            desc,
            cat,
            stock,
            low_threshold,
            price_str,
            unit,
            actions,
        ) in self.parts_data:
            try:
                # Handle formatted currency strings or raw floats
                if isinstance(price_str, str):
                    price = float(
                        price_str.replace("$", "").replace("₱", "").replace(",", "")
                    )
                else:
                    price = float(price_str)
                total_value += stock * price
            except ValueError:
                pass

            if stock == 0:
                out_of_stock_count += 1
            elif stock <= low_threshold:
                low_stock_count += 1

        cards = [
            ("Total Parts (SKUs)", str(total_parts), BRAND_BLUE, "Catalog items"),
            ("Inventory Value", f"₱{total_value:,.2f}", "#16a34a", "Total stock value"),
            ("Low Stock Items", str(low_stock_count), ACCENT_AMBER, "Below threshold"),
            ("Out of Stock", str(out_of_stock_count), ACCENT_RED, "Critical items"),
        ]

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=0, pady=6)

        for i in range(len(cards)):
            container.grid_columnconfigure(i, weight=1)

        for idx, (title, val, clr, sub) in enumerate(cards):
            card = ctk.CTkFrame(
                container,
                fg_color=CARD_BG,
                corner_radius=12,
                border_width=1,
                border_color=BORDER,
                height=108,
            )
            card.grid(
                row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 5), pady=0
            )
            card.pack_propagate(False)

            ctk.CTkLabel(
                card, text=title, font=("Segoe UI", 11, "bold"), text_color=TEXT_MUTED
            ).pack(anchor="w", padx=14, pady=(12, 0))
            ctk.CTkLabel(
                card, text=val, font=("Segoe UI", 22, "bold"), text_color=TEXT_DARK
            ).pack(anchor="w", padx=14, pady=(2, 0))
            ctk.CTkLabel(card, text=sub, font=("Segoe UI", 10), text_color=clr).pack(
                anchor="w", padx=14, pady=(0, 12)
            )


# ══════════════════════════════════════════════════════════════════════════════
#  INVENTORY VIEW (Main)
# ══════════════════════════════════════════════════════════════════════════════
class InventoryView(ctk.CTkFrame):
    def __init__(self, parent, controller=None, db_config=None, **kwargs):
        super().__init__(
            parent, fg_color=PAGE_BG, corner_radius=0, border_width=0, **kwargs
        )
        self.controller = controller
        self.db_config = db_config

        session = getattr(self.controller, "session", None)
        self.role = getattr(session, "role", None) or "Manager"
        self.db_config = db_config
        self._session_manager = getattr(controller, "session_manager", None)

        # --- RBAC: Fetch role from the secure session ---
        session = getattr(self.controller, "session", None)
        self.role = getattr(session, "role", None) or "Manager"

        self._current_page = 1
        self._page_size = 15
        self._parts_rows = []
        self._filtered_rows = []
        self._parts_tree = None
        self._tbl_container = None
        # Supplier form fields (initialized here so Pylance knows these attrs exist)
        self.supp_name = None
        self.supp_contact = None
        self.supp_phone = None
        self.supp_email = None
        self.supp_address = None
        self._info_bg = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create the tab view FIRST
        self.tabs = ctk.CTkTabview(
            self,
            fg_color=PAGE_BG,
            segmented_button_fg_color=PAGE_BG,
            segmented_button_selected_color=BRAND_BLUE,
            segmented_button_selected_hover_color="#2980b9",
            segmented_button_unselected_color="#ffffff",
            segmented_button_unselected_hover_color="#eef1f5",
            text_color=TEXT_DARK,
        )
        self.tabs.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 20))

        # ── Pill-style tab buttons (matches the Worker Files / Payroll style) ──
        try:
            seg = self.tabs._segmented_button
            seg.configure(
                corner_radius=20,
                border_width=1,
                fg_color=PAGE_BG,
                selected_color=BRAND_BLUE,
                selected_hover_color="#2980b9",
                unselected_color="#ffffff",
                unselected_hover_color="#eef1f5",
                text_color=TEXT_DARK,
                text_color_disabled=TEXT_MUTED,
                font=("Segoe UI", 12),
            )
        except Exception:
            pass

        self.tab_catalog = self.tabs.add("Parts Catalog")
        self.tab_reorder = self.tabs.add("Stock Reordering")
        self.tab_suppliers = self.tabs.add("Suppliers")
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)

        # --- LEFT PANEL: Parts Catalog ---
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.left_panel.columnconfigure(0, weight=1)
        self.left_panel.rowconfigure(1, weight=0)  # Keeps header tight

        # KPI Bar
        self.kpi = InventoryKPIBar(self.left_panel, self._parts_rows)
        self.kpi.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        self._build_catalog_section()

        # --- RIGHT PANEL: Restock Sidebar ---
        self.right_panel = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0, border_width=0
        )
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self._load_parts_data()

        self._build_catalog_tab()
        self._build_reorder_tab()
        self._build_suppliers_tab()

    def _ensure_active_session(self, allowed_roles=None):
        """Enforce session validity before inventory mutations."""
        if self._session_manager is not None:
            self._session_manager.ensure_active(allowed_roles)

    def _load_parts_data(self):
        import psycopg2
        import psycopg2.extras

        try:
            assert self.db_config is not None
            assert self.db_config is not None
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT
                    p.part_number,
                    p.description,
                    p.selling_price,
                    p.stock_count,
                    p.trigger_amount,
                    p.on_order,
                    s.company_name AS best_supplier_name
                FROM parts p
                LEFT JOIN LATERAL (
                    SELECT ip.supplier_id
                    FROM item_parts ip
                    WHERE ip.part_number = p.part_number
                    ORDER BY ip.cost ASC
                    LIMIT 1
                ) bs ON TRUE
                LEFT JOIN suppliers s ON s.supplier_id = bs.supplier_id
                ORDER BY p.part_number
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            self._parts_rows = []
            for r in rows:
                self._parts_rows.append(
                    (
                        str(r["part_number"]),
                        r["description"],
                        "General",  # no category in schema
                        r["stock_count"],
                        r["trigger_amount"],
                        f"₱{float(r['selling_price']):,.2f}",
                        r["best_supplier_name"] or "—",
                        "✏️ Edit",
                    )
                )

        except Exception as e:
            print(f"[DB ERROR] _load_parts_data: {e}")
            self._parts_rows = []

    def _fetch_suppliers(self):
        """Returns list of supplier names from DB for dropdowns."""
        import psycopg2

        try:
            assert self.db_config is not None
            assert self.db_config is not None
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute("SELECT company_name FROM suppliers ORDER BY company_name")
            names = [row[0] for row in cur.fetchall()]
            cur.close()
            conn.close()
            return names if names else ["No suppliers found"]
        except Exception as e:
            print(f"[DB ERROR] _fetch_suppliers: {e}")
            return ["DB unavailable"]

    # ════════════════════════════════════════════════════════════════════
    # LEFT PANEL: Catalog header + search + table
    # ════════════════════════════════════════════════════════════════════
    def _build_catalog_tab(self):
        # Two columns: left = catalog table, right = action panels
        self.tab_catalog.columnconfigure(0, weight=3)  # table expands
        self.tab_catalog.columnconfigure(1, weight=0)  # right panel fixed
        self.tab_catalog.rowconfigure(0, weight=1)  # single row fills height

        # ── LEFT COLUMN wrapper ──────────────────────────────────────────
        self._catalog_left = ctk.CTkFrame(self.tab_catalog, fg_color="transparent")
        left = self._catalog_left
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(2, weight=1)  # row 2 = table, expands

        # Row 0: KPI Bar
        self.kpi = InventoryKPIBar(left, self._parts_rows)
        self.kpi.grid(row=0, column=0, sticky="ew", pady=(0, 8))

    def _build_catalog_section(self):
        hdr = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        hdr.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        hdr.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr,
            text=f"Parts Catalog ({len(self._parts_rows)} items)",
            font=FONT_TITLE,
            text_color=TEXT_DARK,
        ).grid(row=0, column=0, sticky="w")

        actions = ctk.CTkFrame(hdr, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e")

        # --- RBAC: Add New Part Masking ---
        self.add_btn = ctk.CTkButton(
            actions,
            text="+ Add New Part",
            width=130,
            height=34,
            corner_radius=6,
            fg_color=BRAND_BLUE,
            hover_color="#2980b9",
            font=("Segoe UI", 12, "bold"),
            command=self.handle_add_new_part,
        )
        self.add_btn.pack(side="left", padx=(0, 8))

        if self.role != "Manager":
            self.add_btn.configure(
                state="disabled", fg_color="#bdc3c7", text_color="#7f8c8d"
            )

        self.toggle_btn = ctk.CTkButton(
            actions,
            text="◀",
            width=34,
            height=34,
            corner_radius=8,
            fg_color="#2b9430",
            hover_color="#1c7421",
            text_color="#ffffff",
            font=("Segoe UI", 14, "bold"),
            command=self.toggle_side_panels,
        )
        self.toggle_btn.pack(side="left")

        # Row 1: Search & Pagination bar
        search_bar = ctk.CTkFrame(
            self.left_panel,
            fg_color=CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        search_bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        # Search + filter bar
        search_bar = ctk.CTkFrame(
            self.left_panel,
            fg_color=CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        search_bar.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        inner = ctk.CTkFrame(search_bar, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        left_tools = ctk.CTkFrame(inner, fg_color="transparent")
        left_tools.pack(side="left", fill="x", expand=True)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_search_filter())
        ctk.CTkEntry(
            left_tools,
            textvariable=self._search_var,
            placeholder_text="Search parts…",
            width=250,
            height=34,
        ).pack(side="left", padx=(0, 12))
        ctk.CTkEntry(
            left_tools,
            textvariable=self._search_var,
            placeholder_text="Search…",
            width=240,
            height=34,
            corner_radius=6,
            fg_color="#f5f7fa",
            text_color=TEXT_DARK,
            border_color=BORDER,
            font=FONT_BODY,
        ).pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            left_tools, text="Filter:", font=FONT_BODY, text_color=TEXT_MUTED
        ).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            left_tools, text="Filter:", font=FONT_BODY, text_color=TEXT_MUTED
        ).pack(side="left", padx=(0, 8))
        self._filter_var = tk.StringVar(value="All")
        self._filter_var.trace_add("write", lambda *_: self._apply_search_filter())
        ctk.CTkOptionMenu(
            left_tools,
            variable=self._filter_var,
            values=["All", "In Stock", "Low Stock", "Out of Stock"],
            width=140,
            height=34,
            fg_color="#f5f7fa",
            button_color=BRAND_BLUE,
            text_color=TEXT_DARK,
            font=FONT_BODY,
        ).pack(side="left")
        ctk.CTkOptionMenu(
            left_tools,
            variable=self._filter_var,
            values=["All", "In Stock", "Low Stock", "Out of Stock"],
            width=130,
            height=34,
            corner_radius=6,
            fg_color="#f5f7fa",
            button_color=BRAND_BLUE,
            text_color=TEXT_DARK,
            font=FONT_BODY,
        ).pack(side="left")

        right_tools = ctk.CTkFrame(inner, fg_color="transparent")
        right_tools.pack(side="right")

        self.refresh_btn = ctk.CTkButton(
            right_tools,
            text="↻",
            width=34,
            height=34,
            corner_radius=6,
            fg_color=BRAND_BLUE,
            hover_color="#2980b9",
            command=self.refresh_catalog_data,
        )
        self.refresh_btn.pack(side="left", padx=(0, 8))

        self.prev_btn = ctk.CTkButton(
            right_tools,
            text="‹",
            width=30,
            height=28,
            corner_radius=6,
            fg_color="#f3f5f8",
            hover_color="#e8ecf2",
            text_color="#9ca3af",
            font=("Segoe UI", 13, "bold"),
            command=self._go_prev_page,
        )
        self.prev_btn.pack(side="left", padx=2)
        self.prev_page_btn = ctk.CTkButton(
            right_tools,
            text="‹",
            width=30,
            height=28,
            corner_radius=6,
            fg_color="#f3f5f8",
            hover_color="#e8ecf2",
            text_color="#9ca3af",
            font=("Segoe UI", 13, "bold"),
            command=self._go_prev_page,
        )
        self.prev_page_btn.pack(side="left", padx=(0, 6))

        self.page_label = ctk.CTkLabel(
            right_tools,
            text="1",
            width=42,
            height=28,
            fg_color="#ffffff",
            text_color=TEXT_DARK,
            font=("Segoe UI", 12, "bold"),
        )
        self.page_label.pack(side="left", padx=(0, 2))
        self.page_label = ctk.CTkLabel(
            right_tools,
            text="1",
            width=42,
            height=28,
            corner_radius=6,
            fg_color="#ffffff",
            text_color=TEXT_DARK,
            font=("Segoe UI", 12, "bold"),
        )
        self.page_label.pack(side="left", padx=(0, 6))

        self.page_count_label = ctk.CTkLabel(
            right_tools, text="of 1", text_color="#374151", font=("Segoe UI", 11)
        )
        self.page_count_label.pack(side="left", padx=(0, 4))
        self.page_count_label = ctk.CTkLabel(
            right_tools, text="of 1", text_color="#374151", font=("Segoe UI", 11)
        )
        self.page_count_label.pack(side="left", padx=(0, 6))

        self.next_btn = ctk.CTkButton(
            right_tools,
            text="›",
            width=30,
            height=28,
            corner_radius=6,
            fg_color="#f3f5f8",
            hover_color="#e8ecf2",
            text_color="#9ca3af",
            font=("Segoe UI", 13, "bold"),
            command=self._go_next_page,
        )
        self.next_btn.pack(side="left", padx=2)
        self.next_page_btn = ctk.CTkButton(
            right_tools,
            text="›",
            width=30,
            height=28,
            corner_radius=6,
            fg_color="#f3f5f8",
            hover_color="#e8ecf2",
            text_color="#9ca3af",
            font=("Segoe UI", 13, "bold"),
            command=self._go_next_page,
        )
        self.next_page_btn.pack(side="left")

        # Row 2: Parts table
        tbl_frame = ctk.CTkFrame(
            self.left_panel,
            fg_color=CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        tbl_frame.grid(row=2, column=0, sticky="nsew")
        # Table container
        tbl_frame = ctk.CTkFrame(
            self.left_panel,
            fg_color=CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        tbl_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 0))
        self.left_panel.rowconfigure(3, weight=1)

        self._build_parts_table(tbl_frame)

        # ── RIGHT COLUMN: scrollable action panels ───────────────────────
        self.right_panel = ctk.CTkScrollableFrame(
            self.tab_catalog,
            width=240,
            fg_color=PAGE_BG,
            scrollbar_button_color=BORDER,
        )
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        self._build_place_order_card()
        self._build_bottleneck_card()
        self._build_admin_actions_card()

    def refresh_catalog_data(self):
        self._load_parts_data()
        self._filtered_rows = list(self._parts_rows)

        self.kpi.destroy()
        self.kpi = InventoryKPIBar(self._catalog_left, self._parts_rows)
        self.kpi.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self._apply_search_filter()

    def _build_parts_table(self, parent):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Parts.Treeview",
            background=CARD_BG,
            foreground=TEXT_DARK,
            rowheight=36,
            fieldbackground=CARD_BG,
            font=FONT_TABLE,
            borderwidth=0,
        )
        style.configure(
            "Parts.Treeview.Heading",
            background=BRAND_NAVY,
            foreground=TEXT_WHITE,
            font=("Segoe UI", 11, "bold"),
            relief="flat",
        )
        style.map(
            "Parts.Treeview",
            background=[("selected", "#d6e4f7")],
            foreground=[("selected", BRAND_NAVY)],
        )

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        vsb = ttk.Scrollbar(container, orient="vertical")
        hsb = ttk.Scrollbar(container, orient="horizontal")

        cols = (
            "SKU",
            "Part Description",
            "Category",
            "Stock Count",
            "Low Stock Threshold",
            "Selling Price",
            "Unit",
            "Actions",
        )
        widths = (80, 220, 100, 80, 130, 120, 60, 80)

        tree = ttk.Treeview(
            container,
            columns=cols,
            show="headings",
            style="Parts.Treeview",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
        )
        vsb.configure(command=tree.yview)
        hsb.configure(command=tree.xview)

        for col, width in zip(cols, widths):
            tree.column(col, width=width, anchor="w")
            tree.heading(col, text=col)
            anchor = "center" if col == "Actions" else "w"
            tree.column(col, width=width, anchor=anchor)
            tree.heading(col, text=col)

        self._parts_tree = tree
        self._tbl_container = container
        container.bind("<Configure>", self._on_table_resize)
        self._current_page = 1

        tree.bind("<ButtonRelease-1>", self._on_parts_table_click)
        tree.bind("<Double-1>", self._on_parts_table_click)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._refresh_parts_table_page()

    def _on_table_resize(self, event=None):
        """Recalculate page size based on available table height and re-render."""
        if self._parts_tree is None:
            return

        row_height = 36  # Must match rowheight in Parts.Treeview style
        header_height = 28  # Approximate heading row height
        if event:
            available_height = event.height
        else:
            assert self._tbl_container is not None
            available_height = self._tbl_container.winfo_height()
        usable = available_height - header_height

        new_page_size = max(1, usable // row_height)

        if new_page_size != self._page_size:
            self._page_size = new_page_size
            self._current_page = 1
            self._refresh_parts_table_page()

    # ════════════════════════════════════════════════════════════════════
    # RIGHT PANEL: Place Restock Order + Receive Restock
    # ════════════════════════════════════════════════════════════════════
    def _build_place_order_card(self):
        card = self._create_card_container(self.right_panel)
        card.pack(fill="x", pady=(0, 8))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=10, pady=(8, 0))
        ctk.CTkLabel(
            hdr, text="Place Restock Order", font=FONT_SECTION, text_color=TEXT_DARK
        ).pack(anchor="w")

        badge = ctk.CTkLabel(
            card,
            text="✓ Auto-Suggested: Lowest Cost Supplier",
            fg_color="#e8f5e9",
            text_color="#2e7d32",
            font=("Segoe UI", 9, "bold"),
            corner_radius=4,
        )
        badge.pack(fill="x", padx=10, pady=(6, 6))

        frame = ctk.CTkFrame(card, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=(0, 5))
        ctk.CTkLabel(
            frame, text="Part Name/SKU", font=FONT_SMALL, text_color=TEXT_MUTED
        ).pack(anchor="w", pady=(0, 3))
        self.po_part_combo = ctk.CTkComboBox(
            frame,
            values=[r[1] for r in self._parts_rows],
            height=28,
            fg_color="#f5f7fa",
            border_color=BORDER,
        )
        self.po_part_combo.pack(fill="x")

        qty_supplier = ctk.CTkFrame(card, fg_color="transparent")
        qty_supplier.pack(fill="x", padx=10, pady=(2, 3))
        qty_supplier.columnconfigure(0, weight=1)
        qty_supplier.columnconfigure(1, weight=1)

        qty_frame = ctk.CTkFrame(qty_supplier, fg_color="transparent")
        qty_frame.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(
            qty_frame, text="Quantity", font=FONT_SMALL, text_color=TEXT_MUTED
        ).pack(anchor="w")
        self.po_qty_entry = ctk.CTkEntry(
            qty_frame, height=28, fg_color="#f5f7fa", placeholder_text="500"
        )
        self.po_qty_entry.pack(fill="x", pady=(2, 0))

        supp_frame = ctk.CTkFrame(qty_supplier, fg_color="transparent")
        supp_frame.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(
            supp_frame, text="Supplier", font=FONT_SMALL, text_color=TEXT_MUTED
        ).pack(anchor="w")
        supplier_names = self._fetch_suppliers()
        self.supplier_combo = ctk.CTkComboBox(
            supp_frame, values=supplier_names, height=28, fg_color="#f5f7fa"
        )
        self.supplier_combo.pack(fill="x", pady=(2, 0))

        price_info = ctk.CTkFrame(card, fg_color="#f5f7fa", corner_radius=6)
        price_info.pack(fill="x", padx=10, pady=(6, 6))
        price_info.grid_columnconfigure(0, weight=1)
        price_info.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            price_info,
            text="Est. Cost",
            font=("Segoe UI", 9, "bold"),
            text_color=TEXT_DARK,
        ).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(
            price_info,
            text="₱2,745.00",
            font=("Segoe UI", 9, "bold"),
            text_color=TEXT_DARK,
        ).grid(row=0, column=1, sticky="e", padx=10, pady=5)

        # --- RBAC: Submit PO Masking ---
        self.submit_po_btn = ctk.CTkButton(
            card,
            text="✈ Submit PO",
            height=32,
            corner_radius=6,
            fg_color=BRAND_BLUE,
            hover_color="#2980b9",
            font=("Segoe UI", 11, "bold"),
            command=self.handle_submit_po,  # <-- ADD THIS LINE
        )
        self.submit_po_btn.pack(fill="x", padx=10, pady=(0, 8))

        if self.role != "Manager":
            self.submit_po_btn.configure(
                state="disabled", fg_color="#bdc3c7", text_color="#7f8c8d"
            )

    def _build_suppliers_tab(self):
        self.tab_suppliers.columnconfigure(1, weight=1)
        self.tab_suppliers.rowconfigure(0, weight=1)

        self.tab_suppliers.columnconfigure(0, weight=0)  # form: fixed width
        self.tab_suppliers.columnconfigure(1, weight=1)  # list: expands
        self.tab_suppliers.rowconfigure(0, weight=1)

        # Left: form
        form = ctk.CTkFrame(
            self.tab_suppliers,
            width=320,
            fg_color=CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        form.grid(row=0, column=0, sticky="nsew", padx=(5, 10), pady=5)
        form.pack_propagate(False)

        ctk.CTkLabel(
            form, text="Supplier Details", font=FONT_SECTION, text_color=TEXT_DARK
        ).pack(anchor="w", padx=16, pady=(14, 6))

        self._editing_supplier_id = None

        def make_field(label, attr_name, placeholder):
            ctk.CTkLabel(form, text=label, font=FONT_SMALL, text_color=TEXT_MUTED).pack(
                anchor="w", padx=16, pady=(8, 2)
            )
            entry = ctk.CTkEntry(
                form, placeholder_text=placeholder, width=270, height=34
            )
            entry.pack(padx=16)
            setattr(self, attr_name, entry)

        make_field("Company Name *", "supp_name", "e.g. Apex Auto Parts")
        make_field("Contact Person", "supp_contact", "e.g. Juan dela Cruz")
        make_field("Phone", "supp_phone", "e.g. +63 912 345 6789")
        make_field("Email", "supp_email", "e.g. orders@apex.ph")
        make_field("Address", "supp_address", "Street, City")

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(
            form, text="Receive Restock", font=FONT_SECTION, text_color=TEXT_DARK
        ).pack(anchor="w", padx=10, pady=(8, 4))

        search_row = ctk.CTkFrame(form, fg_color="#f5f7fa", corner_radius=6)
        search_row.pack(fill="x", padx=10, pady=(0, 6))
        search_row.grid_columnconfigure(0, weight=1)
        self.recv_po_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="PO Number",
            height=28,
            fg_color="#f5f7fa",
            border_color=BORDER,
        )
        self.recv_po_entry.grid(row=0, column=0, sticky="ew", padx=(0, 2), pady=4)

        self._info_bg = ctk.CTkFrame(form, fg_color="#f8f9fa", corner_radius=6)
        self._info_bg.pack(fill="x", padx=10, pady=(0, 6))

        self.save_supp_btn = ctk.CTkButton(
            btn_row,
            text="💾  Save Supplier",
            fg_color=BRAND_BLUE,
            hover_color="#2980b9",
            font=("Segoe UI", 11, "bold"),
            height=34,
            command=self._save_supplier,
        )
        self.save_supp_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="✕  Clear",
            fg_color="#f3f5f8",
            hover_color="#e0e4eb",
            text_color=TEXT_DARK,
            font=("Segoe UI", 11),
            height=34,
            command=self._clear_supplier_form,
        ).pack(side="left")

        self._supp_status_label = ctk.CTkLabel(
            form, text="", font=FONT_SMALL, text_color=ACCENT_GREEN
        )
        self._supp_status_label.pack(anchor="w", padx=16, pady=(4, 0))

        # Right: supplier list
        right = ctk.CTkFrame(
            self.tab_suppliers,
            fg_color=CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 5), pady=5)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        supp_hdr = ctk.CTkFrame(right, fg_color="transparent")
        supp_hdr.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        ctk.CTkLabel(
            supp_hdr, text="Supplier List", font=FONT_SECTION, text_color=TEXT_DARK
        ).pack(side="left")
        ctk.CTkButton(
            supp_hdr,
            text="↻",
            width=32,
            height=32,
            corner_radius=6,
            fg_color="#f3f5f8",
            hover_color="#e0e4eb",
            text_color=TEXT_DARK,
            command=self._load_supplier_list,
        ).pack(side="right")

        style = ttk.Style()
        style.configure(
            "Supp.Treeview",
            background=CARD_BG,
            foreground=TEXT_DARK,
            rowheight=34,
            fieldbackground=CARD_BG,
            font=FONT_TABLE,
            borderwidth=0,
        )
        style.configure(
            "Supp.Treeview.Heading",
            background=BRAND_NAVY,
            foreground=TEXT_WHITE,
            font=("Segoe UI", 11, "bold"),
            relief="flat",
        )
        style.map(
            "Supp.Treeview",
            background=[("selected", "#d6e4f7")],
            foreground=[("selected", BRAND_NAVY)],
        )

        supp_cols = ("ID", "Company Name", "Contact", "Phone", "Email", "Address")
        supp_widths = (50, 180, 140, 130, 190, 200)

        supp_vsb = ttk.Scrollbar(right, orient="vertical")
        supp_hsb = ttk.Scrollbar(right, orient="horizontal")

        self.supp_tree = ttk.Treeview(
            right,
            columns=supp_cols,
            show="headings",
            style="Supp.Treeview",
            yscrollcommand=supp_vsb.set,
            xscrollcommand=supp_hsb.set,
        )
        supp_vsb.configure(command=self.supp_tree.yview)
        supp_hsb.configure(command=self.supp_tree.xview)

        for col, width in zip(supp_cols, supp_widths):
            self.supp_tree.column(col, width=width, anchor="w")
            self.supp_tree.heading(col, text=col)

        self.supp_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 4))
        supp_vsb.grid(row=1, column=1, sticky="ns")
        supp_hsb.grid(row=2, column=0, sticky="ew")

        self.supp_tree.bind("<Double-1>", self._on_supplier_double_click)

        ctk.CTkButton(
            right,
            text="🗑  Delete Selected Supplier",
            fg_color=ACCENT_RED,
            hover_color="#c0392b",
            font=("Segoe UI", 11, "bold"),
            height=32,
            command=self._delete_supplier,
        ).grid(row=3, column=0, columnspan=2, pady=(4, 10), padx=10, sticky="ew")

        self._load_supplier_list()

    def _save_supplier(self):
        import psycopg2

        assert self.supp_name is not None
        assert self.supp_contact is not None
        assert self.supp_phone is not None
        assert self.supp_email is not None
        assert self.supp_address is not None

        name = self.supp_name.get().strip()
        contact = self.supp_contact.get().strip()
        phone = self.supp_phone.get().strip()
        email = self.supp_email.get().strip()
        address = self.supp_address.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Company Name is required.")
            return
        try:
            assert self.db_config is not None
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            if self._editing_supplier_id:
                cur.execute(
                    """
                    UPDATE suppliers SET company_name=%s, contact_person=%s,
                    phone=%s, email=%s, address=%s WHERE supplier_id=%s
                """,
                    (name, contact, phone, email, address, self._editing_supplier_id),
                )
                msg = f"Supplier '{name}' updated."
            else:
                cur.execute(
                    """
                    INSERT INTO suppliers (company_name, contact_person, phone, email, address)
                    VALUES (%s, %s, %s, %s, %s)
                """,
                    (name, contact, phone, email, address),
                )
                msg = f"Supplier '{name}' added."
            conn.commit()
            cur.close()
            conn.close()
            self._supp_status_label.configure(text=f"✓ {msg}", text_color=ACCENT_GREEN)
            self._clear_supplier_form()
            self._load_supplier_list()
            self.reorder_supp.configure(values=self._fetch_suppliers())
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to save supplier:\n{e}")

    def _clear_supplier_form(self):
        self._editing_supplier_id = None
        self.save_supp_btn.configure(text="💾  Save Supplier")
        for attr in (
            "supp_name",
            "supp_contact",
            "supp_phone",
            "supp_email",
            "supp_address",
        ):
            entry = getattr(self, attr, None)
            if entry:
                entry.delete(0, "end")

    def _on_supplier_double_click(self, event):
        selected = self.supp_tree.selection()
        if not selected:
            return
        vals = self.supp_tree.item(selected[0])["values"]
        self._editing_supplier_id = vals[0]
        for attr, val in zip(
            ("supp_name", "supp_contact", "supp_phone", "supp_email", "supp_address"),
            vals[1:],
        ):
            entry = getattr(self, attr)
            entry.delete(0, "end")
            entry.insert(0, val or "")
        self.save_supp_btn.configure(text="✏️  Update Supplier")
        self._supp_status_label.configure(
            text=f"Editing: {vals[1]}", text_color=ACCENT_AMBER
        )

    def _delete_supplier(self):
        import psycopg2

        selected = self.supp_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select a supplier to delete.")
            return
        vals = self.supp_tree.item(selected[0])["values"]
        supplier_id, name = vals[0], vals[1]
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete supplier '{name}'?\nThis may affect linked purchase orders.",
        ):
            return
        try:
            assert self.db_config is not None
            assert self.db_config is not None
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute("DELETE FROM suppliers WHERE supplier_id = %s", (supplier_id,))
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo("Deleted", f"Supplier '{name}' removed.")
            self._clear_supplier_form()
            self._load_supplier_list()
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to delete supplier:\n{e}")

    def _load_supplier_list(self):
        import psycopg2, psycopg2.extras

        self.supp_tree.delete(*self.supp_tree.get_children())
        try:
            assert self.db_config is not None
            assert self.db_config is not None
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT supplier_id, company_name, contact_person, phone, email, address
                FROM suppliers ORDER BY company_name
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to load suppliers:\n{e}")
            return
        for r in rows:
            self.supp_tree.insert(
                "",
                "end",
                values=(
                    r["supplier_id"],
                    r["company_name"] or "",
                    r["contact_person"] or "",
                    r["phone"] or "",
                    r["email"] or "",
                    r["address"] or "",
                ),
            )
        ctk.CTkLabel(
            self._info_bg,
            text="PO-2023-112",
            font=("Segoe UI", 11, "bold"),
            text_color=TEXT_DARK,
        ).pack(anchor="w", padx=8, pady=(4, 0))
        ctk.CTkLabel(
            self._info_bg, text="Supplier", font=FONT_SMALL, text_color=TEXT_MUTED
        ).pack(anchor="w", padx=8, pady=(3, 0))
        ctk.CTkLabel(
            self._info_bg, text="Apex", font=("Segoe UI", 11), text_color=TEXT_DARK
        ).pack(anchor="w", padx=8, pady=(0, 2))

        summary_grid = ctk.CTkFrame(self._info_bg, fg_color="transparent")
        summary_grid.pack(fill="x", padx=8, pady=(3, 4))
        summary_grid.grid_columnconfigure((0, 1, 2), weight=1)

        for col, (label, value) in enumerate(
            [("Items", "4"), ("Qty", "500"), ("Total", "₱2,745.00")]
        ):
            ctk.CTkLabel(
                summary_grid, text=label, font=FONT_SMALL, text_color=TEXT_MUTED
            ).grid(row=0, column=col, sticky="w")
            ctk.CTkLabel(
                summary_grid, text=value, font=("Segoe UI", 10), text_color=TEXT_DARK
            ).grid(row=1, column=col, sticky="w", pady=(1, 0))

        # --- RBAC: Mark Received Masking ---
        self.mark_rcvd_btn = ctk.CTkButton(
            self.tab_suppliers,
            text="⊞  Mark Received",
            height=32,
            corner_radius=6,
            fg_color="#ff3d1f",
            hover_color="#e33317",
            text_color="#ffffff",
            font=("Segoe UI", 11, "bold"),
            command=self.handle_mark_received,
        )
        self.mark_rcvd_btn.pack(fill="x", padx=10, pady=(0, 8))

        if self.role != "Manager":
            self.mark_rcvd_btn.configure(
                state="disabled", fg_color="#bdc3c7", text_color="#7f8c8d"
            )

    def _build_bottleneck_card(self):
        card = self._create_card_container(self.right_panel)
        card.pack(fill="x", pady=(0, 8))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(
            hdr, text="⚠ Order Bottlenecks", font=FONT_SECTION, text_color=ACCENT_RED
        ).pack(side="left")
        ctk.CTkButton(
            hdr,
            text="↻",
            width=28,
            height=28,
            corner_radius=6,
            fg_color="#f5f7fa",
            hover_color="#e8ecf2",
            text_color=TEXT_DARK,
            command=self._refresh_bottlenecks,
        ).pack(side="right")

        self._bottleneck_frame = ctk.CTkFrame(card, fg_color="transparent")
        self._bottleneck_frame.pack(fill="x", padx=10, pady=(0, 8))
        self._refresh_bottlenecks()

    def _refresh_bottlenecks(self):
        import psycopg2
        import psycopg2.extras

        for w in self._bottleneck_frame.winfo_children():
            w.destroy()

        try:
            assert self.db_config is not None
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT
                    p.part_number,
                    p.description,
                    p.stock_count,
                    COUNT(DISTINCT i.invoice_id) AS blocked_order_count
                FROM parts p
                JOIN invoice_lines il ON il.part_number = p.part_number
                JOIN invoices i ON i.invoice_id = il.invoice_id
                WHERE i.status = 'pending'
                AND p.stock_count <= 1
                AND p.on_order = FALSE
                GROUP BY p.part_number, p.description, p.stock_count
                ORDER BY p.stock_count ASC
            """)
            bottlenecks = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            ctk.CTkLabel(
                self._bottleneck_frame,
                text=f"DB Error: {e}",
                text_color=ACCENT_RED,
                font=FONT_SMALL,
            ).pack()
            return

        if not bottlenecks:
            ctk.CTkLabel(
                self._bottleneck_frame,
                text="✓ No bottlenecks detected",
                font=FONT_SMALL,
                text_color=ACCENT_GREEN,
            ).pack(anchor="w")
            return

        for b in bottlenecks:
            row = ctk.CTkFrame(
                self._bottleneck_frame, fg_color="#fff5f5", corner_radius=6
            )
            row.pack(fill="x", pady=(0, 4))
            ctk.CTkLabel(
                row,
                text=f"Part {b['part_number']} — {b['description'][:28]}",
                font=("Segoe UI", 10, "bold"),
                text_color=ACCENT_RED,
            ).pack(anchor="w", padx=8, pady=(4, 0))
            ctk.CTkLabel(
                row,
                text=f"Stock: {b['stock_count']}  |  Blocking {b['blocked_order_count']} order(s)",
                font=FONT_SMALL,
                text_color=TEXT_MUTED,
            ).pack(anchor="w", padx=8, pady=(0, 4))

    def _build_admin_actions_card(self):
        card = self._create_card_container(self.right_panel)
        card.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            card, text="Admin Actions", font=FONT_SECTION, text_color=TEXT_DARK
        ).pack(anchor="w", padx=10, pady=(8, 6))

        self.restock_btn = ctk.CTkButton(
            card,
            text="⟳ Apply Dynamic Restock",
            height=32,
            corner_radius=6,
            fg_color=ACCENT_AMBER,
            hover_color="#d68910",
            text_color="#ffffff",
            font=("Segoe UI", 11, "bold"),
            command=self.handle_apply_dynamic_restock,
        )
        self.restock_btn.pack(fill="x", padx=10, pady=(0, 6))

        self.inflate_btn = ctk.CTkButton(
            card,
            text="↑ Apply Price Inflation",
            height=32,
            corner_radius=6,
            fg_color=ACCENT_RED,
            hover_color="#c0392b",
            text_color="#ffffff",
            font=("Segoe UI", 11, "bold"),
            command=self.handle_apply_price_inflation,
        )
        self.inflate_btn.pack(fill="x", padx=10, pady=(0, 8))

        if self.role != "Manager":
            for btn in (self.restock_btn, self.inflate_btn):
                btn.configure(
                    state="disabled", fg_color="#bdc3c7", text_color="#7f8c8d"
                )

    def handle_apply_dynamic_restock(self):
        import psycopg2

        try:
            assert self.db_config is not None
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()

            # Find top 2 parts by total quantity sold YTD
            cur.execute("""
                SELECT il.part_number, SUM(il.quantity_ordered) AS ytd_qty
                FROM invoice_lines il
                JOIN invoices i ON i.invoice_id = il.invoice_id
                WHERE EXTRACT(YEAR FROM i.invoice_date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND i.status != 'void'
                GROUP BY il.part_number
                ORDER BY ytd_qty DESC
                LIMIT 2
            """)
            top_parts = [row[0] for row in cur.fetchall()]

            if not top_parts:
                messagebox.showinfo(
                    "Dynamic Restock", "No YTD sales data found. Nothing updated."
                )
                conn.close()
                return

            cur.execute(
                """
                UPDATE parts
                SET restock_value = restock_value * 2
                WHERE part_number = ANY(%s)
            """,
                (top_parts,),
            )

            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo(
                "Dynamic Restock",
                f"Restock value doubled for {len(top_parts)} part(s):\n"
                + "\n".join(str(p) for p in top_parts),
            )
            self._load_parts_data()
            self._refresh_parts_table_page()

        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to apply dynamic restock:\n{e}")

    def handle_apply_price_inflation(self):
        import psycopg2

        confirm = messagebox.askyesno(
            "Confirm Price Inflation",
            "Increase prices for all parts with no YTD sales?\n\n"
            "• restock_value < 4  →  +10%\n"
            "• restock_value ≥ 4  →  +20%\n\nContinue?",
        )
        if not confirm:
            return

        self._ensure_active_session(["Manager"])

        try:
            assert self.db_config is not None
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()

            # Fetch parts with zero YTD sales
            cur.execute("""
                SELECT p.part_number, p.restock_value
                FROM parts p
                WHERE p.part_number NOT IN (
                    SELECT DISTINCT il.part_number
                    FROM invoice_lines il
                    JOIN invoices i ON i.invoice_id = il.invoice_id
                    WHERE EXTRACT(YEAR FROM i.invoice_date) = EXTRACT(YEAR FROM CURRENT_DATE)
                    AND i.status != 'void'
                )
            """)
            zero_parts = cur.fetchall()

            if not zero_parts:
                messagebox.showinfo(
                    "Price Inflation", "All parts have YTD sales. Nothing updated."
                )
                conn.close()
                return

            updated = 0
            for part_number, restock_value in zero_parts:
                multiplier = 1.10 if float(restock_value) < 4 else 1.20
                cur.execute(
                    "UPDATE parts SET selling_price = selling_price * %s WHERE part_number = %s",
                    (multiplier, part_number),
                )
                updated += 1

            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo(
                "Price Inflation", f"Updated prices for {updated} part(s)."
            )
            self._load_parts_data()
            self._refresh_parts_table_page()

        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to apply price inflation:\n{e}")

    def _open_edit_part_dialog(self, sku, values):
        """Modal dialog to edit a part's description, price, stock, and trigger amount."""
        # values = (sku, desc, cat, stock, threshold, price, supplier, action)
        _, desc, _, stock, threshold, price_str, supplier, _ = values

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit Part — SKU {sku}")
        dialog.geometry("420x380")
        dialog.resizable(False, False)
        dialog.grab_set()  # modal
        dialog.focus()

        ctk.CTkLabel(
            dialog,
            text=f"Editing Part: {sku}",
            font=("Segoe UI", 14, "bold"),
            text_color=TEXT_DARK,
        ).pack(anchor="w", padx=20, pady=(16, 4))

        ctk.CTkLabel(
            dialog, text="Description", font=FONT_SMALL, text_color=TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(8, 2))
        desc_entry = ctk.CTkEntry(dialog, width=380, height=34)
        desc_entry.insert(0, desc)
        desc_entry.pack(padx=20)

        ctk.CTkLabel(
            dialog, text="Selling Price (₱)", font=FONT_SMALL, text_color=TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(8, 2))
        price_entry = ctk.CTkEntry(dialog, width=380, height=34)
        price_entry.insert(0, price_str.replace("₱", "").replace(",", ""))
        price_entry.pack(padx=20)

        ctk.CTkLabel(
            dialog, text="Stock Count", font=FONT_SMALL, text_color=TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(8, 2))
        stock_entry = ctk.CTkEntry(dialog, width=380, height=34)
        stock_entry.insert(0, str(stock))
        stock_entry.pack(padx=20)

        ctk.CTkLabel(
            dialog,
            text="Low Stock Threshold (Trigger Amount)",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=20, pady=(8, 2))
        threshold_entry = ctk.CTkEntry(dialog, width=380, height=34)
        threshold_entry.insert(0, str(threshold))
        threshold_entry.pack(padx=20)

        status_label = ctk.CTkLabel(
            dialog, text="", font=FONT_SMALL, text_color=ACCENT_GREEN
        )
        status_label.pack(anchor="w", padx=20, pady=(6, 0))

        def save():
            import psycopg2

            new_desc = desc_entry.get().strip()
            new_price_str = price_entry.get().strip()
            new_stock_str = stock_entry.get().strip()
            new_thresh_str = threshold_entry.get().strip()

            # Validate
            if not new_desc:
                status_label.configure(
                    text="✗ Description cannot be empty.", text_color=ACCENT_RED
                )
                return
            try:
                new_price = float(new_price_str)
                new_stock = int(new_stock_str)
                new_thresh = int(new_thresh_str)
                if new_price < 0 or new_stock < 0 or new_thresh < 0:
                    raise ValueError
            except ValueError:
                status_label.configure(
                    text="✗ Price must be a number; Stock and Threshold must be whole numbers ≥ 0.",
                    text_color=ACCENT_RED,
                )
                return

            try:
                assert self.db_config is not None
                conn = psycopg2.connect(**self.db_config)
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE parts
                    SET description    = %s,
                        selling_price  = %s,
                        stock_count    = %s,
                        trigger_amount = %s
                    WHERE part_number  = %s
                """,
                    (new_desc, new_price, new_stock, new_thresh, sku),
                )
                conn.commit()
                cur.close()
                conn.close()

                status_label.configure(
                    text="✓ Saved successfully.", text_color=ACCENT_GREEN
                )
                # Refresh catalog table and KPI bar
                self.refresh_catalog_data()
                dialog.after(800, dialog.destroy)

            except Exception as e:
                status_label.configure(text=f"✗ DB Error: {e}", text_color=ACCENT_RED)

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(12, 0))

        ctk.CTkButton(
            btn_row,
            text="💾  Save Changes",
            fg_color=BRAND_BLUE,
            hover_color="#2980b9",
            font=("Segoe UI", 11, "bold"),
            height=34,
            command=save,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="✕  Cancel",
            fg_color="#f3f5f8",
            hover_color="#e0e4eb",
            text_color=TEXT_DARK,
            font=("Segoe UI", 11),
            height=34,
            command=dialog.destroy,
        ).pack(side="left")

    # ════════════════════════════════════════════════════════════════════
    # Helpers
    # ════════════════════════════════════════════════════════════════════

    def _on_parts_table_click(self, event):
        """Fires when user clicks a row. Opens edit dialog if Actions column clicked."""
        assert self._parts_tree is not None
        region = self._parts_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        col_id = self._parts_tree.identify_column(event.x)  # e.g. "#8"
        col_index = int(col_id.replace("#", "")) - 1  # 0-based

        # Actions column is index 7 (the 8th column)
        if col_index != 7:
            return

        selected = self._parts_tree.identify_row(event.y)
        if not selected:
            return

        values = self._parts_tree.item(selected, "values")
        if not values:
            return

        sku = values[0]
        self._open_edit_part_dialog(sku, values)

    def _create_card_container(self, parent):
        return ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )

    def _create_form_field(self, parent, label, is_combo=False):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=(0, 5))
        ctk.CTkLabel(frame, text=label, font=FONT_SMALL, text_color=TEXT_MUTED).pack(
            anchor="w", pady=(0, 3)
        )
        if is_combo:
            ctk.CTkComboBox(
                frame,
                values=["BIC Pens Blue (12pk)", "HP LaserJet Toner"],
                height=28,
                fg_color="#f5f7fa",
                border_color=BORDER,
            ).pack(fill="x")
        else:
            ctk.CTkEntry(
                frame, height=28, fg_color="#f5f7fa", border_color=BORDER
            ).pack(fill="x")

    def _set_toggle_state(self, visible: bool):
        if hasattr(self, "toggle_btn") and self.toggle_btn is not None:
            if visible:
                self.toggle_btn.configure(text="◀", fg_color="#2b9430")
            else:
                self.toggle_btn.configure(text="▶", fg_color="#27ae60")

    def _apply_search_filter(self):
        query = self._search_var.get().lower()
        status_filter = self._filter_var.get()

        result = []
        for r in self._parts_rows:
            # r = (sku, desc, cat, stock, threshold, price, supplier, action)
            sku, desc, _, stock, threshold, *_ = r

            # Search match
            if query and query not in sku.lower() and query not in desc.lower():
                continue

            # Status filter match
            if status_filter == "In Stock" and stock <= 0:
                continue
            if status_filter == "Low Stock" and not (0 < stock <= threshold):
                continue
            if status_filter == "Out of Stock" and stock != 0:
                continue

            result.append(r)

        self._filtered_rows = result
        self._current_page = 1
        self._refresh_parts_table_page()

    def _refresh_parts_table_page(self):
        if self._parts_tree is None:
            return

        # Use filtered rows if available, otherwise fall back to all rows
        rows = getattr(self, "_filtered_rows", self._parts_rows)

        self._parts_tree.delete(*self._parts_tree.get_children())
        total_rows = len(rows)
        total_pages = max(1, (total_rows + self._page_size - 1) // self._page_size)

        if self._current_page > total_pages:
            self._current_page = total_pages
        if self._current_page < 1:
            self._current_page = 1

        start = (self._current_page - 1) * self._page_size
        end = start + self._page_size

        for row in rows[start:end]:
            self._parts_tree.insert("", "end", values=row)

        self._update_pager_state(total_pages)

    def _update_pager_state(self, total_pages: int):
        if hasattr(self, "page_label"):
            self.page_label.configure(text=str(self._current_page))
        if hasattr(self, "page_count_label"):
            self.page_count_label.configure(text=f"of {total_pages}")

        prev_enabled = self._current_page > 1
        next_enabled = self._current_page < total_pages

        for attr in ("prev_btn", "prev_page_btn"):
            btn = getattr(self, attr, None)
            if btn:
                btn.configure(
                    state="normal" if prev_enabled else "disabled",
                    text_color="#6b7280" if prev_enabled else "#c4c9d1",
                )
        for attr in ("next_btn", "next_page_btn"):
            btn = getattr(self, attr, None)
            if btn:
                btn.configure(
                    state="normal" if next_enabled else "disabled",
                    text_color="#6b7280" if next_enabled else "#c4c9d1",
                )
        if hasattr(self, "prev_page_btn"):
            self.prev_page_btn.configure(
                state="normal" if prev_enabled else "disabled",
                text_color="#6b7280" if prev_enabled else "#c4c9d1",
            )
        if hasattr(self, "next_page_btn"):
            self.next_page_btn.configure(
                state="normal" if next_enabled else "disabled",
                text_color="#6b7280" if next_enabled else "#c4c9d1",
            )

    def _go_prev_page(self):
        if self._current_page > 1:
            self._current_page -= 1
            self._refresh_parts_table_page()

    def _go_next_page(self):
        rows = getattr(self, "_filtered_rows", self._parts_rows)
        total_pages = max(1, (len(rows) + self._page_size - 1) // self._page_size)
        if self._current_page < total_pages:
            self._current_page += 1
            self._refresh_parts_table_page()

    def toggle_side_panels(self):
        if self._right_panel_visible:
            self.right_panel.grid_remove()
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=0)
            self._right_panel_visible = False
        else:
            self.right_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            self.grid_columnconfigure(0, weight=3)
            self.grid_columnconfigure(1, weight=1)
            self._right_panel_visible = True

        self._set_toggle_state(self._right_panel_visible)

    def _build_reorder_tab(self):
        self.tab_reorder.columnconfigure(0, weight=1)
        self.tab_reorder.rowconfigure(1, weight=1)

        # Top form
        form_panel = ctk.CTkFrame(
            self.tab_reorder,
            fg_color=CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        form_panel.grid(row=0, column=0, sticky="ew", pady=(0, 10), padx=5)
        form_panel.columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkLabel(form_panel, text="New Reorder Entry", font=FONT_SECTION).grid(
            row=0, column=0, columnspan=5, padx=15, pady=(10, 6), sticky="w"
        )

        ctk.CTkLabel(
            form_panel, text="Part (SKU)", font=FONT_SMALL, text_color=TEXT_MUTED
        ).grid(row=1, column=0, padx=(15, 5), sticky="w")
        self.reorder_sku = ctk.CTkComboBox(
            form_panel,
            values=[r[0] for r in self._parts_rows],
            width=150,
            command=self._on_reorder_sku_changed,
        )
        self.reorder_sku.grid(row=2, column=0, padx=(15, 5), pady=(0, 10), sticky="ew")

        ctk.CTkLabel(
            form_panel, text="Supplier", font=FONT_SMALL, text_color=TEXT_MUTED
        ).grid(row=1, column=1, padx=5, sticky="w")
        self.reorder_supp = ctk.CTkComboBox(
            form_panel,
            values=self._fetch_suppliers(),
            width=200,
            command=self._on_reorder_supplier_changed,
        )
        self.reorder_supp.grid(row=2, column=1, padx=5, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(
            form_panel, text="Qty", font=FONT_SMALL, text_color=TEXT_MUTED
        ).grid(row=1, column=2, padx=5, sticky="w")
        self.reorder_qty = ctk.CTkEntry(
            form_panel, placeholder_text="e.g. 100", width=100
        )
        self.reorder_qty.grid(row=2, column=2, padx=5, pady=(0, 10), sticky="ew")
        self.reorder_qty.bind(
            "<KeyRelease>", lambda *_: self._update_reorder_cost_preview()
        )

        ctk.CTkLabel(
            form_panel, text="Unit Cost", font=FONT_SMALL, text_color=TEXT_MUTED
        ).grid(row=1, column=3, padx=5, sticky="w")
        self._reorder_unit_cost_var = tk.StringVar(value="₱0.00")
        ctk.CTkEntry(
            form_panel,
            textvariable=self._reorder_unit_cost_var,
            state="disabled",
            width=110,
            fg_color="#f5f7fa",
        ).grid(row=2, column=3, padx=5, pady=(0, 10), sticky="ew")

        ctk.CTkButton(
            form_panel,
            text="+ Add to List",
            fg_color=ACCENT_GREEN,
            hover_color="#27ae60",
            font=("Segoe UI", 11, "bold"),
            width=130,
            command=self._submit_to_reorder_list,
        ).grid(row=2, column=4, padx=(5, 15), pady=(0, 10), sticky="ew")

        # Reorder list table
        list_frame = ctk.CTkFrame(
            self.tab_reorder,
            fg_color=CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        list_frame.grid(row=1, column=0, sticky="nsew", padx=5)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure(
            "Reorder.Treeview",
            background=CARD_BG,
            foreground=TEXT_DARK,
            rowheight=36,
            fieldbackground=CARD_BG,
            font=FONT_TABLE,
            borderwidth=0,
        )
        style.configure(
            "Reorder.Treeview.Heading",
            background=BRAND_NAVY,
            foreground=TEXT_WHITE,
            font=("Segoe UI", 11, "bold"),
            relief="flat",
        )
        style.map(
            "Reorder.Treeview",
            background=[("selected", "#d6e4f7")],
            foreground=[("selected", BRAND_NAVY)],
        )

        ro_cols = (
            "PO #",
            "Part SKU",
            "Part Description",
            "Supplier",
            "Qty",
            "Unit Cost",
            "Total",
            "Status",
        )
        ro_widths = (60, 90, 200, 160, 60, 100, 110, 100)

        ro_vsb = ttk.Scrollbar(list_frame, orient="vertical")
        ro_hsb = ttk.Scrollbar(list_frame, orient="horizontal")

        self.reorder_tree = ttk.Treeview(
            list_frame,
            columns=ro_cols,
            show="headings",
            style="Reorder.Treeview",
            yscrollcommand=ro_vsb.set,
            xscrollcommand=ro_hsb.set,
        )
        ro_vsb.configure(command=self.reorder_tree.yview)
        ro_hsb.configure(command=self.reorder_tree.xview)

        for col, width in zip(ro_cols, ro_widths):
            self.reorder_tree.column(col, width=width, anchor="w")
            self.reorder_tree.heading(col, text=col)

        self.reorder_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        ro_vsb.grid(row=0, column=1, sticky="ns")
        ro_hsb.grid(row=1, column=0, sticky="ew")

        # Action bar
        action_bar = ctk.CTkFrame(self.tab_reorder, fg_color="transparent")
        action_bar.grid(row=2, column=0, pady=(8, 0), sticky="ew", padx=5)

        ctk.CTkButton(
            action_bar,
            text="✈  Mark Selected as Shipped",
            fg_color=BRAND_BLUE,
            hover_color="#2980b9",
            font=("Segoe UI", 11, "bold"),
            height=34,
            command=self._mark_shipped,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            action_bar,
            text="⊞  Mark Selected as Received",
            fg_color=ACCENT_GREEN,
            hover_color="#27ae60",
            font=("Segoe UI", 11, "bold"),
            height=34,
            command=self._mark_received_from_reorder,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            action_bar,
            text="↻  Refresh List",
            fg_color="#f3f5f8",
            hover_color="#e0e4eb",
            text_color=TEXT_DARK,
            font=("Segoe UI", 11),
            height=34,
            command=self._load_reorder_list,
        ).pack(side="left")

        self._load_reorder_list()

    def _on_reorder_sku_changed(self, value=None):
        self._update_reorder_cost_preview()

    def _on_reorder_supplier_changed(self, value=None):
        self._update_reorder_cost_preview()

    def _update_reorder_cost_preview(self, *_):
        import psycopg2

        sku = self.reorder_sku.get().strip()
        supplier_name = self.reorder_supp.get().strip()
        if not sku or not supplier_name:
            self._reorder_unit_cost_var.set("₱0.00")
            return
        try:
            assert self.db_config is not None
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ip.cost FROM item_parts ip
                JOIN suppliers s ON s.supplier_id = ip.supplier_id
                WHERE ip.part_number = %s AND s.company_name = %s
            """,
                (sku, supplier_name),
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            self._reorder_unit_cost_var.set(
                f"₱{float(row[0]):,.2f}" if row else "₱0.00"
            )
        except Exception as e:
            print(f"[DB ERROR] cost preview: {e}")
            self._reorder_unit_cost_var.set("₱0.00")

    def _submit_to_reorder_list(self):
        import psycopg2

        sku = self.reorder_sku.get().strip()
        supplier_name = self.reorder_supp.get().strip()
        qty_str = self.reorder_qty.get().strip()

        if not sku or not supplier_name or not qty_str:
            messagebox.showwarning("Validation", "Please fill in all fields.")
            return
        try:
            qty = int(qty_str)
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Validation", "Quantity must be a positive whole number."
            )
            return

        try:
            assert self.db_config is not None
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute(
                "SELECT supplier_id FROM suppliers WHERE company_name = %s",
                (supplier_name,),
            )
            sup_row = cur.fetchone()
            if not sup_row:
                messagebox.showerror("Error", f"Supplier '{supplier_name}' not found.")
                conn.close()
                return
            supplier_id = sup_row[0]

            cur.execute(
                "SELECT cost FROM item_parts WHERE part_number = %s AND supplier_id = %s",
                (sku, supplier_id),
            )
            cost_row = cur.fetchone()
            unit_cost = float(cost_row[0]) if cost_row else 0.0

            cur.execute(
                """
                INSERT INTO purchase_orders
                    (part_number, supplier_id, quantity, unit_cost, received, status)
                VALUES (%s, %s, %s, %s, FALSE, 'Pending')
            """,
                (sku, supplier_id, qty, unit_cost),
            )
            cur.execute(
                "UPDATE parts SET on_order = TRUE WHERE part_number = %s", (sku,)
            )

            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo(
                "Success", f"Reorder added: {qty}× {sku} from {supplier_name}."
            )
            self.reorder_qty.delete(0, "end")
            self._load_reorder_list()
            self._load_parts_data()
            self._apply_search_filter()
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to add reorder:\n{e}")

    def _load_reorder_list(self):
        import psycopg2, psycopg2.extras

        self.reorder_tree.delete(*self.reorder_tree.get_children())
        try:
            assert self.db_config is not None
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT po.po_id, po.part_number, p.description,
                    s.company_name AS supplier_name,
                    po.quantity, po.unit_cost,
                    (po.quantity * po.unit_cost) AS total_cost, po.status
                FROM purchase_orders po
                JOIN parts     p ON p.part_number = po.part_number
                JOIN suppliers s ON s.supplier_id  = po.supplier_id
                ORDER BY po.po_id DESC
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to load reorder list:\n{e}")
            return

        for r in rows:
            tag = (
                "shipped"
                if r["status"] == "Shipped"
                else ("received" if r["status"] == "Received" else "")
            )
            self.reorder_tree.insert(
                "",
                "end",
                tags=(tag,),
                values=(
                    r["po_id"],
                    r["part_number"],
                    r["description"],
                    r["supplier_name"],
                    r["quantity"],
                    f"₱{float(r['unit_cost']):,.2f}",
                    f"₱{float(r['total_cost']):,.2f}",
                    r["status"],
                ),
            )
        self.reorder_tree.tag_configure("shipped", background="#fff9e6")
        self.reorder_tree.tag_configure("received", background="#e8f5e9")

    def _mark_shipped(self):
        self._update_po_status("Shipped")

    def _mark_received_from_reorder(self):
        selected = self.reorder_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select a reorder entry first.")
            return
        po_id = self.reorder_tree.item(selected[0])["values"][0]
        self._receive_po(po_id)

    def _update_po_status(self, new_status: str):
        import psycopg2

        selected = self.reorder_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select a reorder entry first.")
            return
        po_id = self.reorder_tree.item(selected[0])["values"][0]
        try:
            assert self.db_config is not None
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute(
                "UPDATE purchase_orders SET status = %s WHERE po_id = %s",
                (new_status, po_id),
            )
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo("Updated", f"PO #{po_id} marked as {new_status}.")
            self._load_reorder_list()
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to update status:\n{e}")

    def _receive_po(self, po_id):
        import psycopg2

        try:
            assert self.db_config is not None
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute(
                "SELECT part_number, quantity, status FROM purchase_orders WHERE po_id = %s",
                (po_id,),
            )
            po = cur.fetchone()
            if not po:
                messagebox.showerror("Error", f"PO #{po_id} not found.")
                conn.close()
                return
            part_number, quantity, current_status = po
            if current_status == "Received":
                messagebox.showwarning(
                    "Already Received", "This PO has already been received."
                )
                conn.close()
                return
            cur.execute(
                "UPDATE parts SET stock_count = stock_count + %s, on_order = FALSE WHERE part_number = %s",
                (quantity, part_number),
            )
            cur.execute(
                "UPDATE purchase_orders SET received = TRUE, status = 'Received' WHERE po_id = %s",
                (po_id,),
            )
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo("Received", f"PO #{po_id} received. Stock updated.")
            self._load_reorder_list()
            self._load_parts_data()
            self._apply_search_filter()
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to mark received:\n{e}")

    # ════════════════════════════════════════════════════════════════════
    # SECURE ACTION HANDLERS (Phase 3 Integration)
    # ════════════════════════════════════════════════════════════════════

    def handle_add_new_part(self):
        """Action for the '+ Add New Part' button."""
        try:
            # Here you would typically open a modal/dialog, then call the backend:
            # self.controller.query_manager.add_part(data)
            messagebox.showinfo(
                "Inventory Management", "Opening 'Add New Part' dialog..."
            )

        except PermissionError as e:
            # Caught by the @require_role decorator in the backend!
            messagebox.showerror("Security Override", str(e))
        except Exception as e:
            messagebox.showerror("System Error", f"An unexpected error occurred: {e}")

    def handle_submit_po(self):
        import psycopg2
        from tkinter import messagebox

        part_desc = self.po_part_combo.get()
        qty_str = self.po_qty_entry.get().strip()
        supplier_name = self.supplier_combo.get()

        if not part_desc or not qty_str:
            messagebox.showwarning(
                "Validation", "Please select a part and enter a quantity."
            )
            return

        try:
            qty = int(qty_str)
        except ValueError:
            messagebox.showwarning("Validation", "Quantity must be a whole number.")
            return

        # Resolve part_number from description
        part_number = next((r[0] for r in self._parts_rows if r[1] == part_desc), None)
        if not part_number:
            messagebox.showerror("Error", "Could not resolve part number.")
            return

        self._ensure_active_session(["Manager"])

        try:
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor()

            # Resolve supplier_id
            cur.execute(
                "SELECT supplier_id FROM suppliers WHERE company_name = %s",
                (supplier_name,),
            )
            row = cur.fetchone()
            if not row:
                messagebox.showerror("Error", f"Supplier '{supplier_name}' not found.")
                conn.close()
                return
            supplier_id = row[0]

            # Get unit cost from item_parts
            cur.execute(
                "SELECT cost FROM item_parts WHERE part_number = %s AND supplier_id = %s",
                (part_number, supplier_id),
            )
            cost_row = cur.fetchone()
            unit_cost = float(cost_row[0]) if cost_row else 0.0

            # Insert purchase order
            cur.execute(
                """
                INSERT INTO purchase_orders
                    (part_number, supplier_id, quantity, unit_cost, received)
                VALUES (%s, %s, %s, %s, FALSE)
            """,
                (part_number, supplier_id, qty, unit_cost),
            )

            # Mark part as on_order
            cur.execute(
                "UPDATE parts SET on_order = TRUE WHERE part_number = %s",
                (part_number,),
            )

            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo(
                "Success", f"PO submitted: {qty}x {part_desc} from {supplier_name}."
            )
            self._load_parts_data()
            self._refresh_parts_table_page()

        except PermissionError as e:
            messagebox.showerror("Access Denied", str(e))
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to submit PO:\n{e}")

    def handle_mark_received(self):
        import psycopg2
        from tkinter import messagebox

        po_number = self.recv_po_entry.get().strip()
        if not po_number:
            messagebox.showwarning("Validation", "Please enter a PO number.")
            return

        try:
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor()

            # Fetch the PO
            cur.execute(
                """
                SELECT po_id, part_number, quantity, received
                FROM purchase_orders
                WHERE po_id = %s
            """,
                (po_number,),
            )
            po = cur.fetchone()

            if not po:
                messagebox.showerror("Not Found", f"No PO found with ID '{po_number}'.")
                conn.close()
                return

            po_id, part_number, quantity, already_received = po

            if already_received:
                messagebox.showwarning(
                    "Already Received", "This PO has already been marked as received."
                )
                conn.close()
                return

            # Update stock and mark PO received
            cur.execute(
                """
                UPDATE parts
                SET stock_count = stock_count + %s,
                    on_order = FALSE
                WHERE part_number = %s
            """,
                (quantity, part_number),
            )

            cur.execute(
                """
                UPDATE purchase_orders
                SET received = TRUE
                WHERE po_id = %s
            """,
                (po_id,),
            )

            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Success", f"PO {po_number} received. Stock updated.")
            self._load_parts_data()
            self._refresh_parts_table_page()

        except PermissionError as e:
            messagebox.showerror("Access Denied", str(e))
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to mark received:\n{e}")
