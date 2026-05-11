import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
import psycopg2
import psycopg2.extras

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
        total_parts = len(self.parts_data)
        total_value = 0.0
        low_stock_count = 0
        out_of_stock_count = 0

        # Use index-based extraction to prevent unpacking crashes
        for r in self.parts_data:
            try:
                # Ensure stock and threshold are treated as integers
                stock = int(r[3] or 0)
                low_threshold = int(r[4] or 0)
                
                # Safely parse the formatted price string (e.g., "₱1,200.50" -> 1200.50)
                price_str = str(r[5])
                price = float(price_str.replace("₱", "").replace("$", "").replace(",", ""))
                
                total_value += (stock * price)

                # Evaluate thresholds
                if stock == 0:
                    out_of_stock_count += 1
                elif stock <= low_threshold:
                    low_stock_count += 1
                    
            except (ValueError, TypeError, IndexError) as e:
                # Silently skip malformed rows so the UI still loads
                continue

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
                container, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER, height=108,
            )
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 5), pady=0)
            card.pack_propagate(False)

            ctk.CTkLabel(card, text=title, font=("Segoe UI", 11, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=14, pady=(12, 0))
            ctk.CTkLabel(card, text=val, font=("Segoe UI", 22, "bold"), text_color=TEXT_DARK).pack(anchor="w", padx=14, pady=(2, 0))
            ctk.CTkLabel(card, text=sub, font=("Segoe UI", 10), text_color=clr).pack(anchor="w", padx=14, pady=(0, 12))

# ══════════════════════════════════════════════════════════════════════════════
#  INVENTORY VIEW (Main)
# ══════════════════════════════════════════════════════════════════════════════
class InventoryView(ctk.CTkFrame):
    def __init__(self, parent, controller=None, db_config=None, **kwargs):
        super().__init__(parent, fg_color=PAGE_BG, corner_radius=0, border_width=0, **kwargs)
        self.controller = controller
        self.db_config = db_config

        session = getattr(self.controller, "session", None)
        self.role = getattr(session, "role", None) or "Manager"
        self._session_manager = getattr(controller, "session_manager", None)

        self._current_page = 1
        self._page_size = 15
        self._parts_rows = []
        self._filtered_rows = []
        
        # Pylance Fix: Initialize Treeview vars
        self._parts_tree = None
        self.supp_tree = None
        self.reorder_tree = None
        self._tbl_container = None
        
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
            self, fg_color=PAGE_BG, segmented_button_fg_color=PAGE_BG,
            segmented_button_selected_color=BRAND_BLUE, segmented_button_selected_hover_color="#2980b9",
            segmented_button_unselected_color="#ffffff", segmented_button_unselected_hover_color="#eef1f5",
            text_color=TEXT_DARK,
        )
        self.tabs.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 20))

        try:
            seg = self.tabs._segmented_button
            seg.configure(
                corner_radius=20, border_width=1, fg_color=PAGE_BG,
                selected_color=BRAND_BLUE, selected_hover_color="#2980b9",
                unselected_color="#ffffff", unselected_hover_color="#eef1f5",
                text_color=TEXT_DARK, text_color_disabled=TEXT_MUTED, font=("Segoe UI", 12),
            )
        except Exception:
            pass

        self.tab_catalog = self.tabs.add("Parts Catalog")
        self.tab_reorder = self.tabs.add("Stock Reordering")
        self.tab_suppliers = self.tabs.add("Suppliers")

        self._load_parts_data()

        self._build_catalog_tab()
        self._build_reorder_tab()
        self._build_suppliers_tab()

    def _ensure_active_session(self, allowed_roles=None):
        if self._session_manager is not None:
            self._session_manager.ensure_active(allowed_roles)

    def _load_parts_data(self):
        try:
            # Pylance Fix: Use (self.db_config or {})
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT
                    p.part_number, p.description, p.selling_price, p.stock_count, p.trigger_amount, p.on_order,
                    s.company_name AS best_supplier_name
                FROM parts p
                LEFT JOIN LATERAL (
                    SELECT ip.supplier_id FROM item_parts ip WHERE ip.part_number = p.part_number ORDER BY ip.cost ASC LIMIT 1
                ) bs ON TRUE
                LEFT JOIN suppliers s ON s.supplier_id = bs.supplier_id
                ORDER BY p.part_number
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            self._parts_rows = []
            for r in rows:
                self._parts_rows.append((
                    str(r["part_number"]), r["description"], "General", r["stock_count"], r["trigger_amount"],
                    f"₱{float(r['selling_price']):,.2f}", r["best_supplier_name"] or "—", "✏️ Edit",
                ))
            self._filtered_rows = list(self._parts_rows)

        except Exception as e:
            print(f"[DB ERROR] _load_parts_data: {e}")
            self._parts_rows = []
            self._filtered_rows = []

    def _fetch_suppliers(self):
        try:
            conn = psycopg2.connect(**(self.db_config or {}))
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
        self.tab_catalog.columnconfigure(0, weight=3)
        self.tab_catalog.columnconfigure(1, weight=0)
        self.tab_catalog.rowconfigure(0, weight=1)

        # ── LEFT COLUMN wrapper ──
        self.left_panel = ctk.CTkFrame(self.tab_catalog, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.left_panel.columnconfigure(0, weight=1)
        self.left_panel.rowconfigure(2, weight=1) 

        # Row 0: KPI Bar
        self.kpi = InventoryKPIBar(self.left_panel, self._parts_rows)
        self.kpi.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        
        # Row 1 & 2: Search and Table
        self._build_catalog_section()

        # ── RIGHT COLUMN: scrollable action panels ──
        self.right_panel = ctk.CTkScrollableFrame(self.tab_catalog, width=300, fg_color=PAGE_BG, scrollbar_button_color=BORDER)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        self._build_place_order_card()
        self._build_bottleneck_card()
        self._build_admin_actions_card()

    def _build_catalog_section(self):
        hdr = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        hdr.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        hdr.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr, text=f"Parts Catalog", font=FONT_TITLE, text_color=TEXT_DARK
        ).grid(row=0, column=0, sticky="w")

        actions = ctk.CTkFrame(hdr, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e")

        self.add_btn = ctk.CTkButton(
            actions, text="+ Add New Part", width=130, height=34, corner_radius=6,
            fg_color=BRAND_BLUE, hover_color="#2980b9", font=("Segoe UI", 12, "bold"),
            command=self.handle_add_new_part,
        )
        self.add_btn.pack(side="left", padx=(0, 8))

        if self.role != "Manager":
            self.add_btn.configure(state="disabled", fg_color="#bdc3c7", text_color="#7f8c8d")

        search_bar = ctk.CTkFrame(self.left_panel, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER)
        search_bar.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        inner = ctk.CTkFrame(search_bar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=10) # Increased outer padding to give elements room to breathe

        # --- LEFT SIDE: Search & Filter ---
        left_tools = ctk.CTkFrame(inner, fg_color="transparent")
        left_tools.pack(side="left", fill="x", expand=True)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_search_filter())
        
        ctk.CTkEntry(
            left_tools, textvariable=self._search_var, placeholder_text="Search parts…", width=250, height=34
        ).pack(side="left", padx=(0, 20)) # Added 20px gap after the search bar

        ctk.CTkLabel(left_tools, text="Filter:", font=FONT_BODY, text_color=TEXT_MUTED).pack(side="left", padx=(0, 10))
        
        self._filter_var = tk.StringVar(value="All")
        self._filter_var.trace_add("write", lambda *_: self._apply_search_filter())
        ctk.CTkOptionMenu(
            left_tools, variable=self._filter_var, values=["All", "In Stock", "Low Stock", "Out of Stock"],
            width=140, height=34, fg_color="#f5f7fa", button_color=BRAND_BLUE, text_color=TEXT_DARK
        ).pack(side="left")

        # --- RIGHT SIDE: Refresh & Pagination ---
        right_tools = ctk.CTkFrame(inner, fg_color="transparent")
        right_tools.pack(side="right")

        self.refresh_btn = ctk.CTkButton(
            right_tools, text="↻", width=34, height=34, corner_radius=6,
            fg_color=BRAND_BLUE, hover_color="#2980b9", command=self.refresh_catalog_data
        )
        self.refresh_btn.pack(side="left", padx=(0, 20)) # Added 20px gap to cleanly separate refresh from pagination

        self.prev_btn = ctk.CTkButton(
            right_tools, text="‹", width=30, height=28, corner_radius=6,
            fg_color="#f3f5f8", hover_color="#e8ecf2", text_color="#9ca3af",
            font=("Segoe UI", 13, "bold"), command=self._go_prev_page
        )
        self.prev_btn.pack(side="left", padx=(0, 8))

        self.page_label = ctk.CTkLabel(
            right_tools, text="1", width=30, height=28, fg_color="transparent", # Removed the white box so text flows naturally
            text_color=TEXT_DARK, font=("Segoe UI", 12, "bold")
        )
        self.page_label.pack(side="left", padx=(0, 4))

        self.page_count_label = ctk.CTkLabel(right_tools, text="of 1", text_color="#374151", font=("Segoe UI", 11))
        self.page_count_label.pack(side="left", padx=(0, 8))

        self.next_btn = ctk.CTkButton(
            right_tools, text="›", width=30, height=28, corner_radius=6,
            fg_color="#f3f5f8", hover_color="#e8ecf2", text_color="#9ca3af",
            font=("Segoe UI", 13, "bold"), command=self._go_next_page
        )
        self.next_btn.pack(side="left", padx=(0, 0))

        tbl_frame = ctk.CTkFrame(self.left_panel, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER)
        tbl_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 0))
        self.left_panel.rowconfigure(3, weight=1)

        self._build_parts_table(tbl_frame)

    def refresh_catalog_data(self):
        self._load_parts_data()
        self._filtered_rows = list(self._parts_rows)

        # Refresh KPI bar in the main view
        self.kpi.destroy()
        self.kpi = InventoryKPIBar(self, self._parts_rows)
        self.kpi.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))

        self._apply_search_filter()
        
        # --- NEW: Sync the dropdowns on the other tabs! ---
        if hasattr(self, 'supp_part_combo'):
            part_options = [r[1] for r in self._parts_rows] if self._parts_rows else ["No parts available"]
            self.supp_part_combo.configure(values=part_options)

    def _build_parts_table(self, parent):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Parts.Treeview", background=CARD_BG, foreground=TEXT_DARK, rowheight=36, fieldbackground=CARD_BG, font=FONT_TABLE, borderwidth=0)
        style.configure("Parts.Treeview.Heading", background=BRAND_NAVY, foreground=TEXT_WHITE, font=("Segoe UI", 11, "bold"), relief="flat")
        style.map("Parts.Treeview", background=[("selected", "#d6e4f7")], foreground=[("selected", BRAND_NAVY)])

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        vsb = ttk.Scrollbar(container, orient="vertical")
        hsb = ttk.Scrollbar(container, orient="horizontal")

        cols = ("SKU", "Part Description", "Category", "Stock Count", "Low Stock Threshold", "Selling ", "Best Supplier", "Actions")
        widths = (80, 220, 100, 80, 130, 120, 160, 80)

        tree = ttk.Treeview(container, columns=cols, show="headings", style="Parts.Treeview", yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.configure(command=tree.yview)
        hsb.configure(command=tree.xview)

        for col, width in zip(cols, widths):
            tree.column(col, width=width, anchor="w")
            tree.heading(col, text=col)
            anchor = "center" if col == "Actions" else "w"
            tree.column(col, width=width, anchor=anchor)

        self._parts_tree = tree
        self._tbl_container = container
        container.bind("<Configure>", self._on_table_resize)
        self._current_page = 1

        tree.bind("<ButtonRelease-1>", self._on_parts_table_click)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._refresh_parts_table_page()

    def _on_table_resize(self, event=None):
        if self._parts_tree is None or self._tbl_container is None: return
        row_height = 36  
        header_height = 28  
        available_height = event.height if event else (self._tbl_container.winfo_height() if self._tbl_container else 400)
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
        ctk.CTkLabel(hdr, text="Place Restock Order", font=FONT_SECTION, text_color=TEXT_DARK).pack(anchor="w")

        badge = ctk.CTkLabel(card, text="✓ Auto-Suggested: Lowest Cost Supplier", fg_color="#e8f5e9", text_color="#2e7d32", font=("Segoe UI", 9, "bold"), corner_radius=4)
        badge.pack(fill="x", padx=10, pady=(6, 6))

        frame = ctk.CTkFrame(card, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=(0, 5))
        ctk.CTkLabel(frame, text="Part Name/SKU", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 3))
        
        self.po_part_combo = ctk.CTkComboBox(
            frame, 
            values=[r[1] for r in self._parts_rows], 
            height=28, 
            fg_color="#f5f7fa", 
            border_color=BORDER,
            command=self._on_po_part_changed 
        )
        self.po_part_combo.pack(fill="x")

        qty_supplier = ctk.CTkFrame(card, fg_color="transparent")
        qty_supplier.pack(fill="x", padx=10, pady=(2, 3))
        qty_supplier.columnconfigure(0, weight=1)
        qty_supplier.columnconfigure(1, weight=1)

        qty_frame = ctk.CTkFrame(qty_supplier, fg_color="transparent")
        qty_frame.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(qty_frame, text="Quantity", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w")
        self.po_qty_entry = ctk.CTkEntry(qty_frame, height=28, fg_color="#f5f7fa", placeholder_text="500")
        self.po_qty_entry.pack(fill="x", pady=(2, 0))

        supp_frame = ctk.CTkFrame(qty_supplier, fg_color="transparent")
        supp_frame.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(supp_frame, text="Supplier", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w")
        self.supplier_combo = ctk.CTkComboBox(supp_frame, values=self._fetch_suppliers(), height=28, fg_color="#f5f7fa")
        self.supplier_combo.pack(fill="x", pady=(2, 0))
        
        self.supplier_combo.configure(command=lambda _: self._update_po_sidebar_total())
        self.po_qty_entry.bind("<KeyRelease>", lambda _: self._update_po_sidebar_total())

        self.po_total_label = ctk.CTkLabel(card, text="Total: ₱0.00", font=("Segoe UI", 16, "bold"), text_color=TEXT_DARK)
        self.po_total_label.pack(anchor="e", padx=15, pady=(10, 0))

        self.submit_po_btn = ctk.CTkButton(card, text="✈ Submit PO", height=32, corner_radius=6, fg_color=BRAND_BLUE, hover_color="#2980b9", font=("Segoe UI", 11, "bold"), command=self.handle_submit_po)
        self.submit_po_btn.pack(fill="x", padx=10, pady=(10, 8))

        if self.role != "Manager":
            self.submit_po_btn.configure(state="disabled", fg_color="#bdc3c7", text_color="#7f8c8d")
    
    def _on_po_part_changed(self, selected_desc):
        import psycopg2

        part_number = next((r[0] for r in self._parts_rows if r[1] == selected_desc), None)
        if not part_number:
            return

        try:
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor()

            cur.execute("""
                SELECT s.company_name, ip.cost 
                FROM item_parts ip
                JOIN suppliers s ON s.supplier_id = ip.supplier_id
                WHERE ip.part_number = %s
                ORDER BY ip.cost ASC
            """, (part_number,))
            
            results = cur.fetchall()
            conn.close()

            if results:
                # Format: "Company Name — ₱XX.XX"
                supplier_options = [f"{row[0]} — ₱{float(row[1]):,.2f}" for row in results]
                
                self.supplier_combo.configure(values=supplier_options)
                self.supplier_combo.set(supplier_options[0]) # Auto-select cheapest
                
                # Trigger the cost preview to update immediately
                self._update_reorder_cost_preview()
            else:
                self.supplier_combo.configure(values=["No suppliers found"])
                self.supplier_combo.set("No suppliers found")
                self._reorder_unit_cost_var.set("₱0.00")

        except Exception as e:
            print(f"[DB ERROR] Failed to auto-suggest supplier: {e}")
            
        self._update_po_sidebar_total()

    def _build_bottleneck_card(self):
        card = self._create_card_container(self.right_panel)
        card.pack(fill="x", pady=(0, 8))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(hdr, text="⚠ Order Bottlenecks", font=FONT_SECTION, text_color=ACCENT_RED).pack(side="left")
        ctk.CTkButton(hdr, text="↻", width=28, height=28, corner_radius=6, fg_color="#f5f7fa", text_color=TEXT_DARK, command=self._refresh_bottlenecks).pack(side="right")

        self._bottleneck_frame = ctk.CTkFrame(card, fg_color="transparent")
        self._bottleneck_frame.pack(fill="x", padx=10, pady=(0, 8))
        self._refresh_bottlenecks()

    def _refresh_bottlenecks(self):
        for w in self._bottleneck_frame.winfo_children(): w.destroy()
        try:
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT p.part_number, p.description, p.stock_count, COUNT(DISTINCT i.invoice_id) AS blocked_order_count
                FROM parts p
                JOIN invoice_lines il ON il.part_number = p.part_number
                JOIN invoices i ON i.invoice_id = il.invoice_id
                WHERE i.status = 'active'
                AND p.stock_count <= 1
                AND p.on_order = FALSE
                GROUP BY p.part_number, p.description, p.stock_count
                ORDER BY p.stock_count ASC
            """)
            bottlenecks = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            ctk.CTkLabel(self._bottleneck_frame, text=f"DB Error: {e}", text_color=ACCENT_RED, font=FONT_SMALL).pack()
            return

        if not bottlenecks:
            ctk.CTkLabel(self._bottleneck_frame, text="✓ No bottlenecks detected", font=FONT_SMALL, text_color=ACCENT_GREEN).pack(anchor="w")
            return

        for b in bottlenecks:
            row = ctk.CTkFrame(self._bottleneck_frame, fg_color="#fff5f5", corner_radius=6)
            row.pack(fill="x", pady=(0, 4))
            ctk.CTkLabel(row, text=f"Part {b['part_number']} — {b['description'][:28]}", font=("Segoe UI", 10, "bold"), text_color=ACCENT_RED).pack(anchor="w", padx=8, pady=(4, 0))
            ctk.CTkLabel(row, text=f"Stock: {b['stock_count']}  |  Blocking {b['blocked_order_count']} order(s)", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w", padx=8, pady=(0, 4))

    def _build_admin_actions_card(self):
        card = self._create_card_container(self.right_panel)
        card.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(card, text="Admin Actions", font=FONT_SECTION, text_color=TEXT_DARK).pack(anchor="w", padx=10, pady=(8, 6))

        self.restock_btn = ctk.CTkButton(card, text="⟳ Apply Dynamic Restock", height=32, corner_radius=6, fg_color=ACCENT_AMBER, font=("Segoe UI", 11, "bold"), command=self.handle_apply_dynamic_restock)
        self.restock_btn.pack(fill="x", padx=10, pady=(0, 6))

        self.inflate_btn = ctk.CTkButton(card, text="↑ Apply Price Inflation", height=32, corner_radius=6, fg_color=ACCENT_RED, font=("Segoe UI", 11, "bold"), command=self.handle_apply_price_inflation)
        self.inflate_btn.pack(fill="x", padx=10, pady=(0, 8))

        if self.role != "Manager":
            for btn in (self.restock_btn, self.inflate_btn):
                btn.configure(state="disabled", fg_color="#bdc3c7", text_color="#7f8c8d")

    # ════════════════════════════════════════════════════════════════════
    # LOGIC HANDLERS
    # ════════════════════════════════════════════════════════════════════

    def handle_apply_dynamic_restock(self):
        try:
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor()
            cur.execute("""
                SELECT il.part_number, SUM(il.quantity_ordered) AS ytd_qty
                FROM invoice_lines il
                JOIN invoices i ON i.invoice_id = il.invoice_id
                WHERE EXTRACT(YEAR FROM i.date_written) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND i.status != 'void'
                GROUP BY il.part_number
                ORDER BY ytd_qty DESC
                LIMIT 2
            """)
            top_parts = [row[0] for row in cur.fetchall()]

            if not top_parts:
                messagebox.showinfo("Dynamic Restock", "No YTD sales data found. Nothing updated.")
                conn.close()
                return

            cur.execute("UPDATE parts SET trigger_amount = trigger_amount * 2 WHERE part_number = ANY(%s)", (top_parts,))
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Dynamic Restock", f"Restock threshold doubled for {len(top_parts)} part(s):\n" + "\n".join(str(p) for p in top_parts))
            self._load_parts_data()
            self._refresh_parts_table_page()
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to apply dynamic restock:\n{e}")

    def handle_apply_price_inflation(self):
        confirm = messagebox.askyesno("Confirm Price Inflation", "Increase prices for all parts with no YTD sales?\n\n• restock_value < 4  →  +10%\n• restock_value ≥ 4  →  +20%\n\nContinue?")
        if not confirm: return
        self._ensure_active_session(["Manager"])

        try:
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor()
            cur.execute("""
                SELECT p.part_number, p.restock_value
                FROM parts p
                WHERE p.part_number NOT IN (
                    SELECT DISTINCT il.part_number
                    FROM invoice_lines il
                    JOIN invoices i ON i.invoice_id = il.invoice_id
                    WHERE EXTRACT(YEAR FROM i.date_written) = EXTRACT(YEAR FROM CURRENT_DATE)
                    AND i.status != 'void'
                )
            """)
            zero_parts = cur.fetchall()

            if not zero_parts:
                messagebox.showinfo("Price Inflation", "All parts have YTD sales. Nothing updated.")
                conn.close()
                return

            updated = 0
            for part_number, restock_value in zero_parts:
                multiplier = 1.10 if float(restock_value or 0) < 4 else 1.20
                cur.execute("UPDATE parts SET selling_price = selling_price * %s WHERE part_number = %s", (multiplier, part_number))
                updated += 1

            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Price Inflation", f"Updated prices for {updated} part(s).")
            self._load_parts_data()
            self._refresh_parts_table_page()
            self.kpi._build()
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to apply price inflation:\n{e}")

    def handle_add_new_part(self):
        """Opens a modal to add a completely new part to the database."""
        if self.role != "Manager":
            messagebox.showwarning("Access Denied", "Only Managers can add new parts.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Add New Part")
        dialog.geometry("450x500")
        dialog.grab_set() 
        dialog.focus()

        ctk.CTkLabel(dialog, text="Create New Catalog Item", font=("Segoe UI", 16, "bold"), text_color=TEXT_DARK).pack(anchor="w", padx=20, pady=(20, 10))

        # Helper to create consistent entry fields
        def make_entry(label, placeholder):
            ctk.CTkLabel(dialog, text=label, font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(5, 2))
            entry = ctk.CTkEntry(dialog, placeholder_text=placeholder, width=410, height=34)
            entry.pack(padx=20)
            return entry

        sku_entry = make_entry("Part Number / SKU *", "e.g. PN-1001")
        desc_entry = make_entry("Description *", "e.g. Ballpoint Pen - Red")
        price_entry = make_entry("Selling Price (₱) *", "e.g. 15.00")
        stock_entry = make_entry("Initial Stock", "e.g. 0")
        thresh_entry = make_entry("Low Stock Threshold", "e.g. 50")

        status_label = ctk.CTkLabel(dialog, text="", font=FONT_SMALL, text_color=ACCENT_RED)
        status_label.pack(anchor="w", padx=20, pady=(10, 0))

        def save_part():
            import psycopg2
            
            sku = sku_entry.get().strip()
            desc = desc_entry.get().strip()
            price_str = price_entry.get().strip()
            stock_str = stock_entry.get().strip() or "0"
            thresh_str = thresh_entry.get().strip() or "0"

            # 1. Validation
            if not sku or not desc or not price_str:
                status_label.configure(text="✗ Please fill all required (*) fields.", text_color=ACCENT_RED)
                return

            try:
                price = float(price_str)
                stock = int(stock_str)
                thresh = int(thresh_str)
                if price < 0 or stock < 0 or thresh < 0: raise ValueError
            except ValueError:
                status_label.configure(text="✗ Price, Stock, and Threshold must be positive numbers.", text_color=ACCENT_RED)
                return

            # 2. Database Insert
            try:
                conn = psycopg2.connect(**(self.db_config or {}))
                cur = conn.cursor()
                
                # Check if SKU already exists
                cur.execute("SELECT 1 FROM parts WHERE part_number = %s", (sku,))
                if cur.fetchone():
                    status_label.configure(text=f"✗ Part Number '{sku}' already exists.", text_color=ACCENT_RED)
                    conn.close()
                    return

                cur.execute(
                    """INSERT INTO parts (part_number, description, selling_price, stock_count, trigger_amount, on_order) 
                       VALUES (%s, %s, %s, %s, %s, FALSE)""",
                    (sku, desc, price, stock, thresh)
                )
                conn.commit()
                cur.close()
                conn.close()

                messagebox.showinfo("Success", f"Part '{desc}' added to catalog!")
                
                # 3. Refresh UI Elements
                self.refresh_catalog_data() 
                dialog.destroy()

            except Exception as e:
                status_label.configure(text=f"✗ DB Error: {e}", text_color=ACCENT_RED)

        # Buttons
        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(15, 20))
        ctk.CTkButton(btn_row, text="💾 Save Part", fg_color=BRAND_BLUE, font=("Segoe UI", 11, "bold"), height=34, command=save_part).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="✕ Cancel", fg_color="#f3f5f8", text_color=TEXT_DARK, font=("Segoe UI", 11), height=34, command=dialog.destroy).pack(side="left")

    def handle_submit_po(self):
        part_desc = self.po_part_combo.get()
        qty_str = self.po_qty_entry.get().strip()
        supplier_name = self.supplier_combo.get()

        if not part_desc or not qty_str: return messagebox.showwarning("Validation", "Select a part and quantity.")
        try: qty = int(qty_str)
        except ValueError: return messagebox.showwarning("Validation", "Quantity must be a whole number.")

        part_number = next((r[0] for r in self._parts_rows if r[1] == part_desc), None)
        if not part_number: return messagebox.showerror("Error", "Could not resolve part number.")

        self._ensure_active_session(["Manager"])

        try:
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor()
            cur.execute("SELECT supplier_id FROM suppliers WHERE company_name = %s", (supplier_name,))
            row = cur.fetchone()
            if not row: return messagebox.showerror("Error", f"Supplier '{supplier_name}' not found.")
            supplier_id = row[0]

            cur.execute("INSERT INTO purchase_orders (part_number, supplier_id, quantity_ordered) VALUES (%s, %s, %s)", (part_number, supplier_id, qty))
            cur.execute("UPDATE parts SET on_order = TRUE WHERE part_number = %s", (part_number,))

            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Success", f"PO submitted: {qty}x {part_desc} from {supplier_name}.")
            self._load_parts_data()
            self._refresh_parts_table_page()
        except PermissionError as e:
            messagebox.showerror("Access Denied", str(e))
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to submit PO:\n{e}")

    def _open_edit_part_dialog(self, sku, values):
        _, desc, _, stock, threshold, price_str, supplier, _ = values

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit Part — SKU {sku}")
        dialog.geometry("420x380")
        dialog.grab_set() 
        dialog.focus()

        ctk.CTkLabel(dialog, text=f"Editing Part: {sku}", font=("Segoe UI", 14, "bold"), text_color=TEXT_DARK).pack(anchor="w", padx=20, pady=(16, 4))
        ctk.CTkLabel(dialog, text="Description", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(8, 2))
        desc_entry = ctk.CTkEntry(dialog, width=380, height=34)
        desc_entry.insert(0, desc)
        desc_entry.pack(padx=20)

        ctk.CTkLabel(dialog, text="Selling Price (₱)", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(8, 2))
        price_entry = ctk.CTkEntry(dialog, width=380, height=34)
        price_entry.insert(0, price_str.replace("₱", "").replace(",", ""))
        price_entry.pack(padx=20)

        ctk.CTkLabel(dialog, text="Stock Count", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(8, 2))
        stock_entry = ctk.CTkEntry(dialog, width=380, height=34)
        stock_entry.insert(0, str(stock))
        stock_entry.pack(padx=20)

        ctk.CTkLabel(dialog, text="Low Stock Threshold (Trigger Amount)", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(8, 2))
        threshold_entry = ctk.CTkEntry(dialog, width=380, height=34)
        threshold_entry.insert(0, str(threshold))
        threshold_entry.pack(padx=20)

        status_label = ctk.CTkLabel(dialog, text="", font=FONT_SMALL, text_color=ACCENT_GREEN)
        status_label.pack(anchor="w", padx=20, pady=(6, 0))

        def save():
            new_desc = desc_entry.get().strip()
            new_price_str = price_entry.get().strip()
            new_stock_str = stock_entry.get().strip()
            new_thresh_str = threshold_entry.get().strip()

            if not new_desc: return status_label.configure(text="✗ Description cannot be empty.", text_color=ACCENT_RED)
            try:
                new_price = float(new_price_str)
                new_stock = int(new_stock_str)
                new_thresh = int(new_thresh_str)
                if new_price < 0 or new_stock < 0 or new_thresh < 0: raise ValueError
            except ValueError:
                return status_label.configure(text="✗ Invalid numbers.", text_color=ACCENT_RED)

            try:
                conn = psycopg2.connect(**(self.db_config or {}))
                cur = conn.cursor()
                cur.execute("UPDATE parts SET description = %s, selling_price = %s, stock_count = %s, trigger_amount = %s WHERE part_number = %s",
                            (new_desc, new_price, new_stock, new_thresh, sku))
                conn.commit()
                cur.close()
                conn.close()

                status_label.configure(text="✓ Saved successfully.", text_color=ACCENT_GREEN)
                self.refresh_catalog_data()
                dialog.after(800, dialog.destroy)
            except Exception as e: status_label.configure(text=f"✗ DB Error: {e}", text_color=ACCENT_RED)

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(12, 0))
        ctk.CTkButton(btn_row, text="💾 Save Changes", fg_color=BRAND_BLUE, command=save).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="✕ Cancel", fg_color="#f3f5f8", text_color=TEXT_DARK, command=dialog.destroy).pack(side="left")

    def _on_parts_table_click(self, event):
        if not self._parts_tree: return 
        region = self._parts_tree.identify_region(event.x, event.y)
        if region != "cell": return
        col_id = self._parts_tree.identify_column(event.x) 
        if col_id != "#8": return

        if self.role != "Manager": return messagebox.showwarning("Access Denied", "Only Managers can edit parts.")
        
        selected = self._parts_tree.identify_row(event.y)
        if not selected: return
        values = self._parts_tree.item(selected, "values")
        if not values: return

        sku = values[0]
        self._open_edit_part_dialog(sku, values)

    def _create_card_container(self, parent):
        return ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER)

    def _apply_search_filter(self):
        query = self._search_var.get().lower()
        status_filter = self._filter_var.get()
        result = []
        for r in self._parts_rows:
            sku, desc, _, stock, threshold, *_ = r
            if query and query not in sku.lower() and query not in desc.lower(): continue
            if status_filter == "In Stock" and stock <= 0: continue
            if status_filter == "Low Stock" and not (0 < stock <= threshold): continue
            if status_filter == "Out of Stock" and stock != 0: continue
            result.append(r)
        self._filtered_rows = result
        self._current_page = 1
        self._refresh_parts_table_page()

    def _refresh_parts_table_page(self):
        if self._parts_tree is None: return
        rows = getattr(self, "_filtered_rows", self._parts_rows)
        self._parts_tree.delete(*self._parts_tree.get_children())
        
        total_rows = len(rows)
        total_pages = max(1, (total_rows + self._page_size - 1) // self._page_size)

        if self._current_page > total_pages: self._current_page = total_pages
        if self._current_page < 1: self._current_page = 1

        start = (self._current_page - 1) * self._page_size
        end = start + self._page_size

        for row in rows[start:end]: self._parts_tree.insert("", "end", values=row)
        self._update_pager_state(total_pages)

    def _update_pager_state(self, total_pages: int):
        if hasattr(self, "page_label"): self.page_label.configure(text=str(self._current_page))
        if hasattr(self, "page_count_label"): self.page_count_label.configure(text=f"of {total_pages}")
        prev_enabled = self._current_page > 1
        next_enabled = self._current_page < total_pages
        if hasattr(self, "prev_btn"): self.prev_btn.configure(state="normal" if prev_enabled else "disabled")
        if hasattr(self, "next_btn"): self.next_btn.configure(state="normal" if next_enabled else "disabled")

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
            
    def _update_po_sidebar_total(self, *_):
        part_desc = getattr(self, 'po_part_combo', None)
        supplier_name = getattr(self, 'supplier_combo', None)
        qty_entry = getattr(self, 'po_qty_entry', None)
        
        if not part_desc or not supplier_name or not qty_entry: return
        
        part_desc = part_desc.get().strip()
        supplier_name = supplier_name.get().strip().split(" — ")[0]
        qty_str = qty_entry.get().strip()
        
        unit_cost = 0.0
        part_number = next((r[0] for r in self._parts_rows if r[1] == part_desc), None)
        
        if part_number and supplier_name:
            try:
                import psycopg2
                conn = psycopg2.connect(**(self.db_config or {}))
                cur = conn.cursor()
                cur.execute("SELECT ip.cost FROM item_parts ip JOIN suppliers s ON s.supplier_id = ip.supplier_id WHERE ip.part_number = %s AND s.company_name = %s", (part_number, supplier_name))
                row = cur.fetchone()
                conn.close()
                if row: unit_cost = float(row[0])
            except Exception: pass
            
        try:
            qty = int(qty_str) if qty_str else 0
            total = unit_cost * qty
            if hasattr(self, 'po_total_label'): self.po_total_label.configure(text=f"Total: ₱{total:,.2f}")
        except ValueError:
            if hasattr(self, 'po_total_label'): self.po_total_label.configure(text="Total: ₱0.00")

    # ════════════════════════════════════════════════════════════════════
    # TAB 2: REORDERING
    # ════════════════════════════════════════════════════════════════════
    def _build_reorder_tab(self):
        self.tab_reorder.columnconfigure(0, weight=1)
        self.tab_reorder.rowconfigure(1, weight=1)

        form_panel = ctk.CTkFrame(self.tab_reorder, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER)
        form_panel.grid(row=0, column=0, sticky="ew", pady=(0, 10), padx=5)
        form_panel.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        ctk.CTkLabel(form_panel, text="New Reorder Entry", font=FONT_SECTION).grid(row=0, column=0, columnspan=6, padx=15, pady=(10, 6), sticky="w")
        
       # Changed label to indicate they can search
        ctk.CTkLabel(form_panel, text="Part (Type to search...)", font=FONT_SMALL, text_color=TEXT_MUTED).grid(row=1, column=0, padx=(15, 5), sticky="w")
        
        # Combine SKU and Description into one string
        self.reorder_part_options = [f"{r[0]} - {r[1]}" for r in getattr(self, '_parts_rows', [])] if getattr(self, '_parts_rows', []) else ["No parts available"]
        
        # Make it wider (width=250) and add the modern dropdown styling
        self.reorder_sku = ctk.CTkComboBox(
            form_panel, 
            values=self.reorder_part_options, 
            width=250, 
            fg_color="#f5f7fa", 
            border_color=BORDER,
            dropdown_fg_color="#ffffff",
            dropdown_hover_color="#d6e4f7",
            dropdown_text_color="#2c3e50",
            command=self._on_reorder_sku_changed
        )
        self.reorder_sku.set("") # Start empty so they can type
        self.reorder_sku.grid(row=2, column=0, padx=(15, 5), pady=(0, 10), sticky="ew")

        # --- Autocomplete Search Filter ---
        def filter_reorder_parts(event):
            if event.keysym in ("Up", "Down", "Return"): return
            typed_text = self.reorder_sku.get().lower()
            if typed_text == "":
                self.reorder_sku.configure(values=self.reorder_part_options)
            else:
                matches = [p for p in self.reorder_part_options if typed_text in p.lower()]
                self.reorder_sku.configure(values=matches if matches else ["No match found"])

        self.reorder_sku.bind("<KeyRelease>", filter_reorder_parts)
        # ----------------------------------

        ctk.CTkLabel(form_panel, text="Supplier", font=FONT_SMALL, text_color=TEXT_MUTED).grid(row=1, column=1, padx=5, sticky="w")
        self.reorder_supp = ctk.CTkComboBox(form_panel, values=self._fetch_suppliers(), width=200, command=self._on_reorder_supplier_changed)
        self.reorder_supp.grid(row=2, column=1, padx=5, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(form_panel, text="Qty", font=FONT_SMALL, text_color=TEXT_MUTED).grid(row=1, column=2, padx=5, sticky="w")
        self.reorder_qty = ctk.CTkEntry(form_panel, placeholder_text="e.g. 100", width=100)
        self.reorder_qty.grid(row=2, column=2, padx=5, pady=(0, 10), sticky="ew")
        self.reorder_qty.bind("<KeyRelease>", lambda *_: self._update_reorder_cost_preview())

        ctk.CTkLabel(form_panel, text="Unit Cost", font=FONT_SMALL, text_color=TEXT_MUTED).grid(row=1, column=3, padx=5, sticky="w")
        self._reorder_unit_cost_var = tk.StringVar(value="₱0.00")
        ctk.CTkEntry(form_panel, textvariable=self._reorder_unit_cost_var, state="disabled", width=110, fg_color="#f5f7fa").grid(row=2, column=3, padx=5, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(form_panel, text="Total Cost", font=FONT_SMALL, text_color=TEXT_MUTED).grid(row=1, column=4, padx=5, sticky="w")
        self._reorder_total_cost_var = tk.StringVar(value="₱0.00")
        ctk.CTkEntry(
            form_panel, textvariable=self._reorder_total_cost_var, state="disabled", 
            width=110, fg_color="#e8f5e9", text_color="#2e7d32" # Slightly green tint to stand out
        ).grid(row=2, column=4, padx=5, pady=(0, 10), sticky="ew")

        # Shifted button to column 5
        ctk.CTkButton(
            form_panel, text="+ Restock Ordert", fg_color=ACCENT_GREEN, font=("Segoe UI", 11, "bold"), 
            width=130, command=self._submit_to_reorder_list
        ).grid(row=2, column=5, padx=(5, 15), pady=(0, 10), sticky="ew")

        list_frame = ctk.CTkFrame(self.tab_reorder, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=5)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        ro_cols = ("PO #", "Part SKU", "Part Description", "Supplier", "Qty", "Unit Cost", "Total", "Status")
        ro_widths = (60, 90, 200, 160, 60, 100, 110, 100)
        self.reorder_tree = ttk.Treeview(list_frame, columns=ro_cols, show="headings", style="Parts.Treeview")
        ro_vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.reorder_tree.yview)
        ro_hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.reorder_tree.xview)
        self.reorder_tree.configure(yscrollcommand=ro_vsb.set, xscrollcommand=ro_hsb.set)

        for col, width in zip(ro_cols, ro_widths):
            self.reorder_tree.column(col, width=width, anchor="w")
            self.reorder_tree.heading(col, text=col)

        self.reorder_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        ro_vsb.grid(row=0, column=1, sticky="ns")
        ro_hsb.grid(row=1, column=0, sticky="ew")

        action_bar = ctk.CTkFrame(self.tab_reorder, fg_color="transparent")
        action_bar.grid(row=2, column=0, pady=(8, 0), sticky="ew", padx=5)

        ctk.CTkButton(action_bar, text="⊞  Mark Selected as Received", fg_color=ACCENT_GREEN, font=("Segoe UI", 11, "bold"), height=34, command=self._mark_received_from_reorder).pack(side="left", padx=(0, 8))
        ctk.CTkButton(action_bar, text="↻  Refresh List", fg_color="#f3f5f8", text_color=TEXT_DARK, font=("Segoe UI", 11), height=34, command=self._load_reorder_list).pack(side="left")

        self._load_reorder_list()

    def _on_reorder_supplier_changed(self, value=None): self._update_reorder_cost_preview()

    def _on_reorder_sku_changed(self, value=None):
        raw_sku_selection = self.reorder_sku.get().strip()
        
        if not raw_sku_selection or " - " not in raw_sku_selection:
            return

        sku = raw_sku_selection.split(" - ")[0]
        results = []
        
        try:
            import psycopg2
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor()
            
            cur.execute("""
                SELECT s.company_name 
                FROM item_parts ip
                JOIN suppliers s ON s.supplier_id = ip.supplier_id
                WHERE ip.part_number = %s
                ORDER BY ip.cost ASC
            """, (sku,))
            
            results = cur.fetchall()
            conn.close()

        except Exception as e:
            print(f"[DB ERROR] Failed to auto-suggest supplier: {e}")

        # Process results outside the try block
        if results:
            supplier_options = [row[0] for row in results]
            self.reorder_supp.configure(values=supplier_options)
            self.reorder_supp.set(supplier_options[0]) 
        else:
            self.reorder_supp.configure(values=["No suppliers found"])
            self.reorder_supp.set("No suppliers found")
            
        self._update_reorder_cost_preview()

    def _update_reorder_cost_preview(self, *_):
        raw_sku_selection = getattr(self, 'reorder_sku', None)
        raw_supp_selection = getattr(self, 'reorder_supp', None)
        
        if not raw_sku_selection or not raw_supp_selection: return
            
        raw_sku_selection = raw_sku_selection.get().strip()
        supplier_name = raw_supp_selection.get().strip().split(" — ")[0]
        
        unit_cost = 0.0
        
        if raw_sku_selection and " - " in raw_sku_selection and supplier_name: 
            sku = raw_sku_selection.split(" - ")[0]
            try:
                import psycopg2
                conn = psycopg2.connect(**(self.db_config or {}))
                cur = conn.cursor()
                cur.execute("SELECT ip.cost FROM item_parts ip JOIN suppliers s ON s.supplier_id = ip.supplier_id WHERE ip.part_number = %s AND s.company_name = %s", (sku, supplier_name))
                row = cur.fetchone()
                conn.close()
                if row: unit_cost = float(row[0])
            except Exception: pass
            
        # Update Unit Cost Field
        if hasattr(self, '_reorder_unit_cost_var'):
            self._reorder_unit_cost_var.set(f"₱{unit_cost:,.2f}")

        if hasattr(self, '_reorder_total_cost_var'):
            try:
                qty_str = self.reorder_qty.get().strip()
                qty = int(qty_str) if qty_str else 0
                total = unit_cost * qty
                self._reorder_total_cost_var.set(f"₱{total:,.2f}")
            except ValueError:
                self._reorder_total_cost_var.set("₱0.00")

    def _submit_to_reorder_list(self):
        raw_sku_selection = self.reorder_sku.get().strip()
        supplier_name = self.reorder_supp.get().strip()
        qty_str = self.reorder_qty.get().strip()

        if not raw_sku_selection or " - " not in raw_sku_selection or not supplier_name or not qty_str: 
            return messagebox.showwarning("Validation", "Please fill in all fields correctly.")
            
        try: 
            qty = int(qty_str)
            if qty <= 0: raise ValueError
        except ValueError: 
            return messagebox.showwarning("Validation", "Quantity must be a valid positive number.")

        sku = raw_sku_selection.split(" - ")[0]

        try:
            import psycopg2
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor()
            
            cur.execute("SELECT supplier_id FROM suppliers WHERE company_name = %s", (supplier_name,))
            sup_row = cur.fetchone()
            if not sup_row: 
                conn.close()
                return messagebox.showerror("Error", f"Supplier '{supplier_name}' not found.")
            
            cur.execute("INSERT INTO purchase_orders (part_number, supplier_id, quantity_ordered) VALUES (%s, %s, %s)", (sku, sup_row[0], qty))
            cur.execute("UPDATE parts SET on_order = TRUE WHERE part_number = %s", (sku,))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Reorder added: {qty}× {sku} from {supplier_name}.")
            
            self.reorder_qty.delete(0, "end")
            self._load_reorder_list()
            self.refresh_catalog_data() 
            
        except Exception as e: 
            messagebox.showerror("DB Error", f"Failed to add reorder:\n{e}")

    def _load_reorder_list(self):
        if not self.reorder_tree: return
        self.reorder_tree.delete(*self.reorder_tree.get_children())
        try:
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT po.po_number, po.part_number, p.description, s.company_name AS supplier_name,
                       po.quantity_ordered, ip.cost, (po.quantity_ordered * ip.cost) AS total_cost, 
                       CASE WHEN po.received THEN 'Received' ELSE 'Pending' END AS status
                FROM purchase_orders po
                JOIN parts p ON p.part_number = po.part_number
                JOIN suppliers s ON s.supplier_id = po.supplier_id
                JOIN item_parts ip ON ip.part_number = po.part_number AND ip.supplier_id = po.supplier_id
                ORDER BY po.po_number DESC
            """)
            for r in cur.fetchall():
                self.reorder_tree.insert("", "end", values=(r["po_number"], r["part_number"], r["description"], r["supplier_name"], r["quantity_ordered"], f"₱{float(r['cost']):,.2f}", f"₱{float(r['total_cost']):,.2f}", r["status"]))
            conn.close()
        except Exception as e: return messagebox.showerror("DB Error", str(e))

    def _mark_received_from_reorder(self):
        if not self.reorder_tree: return
        selected = self.reorder_tree.selection()
        if not selected: return messagebox.showwarning("Selection", "Please select a reorder entry first.")
        po_id = self.reorder_tree.item(selected[0])["values"][0]
        try:
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor()
            cur.execute("SELECT part_number, quantity_ordered, received FROM purchase_orders WHERE po_number = %s", (po_id,))
            po = cur.fetchone()
            if not po: return messagebox.showerror("Error", "PO not found.")
            if po[2]: return messagebox.showwarning("Warning", "Already received.")
            
            cur.execute("UPDATE parts SET stock_count = stock_count + %s, on_order = FALSE WHERE part_number = %s", (po[1], po[0]))
            cur.execute("UPDATE purchase_orders SET received = TRUE WHERE po_number = %s", (po_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Received", f"PO #{po_id} received. Stock updated.")
            self._load_reorder_list()
            self._load_parts_data()
            self._refresh_parts_table_page()
        except Exception as e: messagebox.showerror("DB Error", str(e))


    # ════════════════════════════════════════════════════════════════════
    # TAB 3: SUPPLIERS
    # ════════════════════════════════════════════════════════════════════
    def _build_suppliers_tab(self):
        self.tab_suppliers.columnconfigure(0, weight=0) 
        self.tab_suppliers.columnconfigure(1, weight=1) 
        self.tab_suppliers.rowconfigure(0, weight=1)

        form = ctk.CTkFrame(self.tab_suppliers, width=320, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER)
        form.grid(row=0, column=0, sticky="nsew", padx=(5, 10), pady=5)
        form.pack_propagate(False)

        ctk.CTkLabel(form, text="Supplier Details", font=FONT_SECTION, text_color=TEXT_DARK).pack(anchor="w", padx=16, pady=(14, 6))

        self._editing_supplier_id = None
        def make_field(label, attr_name, placeholder):
            ctk.CTkLabel(form, text=label, font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(8, 2))
            entry = ctk.CTkEntry(form, placeholder_text=placeholder, width=270, height=34)
            entry.pack(padx=16)
            setattr(self, attr_name, entry)

        make_field("Company Name *", "supp_name", "e.g. Apex Auto Parts")
        make_field("Phone", "supp_phone", "e.g. +63 912 345 6789")
        make_field("Address", "supp_address", "Street, City")
        
        # --- NEW: Link a Part Section ---
        ctk.CTkLabel(form, text="Link to Catalog (Optional)", font=FONT_SECTION, text_color=TEXT_DARK).pack(anchor="w", padx=16, pady=(20, 6))
        
        # Create a tiny invisible frame to hold the Label and the "+ New Part" button side-by-side
        part_lbl_frame = ctk.CTkFrame(form, fg_color="transparent")
        part_lbl_frame.pack(fill="x", padx=16, pady=(0, 2))
        
        ctk.CTkLabel(part_lbl_frame, text="Select Part (Type to search...)", font=FONT_SMALL, text_color=TEXT_MUTED).pack(side="left")
        
        # THE SHORTCUT BUTTON: Calls the exact same modal from the Catalog tab!
        ctk.CTkButton(
            part_lbl_frame, text="+ New Part", width=60, height=20, corner_radius=4,
            fg_color="#e8f5e9", text_color="#27ae60", hover_color="#c8e6c9", font=("Segoe UI", 10, "bold"),
            command=self.handle_add_new_part
        ).pack(side="right")
        
        # Store the full list in a variable so we can filter it safely
        self.all_part_options = [r[1] for r in getattr(self, '_parts_rows', [])] if getattr(self, '_parts_rows', []) else ["No parts available"]
        
        self.supp_part_combo = ctk.CTkComboBox(
            form, 
            values=self.all_part_options, 
            width=270, 
            height=34, 
            fg_color="#f5f7fa", 
            border_color=BORDER,
            dropdown_fg_color="#ffffff",
            dropdown_hover_color="#d6e4f7",
            dropdown_text_color="#2c3e50"
        )
        self.supp_part_combo.set("") 
        self.supp_part_combo.pack(padx=16)

        # --- Autocomplete Search Filter ---
        def filter_dropdown_options(event):
            if event.keysym in ("Up", "Down", "Return"): return
            typed_text = self.supp_part_combo.get().lower()
            if typed_text == "":
                self.supp_part_combo.configure(values=self.all_part_options)
            else:
                matches = [p for p in self.all_part_options if typed_text in p.lower()]
                self.supp_part_combo.configure(values=matches if matches else ["No match found"])

        self.supp_part_combo.bind("<KeyRelease>", filter_dropdown_options)
        # ---------------------------------------------
        
        ctk.CTkLabel(form, text="Unit Cost from this Supplier (₱)", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(8, 2))
        self.supp_cost_entry = ctk.CTkEntry(form, placeholder_text="e.g. 50.00", width=270, height=34)
        self.supp_cost_entry.pack(padx=16)

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(16, 8))
        
        self.save_supp_btn = ctk.CTkButton(btn_row, text="💾  Save Supplier", fg_color=BRAND_BLUE, font=("Segoe UI", 11, "bold"), height=34, command=self._save_supplier)
        self.save_supp_btn.pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="✕  Clear", fg_color="#f3f5f8", text_color=TEXT_DARK, font=("Segoe UI", 11), height=34, command=self._clear_supplier_form).pack(side="left")

        right = ctk.CTkFrame(self.tab_suppliers, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER)
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 5), pady=5)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        # --- Supplier List Header with Search Bar ---
        supp_hdr = ctk.CTkFrame(right, fg_color="transparent")
        supp_hdr.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        
        ctk.CTkLabel(supp_hdr, text="Supplier List", font=FONT_SECTION, text_color=TEXT_DARK).pack(side="left")
        
        ctk.CTkButton(
            supp_hdr, text="↻", width=32, height=32, corner_radius=6, 
            fg_color="#f3f5f8", hover_color="#e0e4eb", text_color=TEXT_DARK, 
            command=self._load_supplier_list
        ).pack(side="right")

        self._supp_search_var = tk.StringVar()
        self._supp_search_var.trace_add("write", lambda *_: self._apply_supplier_search())
        
        ctk.CTkEntry(
            supp_hdr, textvariable=self._supp_search_var, 
            placeholder_text="Search by name, phone, or address...", 
            height=32, fg_color="#f5f7fa", border_color=BORDER
        ).pack(side="right", fill="x", expand=True, padx=(15, 10))
        # -------------------------------------------------
        
        supp_cols = ("ID", "Company Name", "Phone", "Address")
        self.supp_tree = ttk.Treeview(right, columns=supp_cols, show="headings", style="Parts.Treeview")
        for col in supp_cols: self.supp_tree.heading(col, text=col)
        self.supp_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 4))
        self.supp_tree.bind("<Double-1>", self._on_supplier_double_click)

        action_frame = ctk.CTkFrame(right, fg_color="transparent")
        action_frame.grid(row=3, column=0, pady=(4, 10), padx=10, sticky="ew")
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)

        ctk.CTkButton(
            action_frame, text="📦 View Supplied Parts", fg_color=BRAND_BLUE, hover_color="#2980b9",
            font=("Segoe UI", 11, "bold"), height=32, command=self._show_supplier_parts_modal
        ).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        ctk.CTkButton(
            action_frame, text="🗑 Delete Selected", fg_color=ACCENT_RED, hover_color="#c0392b",
            font=("Segoe UI", 11, "bold"), height=32, command=self._delete_supplier
        ).grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        self._load_supplier_list()

    def _save_supplier(self):
        name = getattr(self, "supp_name").get().strip()
        if not name: return messagebox.showwarning("Validation", "Company Name is required.")
        selected_part_desc = self.supp_part_combo.get().strip()
        cost_str = self.supp_cost_entry.get().strip()
        
        try:
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor()
            
            supplier_id = self._editing_supplier_id
            if supplier_id:
                cur.execute(
                    "UPDATE suppliers SET company_name=%s, phone_number=%s, address=%s WHERE supplier_id=%s", 
                    (name, getattr(self, "supp_phone").get().strip(), getattr(self, "supp_address").get().strip(), supplier_id)
                )
            else:
                cur.execute(
                    "INSERT INTO suppliers (company_name, phone_number, address) VALUES (%s, %s, %s) RETURNING supplier_id", 
                    (name, getattr(self, "supp_phone").get().strip(), getattr(self, "supp_address").get().strip())
                )
                supplier_id = cur.fetchone()[0]
            if selected_part_desc and cost_str:
                try:
                    cost_val = float(cost_str)
                except ValueError:
                    messagebox.showwarning("Validation", "Cost must be a valid number. Supplier saved, but part link failed.")
                    conn.commit()
                    return
                part_number = next((r[0] for r in self._parts_rows if r[1] == selected_part_desc), None)
                if not part_number:
                    messagebox.showwarning("Validation", "Part must exist in the Catalog first! Supplier saved, but part link failed.")
                else:
                    cur.execute("""
                        INSERT INTO item_parts (part_number, supplier_id, cost) 
                        VALUES (%s, %s, %s)
                        ON CONFLICT (part_number, supplier_id) 
                        DO UPDATE SET cost = EXCLUDED.cost
                    """, (part_number, supplier_id, cost_val))
            conn.commit()
            conn.close()
            self._clear_supplier_form()
            self._load_supplier_list()
            messagebox.showinfo("Success", "Supplier info saved!")
        except Exception as e: 
            messagebox.showerror("DB Error", str(e))

    def _clear_supplier_form(self):
        self._editing_supplier_id = None
        self.save_supp_btn.configure(text="💾  Save Supplier")
        for attr in ("supp_name", "supp_phone", "supp_address"): getattr(self, attr).delete(0, "end")
        self.supp_part_combo.set("")
        self.supp_cost_entry.delete(0, "end")

    def _on_supplier_double_click(self, event):
        if not self.supp_tree: return 
        selected = self.supp_tree.selection()
        if not selected: return
        vals = self.supp_tree.item(selected[0])["values"]
        self._editing_supplier_id = vals[0]
        for attr, val in zip(("supp_name", "supp_phone", "supp_address"), vals[1:]):
            getattr(self, attr).delete(0, "end")
            getattr(self, attr).insert(0, val or "")
        self.save_supp_btn.configure(text="✏️  Update Supplier")

    def _delete_supplier(self):
        if not self.supp_tree: return 
        selected = self.supp_tree.selection()
        if not selected: return messagebox.showwarning("Selection", "Select a supplier to delete.")
        if not messagebox.askyesno("Confirm", "Delete supplier?"): return
        try:
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor()
            cur.execute("DELETE FROM suppliers WHERE supplier_id = %s", (self.supp_tree.item(selected[0])["values"][0],))
            conn.commit()
            conn.close()
            self._load_supplier_list()
        except Exception as e: messagebox.showerror("DB Error", str(e))

    def _load_supplier_list(self):
        """Fetches from DB once and stores in memory for fast searching."""
        if not getattr(self, 'supp_tree', None): return 
        
        try:
            import psycopg2
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor()
            cur.execute("SELECT supplier_id, company_name, phone_number, address FROM suppliers ORDER BY company_name")
            
            # Store full list in memory
            self._supplier_rows = cur.fetchall() 
            self._filtered_supplier_rows = list(self._supplier_rows)
            
            conn.close()
            self._refresh_supplier_table()
        except Exception as e: 
            import tkinter.messagebox as messagebox
            messagebox.showerror("DB Error", str(e))

    def _apply_supplier_search(self):
        """Filters the stored list instantly as the user types."""
        query = self._supp_search_var.get().lower()
        
        if not query:
            self._filtered_supplier_rows = list(getattr(self, '_supplier_rows', []))
        else:
            self._filtered_supplier_rows = []
            for r in getattr(self, '_supplier_rows', []):
                # Search across Company Name, Phone, and Address
                if (query in str(r[1] or "").lower() or 
                    query in str(r[2] or "").lower() or 
                    query in str(r[3] or "").lower()):
                    self._filtered_supplier_rows.append(r)
                    
        self._refresh_supplier_table()

    def _refresh_supplier_table(self):
        if self.supp_tree is None: 
            return
        
        self.supp_tree.delete(*self.supp_tree.get_children())
        for r in getattr(self, '_filtered_supplier_rows', []): 
            self.supp_tree.insert("", "end", values=r)
    
    def _show_supplier_parts_modal(self):
        if not self.supp_tree: return
        selected = self.supp_tree.selection()
        
        if not selected:
            messagebox.showwarning("Selection Required", "Please click on a supplier from the list first.")
            return

        # Get the supplier ID and Name from the selected row
        vals = self.supp_tree.item(selected[0])["values"]
        supp_id = vals[0]
        supp_name = vals[1]

        # Create the Modal Window
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Catalog: {supp_name}")
        dialog.geometry("550x400")
        dialog.grab_set() # Forces user to close this before clicking the main app
        dialog.focus()

        ctk.CTkLabel(
            dialog, text=f"Parts Supplied by: {supp_name}", 
            font=("Segoe UI", 16, "bold"), text_color=TEXT_DARK
        ).pack(pady=(20, 10), padx=20, anchor="w")

        # Container for the table
        container = ctk.CTkFrame(dialog, fg_color=CARD_BG, corner_radius=8, border_width=1, border_color=BORDER)
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Query the database for this specific supplier's items
        import psycopg2
        try:
            conn = psycopg2.connect(**(self.db_config or {}))
            cur = conn.cursor()
            
            # Join item_parts to parts to get the description and cost
            cur.execute("""
                SELECT p.part_number, p.description, ip.cost 
                FROM item_parts ip
                JOIN parts p ON p.part_number = ip.part_number
                WHERE ip.supplier_id = %s
                ORDER BY p.description ASC
            """, (supp_id,))
            
            rows = cur.fetchall()
            conn.close()

            # If they don't supply anything yet
            if not rows:
                ctk.CTkLabel(container, text="No parts have been linked to this supplier yet.", text_color=TEXT_MUTED).pack(pady=50)
                return

            # Build the mini-table
            cols = ("SKU", "Part Description", "Unit Cost")
            tree = ttk.Treeview(container, columns=cols, show="headings", style="Parts.Treeview")
            
            # Add scrollbar
            vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)

            # Format columns
            tree.heading("SKU", text="SKU")
            tree.column("SKU", width=100, anchor="w")
            tree.heading("Part Description", text="Part Description")
            tree.column("Part Description", width=250, anchor="w")
            tree.heading("Unit Cost", text="Unit Cost")
            tree.column("Unit Cost", width=100, anchor="w")

            tree.pack(side="left", fill="both", expand=True, padx=(2, 0), pady=2)
            vsb.pack(side="right", fill="y", pady=2)

            # Insert Data
            for r in rows:
                tree.insert("", "end", values=(r[0], r[1], f"₱{float(r[2]):,.2f}"))

        except Exception as e:
            ctk.CTkLabel(container, text=f"Database Error: {e}", text_color=ACCENT_RED).pack(pady=50)