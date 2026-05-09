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

        for (sku, desc, cat, stock, low_threshold, price_str, unit, actions) in self.parts_data:
            try:
                # Handle formatted currency strings or raw floats
                if isinstance(price_str, str):
                    price = float(price_str.replace("$", "").replace("₱", "").replace(",", ""))
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
            card = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER, height=108)
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
        
        # --- RBAC: Fetch role from the secure session ---
        session = getattr(self.controller, 'session', None)
        self.role = getattr(session, 'role', None) or "Manager"

        self._right_panel_visible = True
        self._current_page = 1
        self._page_size = 10
        self._parts_rows = []
        self._parts_tree = None

        self._load_parts_data()

        # Fill frame completely
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)

        # --- LEFT PANEL: Parts Catalog ---
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.left_panel.columnconfigure(0, weight=1)
        self.left_panel.rowconfigure(1, weight=0) # Keeps header tight

        # KPI Bar
        self.kpi = InventoryKPIBar(self.left_panel, self._parts_rows)
        self.kpi.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        self._build_catalog_section()

        # --- RIGHT PANEL: Restock Sidebar ---
        self.right_panel = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0, border_width=0)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self._build_place_order_card()
        self._build_receive_restock_card()

    def _load_parts_data(self):
        """Loads data from the DB via QueryManager. Falls back to mock data if not connected."""
        if hasattr(self.controller, 'query_manager'):
            try:
                # To be integrated with QD-Sec3 logic or general catalog query
                # result = self.controller.query_manager.run_query("CATALOG_ALL")
                # self._parts_rows = [tuple(row.values()) for row in result.rows]
                pass
            except Exception as e:
                print(f"DB Error: {e}")
        
        # Mock Data Fallback
        if not self._parts_rows:
            seeds = [
                ("BIC Pens Blue (12pk)", "Pens", 120, 20, "₱150.00", "Pack"),
                ("HP LaserJet Toner Black", "Toners", 485, 50, "₱4500.00", "Unit"),
                ("Paper Mate Eraser Pink (Lg)", "Pens", 75, 50, "₱25.00", "Unit"),
                ("Bond Paper A4", "Paper", 0, 50, "₱250.00", "Ream"),
            ]
            rows = []
            for idx in range(102):
                desc, cat, stock, low, price, unit = seeds[idx % len(seeds)]
                sku = str(10000 + idx)
                rows.append((sku, desc, cat, stock, low, price, unit, "✏️ Edit"))
            self._parts_rows = rows

    # ════════════════════════════════════════════════════════════════════
    # LEFT PANEL: Catalog header + search + table
    # ════════════════════════════════════════════════════════════════════
    def _build_catalog_section(self):
        hdr = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        hdr.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        hdr.columnconfigure(0, weight=1)

        ctk.CTkLabel(hdr, text=f"Parts Catalog ({len(self._parts_rows)} items)", font=FONT_TITLE, text_color=TEXT_DARK).grid(row=0, column=0, sticky="w")

        actions = ctk.CTkFrame(hdr, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e")

        # --- RBAC: Add New Part Masking ---
        self.add_btn = ctk.CTkButton(
            actions, text="+ Add New Part", width=130, height=34, corner_radius=6, 
            fg_color=BRAND_BLUE, hover_color="#2980b9", font=("Segoe UI", 12, "bold"),
            command=self.handle_add_new_part
        )
        self.add_btn.pack(side="left", padx=(0, 8))
        
        if self.role != "Manager":
            self.add_btn.configure(state="disabled", fg_color="#bdc3c7", text_color="#7f8c8d")

        self.toggle_btn = ctk.CTkButton(actions, text="◀", width=34, height=34, corner_radius=8, fg_color="#2b9430", hover_color="#1c7421", text_color="#ffffff", font=("Segoe UI", 14, "bold"), command=self.toggle_side_panels)
        self.toggle_btn.pack(side="left")

        # Search + filter bar
        search_bar = ctk.CTkFrame(self.left_panel, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER)
        search_bar.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        inner = ctk.CTkFrame(search_bar, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        left_tools = ctk.CTkFrame(inner, fg_color="transparent")
        left_tools.pack(side="left", fill="x", expand=True)

        right_tools = ctk.CTkFrame(inner, fg_color="transparent")
        right_tools.pack(side="right")

        ctk.CTkLabel(left_tools, text="🔍", font=("Segoe UI", 14)).pack(side="left", padx=(0, 8))
        ctk.CTkEntry(left_tools, placeholder_text="Search…", width=240, height=34, corner_radius=6, fg_color="#f5f7fa", text_color=TEXT_DARK, border_color=BORDER, font=FONT_BODY).pack(side="left", padx=(0, 20))
        ctk.CTkLabel(left_tools, text="Filter:", font=FONT_BODY, text_color=TEXT_MUTED).pack(side="left", padx=(0, 8))
        ctk.CTkOptionMenu(left_tools, values=["All", "In Stock", "Low Stock", "Out of Stock"], width=130, height=34, corner_radius=6, fg_color="#f5f7fa", button_color=BRAND_BLUE, text_color=TEXT_DARK, font=FONT_BODY).pack(side="left")

        self.prev_page_btn = ctk.CTkButton(right_tools, text="‹", width=30, height=28, corner_radius=6, fg_color="#f3f5f8", hover_color="#e8ecf2", text_color="#9ca3af", font=("Segoe UI", 13, "bold"), command=self._go_prev_page)
        self.prev_page_btn.pack(side="left", padx=(0, 6))

        self.page_label = ctk.CTkLabel(right_tools, text="1", width=42, height=28, corner_radius=6, fg_color="#ffffff", text_color=TEXT_DARK, font=("Segoe UI", 12, "bold"))
        self.page_label.pack(side="left", padx=(0, 6))

        self.page_count_label = ctk.CTkLabel(right_tools, text="of 1", text_color="#374151", font=("Segoe UI", 11))
        self.page_count_label.pack(side="left", padx=(0, 6))

        self.next_page_btn = ctk.CTkButton(right_tools, text="›", width=30, height=28, corner_radius=6, fg_color="#f3f5f8", hover_color="#e8ecf2", text_color="#9ca3af", font=("Segoe UI", 13, "bold"), command=self._go_next_page)
        self.next_page_btn.pack(side="left")

        # Table container
        tbl_frame = ctk.CTkFrame(self.left_panel, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER)
        tbl_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 0))
        self.left_panel.rowconfigure(3, weight=1)

        self._build_parts_table(tbl_frame)

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

        cols = ("SKU", "Part Description", "Category", "Stock Count", "Low Stock Threshold", "Selling Price", "Unit", "Actions")
        widths = (80, 220, 100, 80, 130, 120, 60, 80)

        tree = ttk.Treeview(container, columns=cols, show="headings", style="Parts.Treeview", yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=10)
        vsb.configure(command=tree.yview)
        hsb.configure(command=tree.xview)

        for col, width in zip(cols, widths):
            tree.column(col, width=width, anchor="w")
            tree.heading(col, text=col)

        self._parts_tree = tree
        self._current_page = 1

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

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

        self._create_form_field(card, "Part Name/SKU", is_combo=True)

        qty_supplier = ctk.CTkFrame(card, fg_color="transparent")
        qty_supplier.pack(fill="x", padx=10, pady=(2, 3))
        qty_supplier.columnconfigure(0, weight=1)
        qty_supplier.columnconfigure(1, weight=1)

        qty_frame = ctk.CTkFrame(qty_supplier, fg_color="transparent")
        qty_frame.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(qty_frame, text="Quantity", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w")
        ctk.CTkEntry(qty_frame, height=28, fg_color="#f5f7fa", placeholder_text="500").pack(fill="x", pady=(2, 0))

        supp_frame = ctk.CTkFrame(qty_supplier, fg_color="transparent")
        supp_frame.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(supp_frame, text="Supplier", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w")
        ctk.CTkComboBox(supp_frame, values=["Apex Office Solutions", "Office Mart"], height=28, fg_color="#f5f7fa").pack(fill="x", pady=(2, 0))

        price_info = ctk.CTkFrame(card, fg_color="#f5f7fa", corner_radius=6)
        price_info.pack(fill="x", padx=10, pady=(6, 6))
        price_info.grid_columnconfigure(0, weight=1)
        price_info.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(price_info, text="Est. Cost", font=("Segoe UI", 9, "bold"), text_color=TEXT_DARK).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(price_info, text="₱2,745.00", font=("Segoe UI", 9, "bold"), text_color=TEXT_DARK).grid(row=0, column=1, sticky="e", padx=10, pady=5)

        # --- RBAC: Submit PO Masking ---
        self.submit_po_btn = ctk.CTkButton(
            card, text="✈ Submit PO", height=32, corner_radius=6, 
            fg_color=BRAND_BLUE, hover_color="#2980b9", font=("Segoe UI", 11, "bold"),
            command=self.handle_submit_po  # <-- ADD THIS LINE
        )
        self.submit_po_btn.pack(fill="x", padx=10, pady=(0, 8))

        if self.role != "Manager":
            self.submit_po_btn.configure(state="disabled", fg_color="#bdc3c7", text_color="#7f8c8d")

    def _build_receive_restock_card(self):
        card = self._create_card_container(self.right_panel)
        card.pack(fill="x", pady=(0, 2))

        ctk.CTkLabel(card, text="Receive Restock", font=FONT_SECTION, text_color=TEXT_DARK).pack(anchor="w", padx=10, pady=(8, 4))

        search_row = ctk.CTkFrame(card, fg_color="#f5f7fa", corner_radius=6)
        search_row.pack(fill="x", padx=10, pady=(0, 6))
        search_row.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(search_row, placeholder_text="PO Number", height=28, fg_color="#f5f7fa", border_color=BORDER).grid(row=0, column=0, sticky="ew", padx=(0, 2), pady=4)
        ctk.CTkLabel(search_row, text="🔍", font=("Segoe UI", 12), text_color=TEXT_MUTED, width=24).grid(row=0, column=1, padx=(0, 6))

        info_bg = ctk.CTkFrame(card, fg_color="#f8f9fa", corner_radius=6)
        info_bg.pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkLabel(info_bg, text="PO-2023-112", font=("Segoe UI", 11, "bold"), text_color=TEXT_DARK).pack(anchor="w", padx=8, pady=(4, 0))
        ctk.CTkLabel(info_bg, text="Supplier", font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w", padx=8, pady=(3, 0))
        ctk.CTkLabel(info_bg, text="Apex", font=("Segoe UI", 11), text_color=TEXT_DARK).pack(anchor="w", padx=8, pady=(0, 2))

        summary_grid = ctk.CTkFrame(info_bg, fg_color="transparent")
        summary_grid.pack(fill="x", padx=8, pady=(3, 4))
        summary_grid.grid_columnconfigure((0, 1, 2), weight=1)

        for col, (label, value) in enumerate([("Items", "4"), ("Qty", "500"), ("Total", "₱2,745.00")]):
            ctk.CTkLabel(summary_grid, text=label, font=FONT_SMALL, text_color=TEXT_MUTED).grid(row=0, column=col, sticky="w")
            ctk.CTkLabel(summary_grid, text=value, font=("Segoe UI", 10), text_color=TEXT_DARK).grid(row=1, column=col, sticky="w", pady=(1, 0))

        # --- RBAC: Mark Received Masking ---
        self.mark_rcvd_btn = ctk.CTkButton(
            card, text="⊞  Mark Received", height=32, corner_radius=6, 
            fg_color="#ff3d1f", hover_color="#e33317", text_color="#ffffff", font=("Segoe UI", 11, "bold"),
            command=self.handle_mark_received
        )
        self.mark_rcvd_btn.pack(fill="x", padx=10, pady=(0, 8))

        if self.role != "Manager":
            self.mark_rcvd_btn.configure(state="disabled", fg_color="#bdc3c7", text_color="#7f8c8d")

    # ════════════════════════════════════════════════════════════════════
    # Helpers
    # ════════════════════════════════════════════════════════════════════
    def _create_card_container(self, parent):
        return ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER)

    def _create_form_field(self, parent, label, is_combo=False):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=(0, 5))
        ctk.CTkLabel(frame, text=label, font=FONT_SMALL, text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 3))
        if is_combo:
            ctk.CTkComboBox(frame, values=["BIC Pens Blue (12pk)", "HP LaserJet Toner"], height=28, fg_color="#f5f7fa", border_color=BORDER).pack(fill="x")
        else:
            ctk.CTkEntry(frame, height=28, fg_color="#f5f7fa", border_color=BORDER).pack(fill="x")

    def _set_toggle_state(self, visible: bool):
        if hasattr(self, "toggle_btn") and self.toggle_btn is not None:
            if visible:
                self.toggle_btn.configure(text="◀", fg_color="#2b9430")
            else:
                self.toggle_btn.configure(text="▶", fg_color="#27ae60")

    def _refresh_parts_table_page(self):
        if self._parts_tree is None:
            return

        self._parts_tree.delete(*self._parts_tree.get_children())
        total_rows = len(self._parts_rows)
        total_pages = max(1, (total_rows + self._page_size - 1) // self._page_size)

        if self._current_page > total_pages:
            self._current_page = total_pages
        if self._current_page < 1:
            self._current_page = 1

        start = (self._current_page - 1) * self._page_size
        end = start + self._page_size

        for row in self._parts_rows[start:end]:
            self._parts_tree.insert("", "end", values=row)

        self._update_pager_state(total_pages)

    def _update_pager_state(self, total_pages: int):
        if hasattr(self, "page_label"):
            self.page_label.configure(text=str(self._current_page))
        if hasattr(self, "page_count_label"):
            self.page_count_label.configure(text=f"of {total_pages}")

        prev_enabled = self._current_page > 1
        next_enabled = self._current_page < total_pages

        if hasattr(self, "prev_page_btn"):
            self.prev_page_btn.configure(state="normal" if prev_enabled else "disabled", text_color="#6b7280" if prev_enabled else "#c4c9d1")
        if hasattr(self, "next_page_btn"):
            self.next_page_btn.configure(state="normal" if next_enabled else "disabled", text_color="#6b7280" if next_enabled else "#c4c9d1")

    def _go_prev_page(self):
        if self._current_page > 1:
            self._current_page -= 1
            self._refresh_parts_table_page()

    def _go_next_page(self):
        total_pages = max(1, (len(self._parts_rows) + self._page_size - 1) // self._page_size)
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
    
    # ════════════════════════════════════════════════════════════════════
    # SECURE ACTION HANDLERS (Phase 3 Integration)
    # ════════════════════════════════════════════════════════════════════

    def handle_add_new_part(self):
        """Action for the '+ Add New Part' button."""
        try:
            # Here you would typically open a modal/dialog, then call the backend:
            # self.controller.query_manager.add_part(data)
            messagebox.showinfo("Inventory Management", "Opening 'Add New Part' dialog...")
            
        except PermissionError as e:
            # Caught by the @require_role decorator in the backend!
            messagebox.showerror("Security Override", str(e))
        except Exception as e:
            messagebox.showerror("System Error", f"An unexpected error occurred: {e}")

    def handle_submit_po(self):
        """Action for the 'Submit PO' button."""
        try:
            # In a full implementation, you'd fetch the combo box values here
            # part = self.po_part_combo.get()
            # qty = self.po_qty_entry.get()
            
            # Simulated Backend Call (this would trigger the decorator in query_manager.py)
            # self.controller.query_manager.create_purchase_order(part, qty, ...)
            
            messagebox.showinfo("Success", "Purchase Order submitted successfully.")
            
        except PermissionError as e:
            messagebox.showerror("Security Override", str(e))
        except Exception as e:
            messagebox.showerror("System Error", f"An unexpected error occurred: {e}")

    def handle_mark_received(self):
        """Action for the 'Mark Received' button."""
        try:
            # Simulate fetching the PO number from the entry field
            # po_number = self.recv_search_entry.get()
            
            # Simulated Backend Call
            # self.controller.query_manager.receive_restock(po_number)
            
            messagebox.showinfo("Success", "Stock updated and PO marked as received.")
            self._refresh_parts_table_page() # Refresh the table to show new stock counts
            
        except PermissionError as e:
            messagebox.showerror("Security Override", str(e))
        except Exception as e:
            messagebox.showerror("System Error", f"An unexpected error occurred: {e}")