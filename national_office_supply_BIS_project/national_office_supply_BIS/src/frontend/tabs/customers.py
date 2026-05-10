import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import psycopg2
from decimal import Decimal, InvalidOperation
from frontend.modular.customer_search_bar import CustomerSearchBar
from frontend.modular.customer_table import CustomerTable


class CustomersView(ctk.CTkFrame):
    def __init__(self, parent, controller, db_config):
        super().__init__(parent, fg_color="#f8f9fa")
        self.controller = controller
        self.db_config = db_config
        self.base_rows = []
        self.active_filter = "all"
        self.filter_buttons = {}
        self._right_panel_visible = True  # track panel state for toggle button sync

        # Layout: 2 columns (table | right cards), top row for compact actions
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=0)  # search bar row
        self.grid_rowconfigure(1, weight=0)  # small filter chips row
        self.grid_rowconfigure(2, weight=1)  # main table row

        # -----------------------
        # SEARCH BAR (top left)
        # -----------------------
        self.search_var = ctk.StringVar()
        # Top row: search bar, filter chips (or filter button), and action icons
        self.top_row = ctk.CTkFrame(self, fg_color="transparent")
        self.top_row.grid(row=0, column=0, sticky="ew", padx=20, pady=(12, 8))
        self.top_row.grid_columnconfigure(0, weight=1)

        self.search_bar = CustomerSearchBar(
            self.top_row,
            search_var=self.search_var,
            on_search=self.search_customers,
            on_clear=self.clear_search,
            on_toggle_panels=self.toggle_side_panels,
            on_refresh=self.load_customers,
            on_edit=self.edit_customer,
        )
        self.search_bar.pack(side="left", fill="x", expand=True)

        # Container for chips or the compact filter button (placed under search)
        self.chips_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.chips_frame.grid(row=1, column=0, sticky="w", padx=24, pady=(4, 6))
        self.filter_popup = None
        self.filter_button = None
        self._build_filter_chips()

        # --- LEFT: Customer Table (below search bar) ---
        self.table_frame = CustomerTable(self)
        self.table_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.tree = self.table_frame.tree

        # Bind double-click to edit
        self.tree.bind("<Double-1>", self._on_row_double_click)
        self.tree.bind("<Button-3>", self._show_row_menu)

        self.row_menu = tk.Menu(self, tearoff=0)
        self.row_menu.add_command(label="Edit Customer", command=self.edit_customer)
        self.row_menu.add_command(
            label="Receive Payment", command=self.receive_payment_for_selected
        )
        self.row_menu.add_command(
            label="View Payment Ledger", command=self.view_ledger_for_selected
        )

        # --- RIGHT: container for Add Customer (top) and Payment (bottom) ---
        self.right_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=12,
            border_width=0,
        )
        self.right_frame.grid(
            row=2, column=1, sticky="nsew", padx=(0, 20), pady=(0, 20)
        )

        # Sync the search bar toggle button with the right panel's initial visibility
        try:
            self.search_bar.set_toggle_state(True)
        except Exception:
            pass

        # Make right_frame use vertical stacking
        self.right_frame.grid_rowconfigure(0, weight=0)  # add panel
        self.right_frame.grid_rowconfigure(1, weight=0)  # payment panel
        self.right_frame.grid_rowconfigure(2, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        # --- Add Customer Panel (top of right_frame) ---
        self.add_shadow = ctk.CTkFrame(
            self.right_frame,
            fg_color="#dfe5ec",
            corner_radius=8,
            border_width=0,
        )
        self.add_shadow.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        self.add_frame = ctk.CTkFrame(
            self.add_shadow,
            fg_color="#ffffff",
            corner_radius=8,
            border_width=1,
            border_color="#e5e7eb",
        )
        self.add_frame.pack(fill="both", expand=True, padx=1, pady=1)

        ctk.CTkLabel(
            self.add_frame,
            text="Add Customer",
            font=("Segoe UI", 14, "bold"),
            text_color="#2c3e50",
        ).pack(pady=(12, 8))

        self.company_entry = ctk.CTkEntry(
            self.add_frame, placeholder_text="Company Name"
        )
        self.company_entry.pack(fill="x", padx=12, pady=4)
        self._style_input(self.company_entry)

        self.contact_entry = ctk.CTkEntry(
            self.add_frame, placeholder_text="Contact Name"
        )
        self.contact_entry.pack(fill="x", padx=12, pady=4)
        self._style_input(self.contact_entry)

        self.phone_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Phone Number")
        self.phone_entry.pack(fill="x", padx=12, pady=4)
        self._style_input(self.phone_entry)

        self.address_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Address")
        self.address_entry.pack(fill="x", padx=12, pady=4)
        self._style_input(self.address_entry)

        self.balance_entry = ctk.CTkEntry(
            self.add_frame, placeholder_text="Current Balance (default: 0.00)"
        )
        self.balance_entry.pack(fill="x", padx=12, pady=4)
        self._style_input(self.balance_entry)

        add_btn = ctk.CTkButton(
            self.add_frame,
            text="Add Customer",
            fg_color="#27ae60",
            hover_color="#1e8449",
            command=self.add_customer,
        )
        add_btn.pack(pady=10)

        # --- Payment Panel (below add_frame) ---
        self.pay_shadow = ctk.CTkFrame(
            self.right_frame,
            fg_color="#dfe5ec",
            corner_radius=8,
            border_width=0,
        )
        self.pay_shadow.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 10))

        self.payment_frame = ctk.CTkFrame(
            self.pay_shadow,
            fg_color="#ffffff",
            corner_radius=8,
            border_width=1,
            border_color="#e5e7eb",
        )
        self.payment_frame.pack(fill="both", expand=True, padx=1, pady=1)

        ctk.CTkLabel(
            self.payment_frame,
            text="Receive Payment",
            font=("Segoe UI", 14, "bold"),
            text_color="#2c3e50",
        ).pack(pady=(12, 8))

        # Scrollable customer dropdown (replaces CTkComboBox for better scroll support)
        self._customer_values = []
        self._dropdown_popup = None

        self._cust_dd_frame = ctk.CTkFrame(
            self.payment_frame,
            fg_color="#f8f9fa",
            border_width=1,
            border_color="#d0d7de",
            corner_radius=8,
            height=34,
        )
        self._cust_dd_frame.pack(fill="x", padx=12, pady=6)
        self._cust_dd_frame.pack_propagate(False)

        self._cust_dd_var = tk.StringVar(value="Select customer...")
        self._cust_dd_entry = ctk.CTkEntry(
            self._cust_dd_frame,
            textvariable=self._cust_dd_var,
            fg_color="transparent",
            border_width=0,
            height=34,
            text_color="#1c1c1c",
            placeholder_text_color="#7f8c8d",
        )
        self._cust_dd_entry.pack(side="left", fill="both", expand=True, padx=(6, 0))

        self._cust_dd_btn = ctk.CTkButton(
            self._cust_dd_frame,
            text="▾",
            width=28,
            height=28,
            fg_color="#abb2b9",
            hover_color="#566573",
            corner_radius=6,
            command=self._toggle_customer_dropdown,
        )
        self._cust_dd_btn.pack(side="right", padx=4, pady=3)

        self._cust_dd_entry.bind("<Button-1>", lambda e: self._toggle_customer_dropdown())
        self._cust_dd_entry.bind("<FocusIn>", lambda e: self._cust_dd_frame.configure(border_color="#3498db"))
        self._cust_dd_entry.bind("<FocusOut>", lambda e: self._cust_dd_frame.configure(border_color="#d0d7de"))
        self._cust_dd_entry.bind("<KeyRelease>", self._filter_customer_dropdown)

        # Shim so existing code using self.customer_dropdown still works
        self.customer_dropdown = self._ScrollableDropdownShim(
            get_fn=lambda: self._cust_dd_var.get(),
            set_fn=self._set_customer_dropdown,
            values_fn=lambda: self._customer_values,
            configure_fn=self._configure_customer_dropdown,
            cget_fn=self._cget_customer_dropdown,
        )

        self.amount_entry = ctk.CTkEntry(
            self.payment_frame, placeholder_text="Enter amount"
        )
        self.amount_entry.pack(fill="x", padx=12, pady=6)
        self._style_input(self.amount_entry)

        # FIX: payment method values must match DB CHECK constraint: 'check', 'cash', 'transfer'
        self.method_dropdown = ctk.CTkComboBox(
            self.payment_frame, values=["cash", "check", "transfer"]
        )
        self.method_dropdown.pack(fill="x", padx=12, pady=6)
        self._style_input(self.method_dropdown)

        self.note_entry = ctk.CTkEntry(
            self.payment_frame,
            placeholder_text="Optional note / OR number",
        )
        self.note_entry.pack(fill="x", padx=12, pady=(0, 6))
        self._style_input(self.note_entry)

        process_btn = ctk.CTkButton(
            self.payment_frame,
            text="Process Payment",
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self.process_payment,
        )
        process_btn.pack(fill="x", padx=12, pady=12)

        # Load initial data
        self.load_customers()

    def _style_input(self, widget):
        common_kwargs = dict(
            fg_color="#f8f9fa",
            border_width=1,
            border_color="#d0d7de",
            corner_radius=8,
            height=34,
            text_color="#1c1c1c",
            placeholder_text_color="#7f8c8d",
        )

        if isinstance(widget, ctk.CTkComboBox):
            widget.configure(
                fg_color=common_kwargs["fg_color"],
                border_width=common_kwargs["border_width"],
                border_color=common_kwargs["border_color"],
                corner_radius=common_kwargs["corner_radius"],
                height=common_kwargs["height"],
            )
            widget.configure(button_color="#abb2b9", button_hover_color="#566573")
        else:
            widget.configure(**common_kwargs)
        widget.bind(
            "<FocusIn>", lambda _e, w=widget: w.configure(border_color="#3498db")
        )
        widget.bind(
            "<FocusOut>", lambda _e, w=widget: w.configure(border_color="#d0d7de")
        )

    # -----------------------------------------------
    # Scrollable customer dropdown helpers
    # -----------------------------------------------
    class _ScrollableDropdownShim:
        """Thin shim so existing code that calls customer_dropdown.set/get/cget/configure still works."""
        def __init__(self, get_fn, set_fn, values_fn, configure_fn, cget_fn):
            self._get = get_fn
            self._set = set_fn
            self._values = values_fn
            self._configure = configure_fn
            self._cget = cget_fn

        def get(self):
            return self._get()

        def set(self, value):
            self._set(value)

        def configure(self, **kwargs):
            self._configure(**kwargs)

        def cget(self, key):
            return self._cget(key)

    def _configure_customer_dropdown(self, **kwargs):
        if "values" in kwargs:
            self._customer_values = list(kwargs["values"])

    def _cget_customer_dropdown(self, key):
        if key == "values":
            return list(self._customer_values)
        return None

    def _set_customer_dropdown(self, value):
        self._cust_dd_var.set(value)

    def _toggle_customer_dropdown(self):
        if self._dropdown_popup and self._dropdown_popup.winfo_exists():
            self._dropdown_popup.destroy()
            self._dropdown_popup = None
            return
        self._open_customer_dropdown(self._customer_values)

    def _filter_customer_dropdown(self, event=None):
        query = self._cust_dd_var.get().lower()
        filtered = [v for v in self._customer_values if query in v.lower()]
        if self._dropdown_popup and self._dropdown_popup.winfo_exists():
            self._refresh_dropdown_list(filtered)
        else:
            self._open_customer_dropdown(filtered)

    def _open_customer_dropdown(self, values):
        if self._dropdown_popup and self._dropdown_popup.winfo_exists():
            self._dropdown_popup.destroy()

        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.configure(bg="#ffffff")
        self._dropdown_popup = popup

        frame = self._cust_dd_frame
        x = frame.winfo_rootx()
        y = frame.winfo_rooty() + frame.winfo_height()
        w = frame.winfo_width()
        popup.geometry(f"{w}x200+{x}+{y}")
        popup.lift()

        container = tk.Frame(popup, bg="#ffffff", bd=1, relief="solid")
        container.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(container, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        self._dd_listbox = tk.Listbox(
            container,
            yscrollcommand=scrollbar.set,
            bg="#ffffff",
            fg="#1c1c1c",
            selectbackground="#3498db",
            selectforeground="#ffffff",
            font=("Segoe UI", 11),
            activestyle="none",
            bd=0,
            highlightthickness=0,
            relief="flat",
        )
        self._dd_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self._dd_listbox.yview)

        self._refresh_dropdown_list(values)

        def on_select(event=None):
            sel = self._dd_listbox.curselection()
            if sel:
                chosen = self._dd_listbox.get(sel[0])
                self._cust_dd_var.set(chosen)
            popup.destroy()
            self._dropdown_popup = None

        self._dd_listbox.bind("<<ListboxSelect>>", on_select)
        self._dd_listbox.bind("<Return>", on_select)

        # Close when clicking outside
        popup.bind("<FocusOut>", lambda e: popup.destroy() if popup.winfo_exists() else None)
        self.winfo_toplevel().bind(
            "<Button-1>",
            lambda e: self._close_dropdown_if_outside(e, popup),
            add="+",
        )

    def _refresh_dropdown_list(self, values):
        lb = getattr(self, "_dd_listbox", None)
        if lb is None or not lb.winfo_exists():
            return
        lb.delete(0, "end")
        for v in values:
            lb.insert("end", v)

    def _close_dropdown_if_outside(self, event, popup):
        try:
            if not popup.winfo_exists():
                return
            wx, wy = popup.winfo_rootx(), popup.winfo_rooty()
            ww, wh = popup.winfo_width(), popup.winfo_height()
            if not (wx <= event.x_root <= wx + ww and wy <= event.y_root <= wy + wh):
                popup.destroy()
                self._dropdown_popup = None
        except Exception:
            pass

    def _build_filter_chips(self):
        chip_specs = [
            ("all", "All"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("balance", "With Balance"),
            ("high_balance", "High Balance"),
            ("gold", "Gold Tier"),
            ("silver", "Silver Tier"),
            ("bronze", "Bronze Tier"),
        ]
        COMPACT_THRESHOLD = 4
        for child in self.chips_frame.winfo_children():
            child.destroy()
        self.filter_buttons.clear()

        if len(chip_specs) > COMPACT_THRESHOLD:
            self.filter_button = ctk.CTkButton(
                self.chips_frame,
                text="Filter ∇",
                width=100,
                height=34,
                corner_radius=12,
                fg_color="#ebeff5",
                hover_color="#dde6f2",
                text_color="#415162",
                command=self._show_filter_popup,
            )
            self.filter_button.pack(side="left")
        else:
            self.filter_button = None
            for key, label in chip_specs:
                btn = ctk.CTkButton(
                    self.chips_frame,
                    text=label,
                    width=86,
                    height=26,
                    corner_radius=13,
                    font=("Segoe UI", 10),
                    fg_color="#ebeff5",
                    hover_color="#dde6f2",
                    text_color="#415162",
                    command=lambda k=key: self.set_active_filter(k),
                )
                btn.pack(side="left", padx=(0, 6))
                self.filter_buttons[key] = btn

        self._refresh_filter_chip_styles()

    def _show_filter_popup(self):
        if (
            self.filter_popup is not None
            and getattr(self.filter_popup, "winfo_exists", lambda: False)()
        ):
            try:
                self.filter_popup.lift()
            except Exception:
                pass
            return

        self.filter_popup = ctk.CTkToplevel(self)
        self.filter_popup.overrideredirect(True)
        fb = getattr(self, "filter_button", None)
        if fb is not None:
            bx = fb.winfo_rootx()
            by = fb.winfo_rooty() + fb.winfo_height()
        else:
            cf = getattr(self, "chips_frame", None)
            if cf is not None:
                bx = cf.winfo_rootx()
                by = cf.winfo_rooty() + cf.winfo_height()
            else:
                bx = self.winfo_rootx()
                by = self.winfo_rooty() + self.winfo_height()
        self.filter_popup.geometry(f"230x440+{bx}+{by}")
        self.filter_popup.transient(self.winfo_toplevel())

        inner = ctk.CTkFrame(
            self.filter_popup,
            fg_color="#ffffff",
            corner_radius=8,
            border_width=1,
            border_color="#e5e7eb",
        )
        inner.pack(fill="both", expand=True, padx=8, pady=8)

        chip_specs = [
            ("all", "All"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("balance", "With Balance"),
            ("high_balance", "High Balance"),
            ("gold", "Gold Tier"),
            ("silver", "Silver Tier"),
            ("bronze", "Bronze Tier"),
        ]

        def _make_select_handler(k):
            def _handler():
                if self.filter_popup is not None:
                    try:
                        if getattr(self.filter_popup, "winfo_exists", lambda: False)():
                            self.filter_popup.destroy()
                    except Exception:
                        pass
                self.set_active_filter(k)
            return _handler

        for key, label in chip_specs:
            b = ctk.CTkButton(
                inner,
                text=label,
                width=200,
                height=42,
                font=("Segoe UI", 12),
                command=_make_select_handler(key),
            )
            b.pack(pady=3)

    def set_active_filter(self, filter_key):
        self.active_filter = filter_key
        self._refresh_filter_chip_styles()
        self._render_rows()

    def _refresh_filter_chip_styles(self):
        for key, btn in self.filter_buttons.items():
            if key == self.active_filter:
                btn.configure(
                    fg_color="#d8e9fb",
                    hover_color="#c8dff7",
                    text_color="#1f5f9f",
                )
            else:
                btn.configure(
                    fg_color="#ebeff5",
                    hover_color="#dde6f2",
                    text_color="#415162",
                )

        fb = getattr(self, "filter_button", None)
        if fb is not None:
            if self.active_filter == "all":
                fb.configure(
                    fg_color="#ebeff5", hover_color="#dde6f2", text_color="#415162"
                )
            else:
                fb.configure(
                    fg_color="#d8e9fb", hover_color="#c8dff7", text_color="#1f5f9f"
                )

    def toggle_side_panels(self):
        if self._right_panel_visible:
            self.right_frame.grid_remove()
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=0)
            self._right_panel_visible = False
        else:
            self.right_frame.grid(
                row=2, column=1, sticky="nsew", padx=(0, 20), pady=(0, 20)
            )
            self.grid_columnconfigure(0, weight=3)
            self.grid_columnconfigure(1, weight=2)
            self._right_panel_visible = True
        try:
            self.search_bar.set_toggle_state(self._right_panel_visible)
        except Exception:
            pass

    def _show_row_menu(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)
        self.tree.focus(item)
        try:
            self.row_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.row_menu.grab_release()

    def _selected_customer(self):
        selected = self.tree.selection()
        if not selected:
            return None, None
        values = self.tree.item(selected[0]).get("values", [])
        if not values:
            return None, None
        try:
            cust_id = int(values[0])
        except Exception:
            cust_id = None
        company = values[1] if len(values) > 1 else ""
        return cust_id, company

    def receive_payment_for_selected(self):
        cust_id, company = self._selected_customer()
        if cust_id is None:
            messagebox.showwarning("Selection", "No customer selected.")
            return

        if not self.right_frame.winfo_viewable():
            self.toggle_side_panels()

        target = f"{cust_id} - {company}"
        options = self.customer_dropdown.cget("values")
        if target in options:
            self.customer_dropdown.set(target)
        else:
            for option in options:
                if str(option).startswith(f"{cust_id} -"):
                    self.customer_dropdown.set(option)
                    break

        self.amount_entry.focus_set()

    def view_ledger_for_selected(self):
        cust_id, company = self._selected_customer()
        if cust_id is None:
            messagebox.showwarning("Selection", "No customer selected.")
            return
        self._open_ledger_popup(cust_id, company)

    # -------------------------
    # Database / UI operations
    # -------------------------
    def _connect(self):
        return psycopg2.connect(**self.db_config)

    def _apply_filter(self, rows):
        if self.active_filter == "all":
            return list(rows)

        filtered = []
        for row in rows:
            # row = (customer_number, company_name, customer_name, phone_number,
            #         address, current_balance, is_active, balance_tier)
            _, _, _, _, _, balance, is_active, tier = row
            amount = (
                float(balance) if isinstance(balance, (int, float, Decimal)) else 0.0
            )
            tier_text = str(tier or "").lower()

            if self.active_filter == "balance" and amount > 0:
                filtered.append(row)
            elif self.active_filter == "high_balance" and amount >= 50000:
                filtered.append(row)
            elif self.active_filter == "active" and bool(is_active):
                filtered.append(row)
            elif self.active_filter == "inactive" and not bool(is_active):
                filtered.append(row)
            elif self.active_filter == "gold" and "gold" in tier_text:
                filtered.append(row)
            elif self.active_filter == "silver" and "silver" in tier_text:
                filtered.append(row)
            elif self.active_filter == "bronze" and "bronze" in tier_text:
                filtered.append(row)

        return filtered

    def _render_rows(self):
        rows_to_render = self._apply_filter(self.base_rows)

        self.table_frame.clear()

        if not self.base_rows:
            self.table_frame.show_empty_state(
                "No customers found",
                "Try adding a customer or clearing your search.",
            )
            self._populate_customer_dropdown([])
            return

        if not rows_to_render:
            self.table_frame.show_empty_state(
                "No matches for this filter",
                "Switch filter chips or clear search to see more customers.",
            )
            self._populate_customer_dropdown([])
            return

        self.table_frame.hide_empty_state()

        # Configure row color tags on the treeview
        self.tree.tag_configure("row_gold",    background="#ffffff", foreground="#000000")
        self.tree.tag_configure("row_silver",  background="#ffffff", foreground="#000000")
        self.tree.tag_configure("row_bronze",  background="#ffffff", foreground="#000000")
        self.tree.tag_configure("row_active",  background="#ffffff", foreground="#000000")
        self.tree.tag_configure("row_inactive",background="#ffffff", foreground="#000000")
        self.tree.tag_configure("row_default", background="#ffffff", foreground="#000000")
        self.tree.tag_configure("hover_even",  background="#ffffff", foreground="#000000")
        self.tree.tag_configure("hover_odd",   background="#ffffff", foreground="#000000")

        for row in rows_to_render:
            cust_no, company, contact, phone, address, balance, is_active, tier = row
            balance_str = (
                f"₱{balance:,.2f}"
                if isinstance(balance, (int, float, Decimal))
                else str(balance)
            )
            active_str = "● Active" if is_active else "○ Inactive"
            tier_text = str(tier or "")
            tier_lower = tier_text.lower()
            if "gold" in tier_lower:
                tier_str = "★ Gold"
                row_tag = "row_gold"
            elif "silver" in tier_lower:
                tier_str = "◈ Silver"
                row_tag = "row_silver"
            elif "bronze" in tier_lower:
                tier_str = "◆ Bronze"
                row_tag = "row_bronze"
            else:
                tier_str = tier_text
                row_tag = "row_active" if bool(is_active) else "row_inactive"

            debt_value = 0.0
            if isinstance(balance, (int, float, Decimal)):
                debt_value = float(balance)

            self.table_frame.insert_row(
                values=(
                    cust_no,
                    company,
                    contact,
                    phone,
                    address,
                    balance_str,
                    active_str,
                    tier_str,
                ),
                balance=debt_value,
            )

        # Apply color tags to the newly inserted rows
        all_items = self.tree.get_children()
        rendered_items = all_items[len(all_items) - len(rows_to_render):]
        _tag_map = []
        for row in rows_to_render:
            _, _, _, _, _, balance, is_active, tier = row
            tier_lower = str(tier or "").lower()
            if "gold" in tier_lower:
                _tag_map.append("row_gold")
            elif "silver" in tier_lower:
                _tag_map.append("row_silver")
            elif "bronze" in tier_lower:
                _tag_map.append("row_bronze")
            else:
                _tag_map.append("row_active" if bool(is_active) else "row_inactive")

        for item_id, tag in zip(self.tree.get_children(), _tag_map):
            self.tree.item(item_id, tags=(tag,))

        self._populate_customer_dropdown(self.base_rows)

    def _populate_customer_dropdown(self, rows):
        dropdown_values = ["Select customer..."]
        for r in rows:
            dropdown_values.append(f"{r[0]} - {r[1]}")
        self._customer_values = dropdown_values
        self._cust_dd_var.set(dropdown_values[0])

    def load_customers(self, rows=None):
        """
        Load customers directly from the customers table.
        FIX: No longer uses customer_list_view (didn't exist).
             Computes balance_tier inline using CASE expression.
             Uses customer_name (correct column) instead of contact_name (wrong).
        """
        if rows is None:
            try:
                conn = self._connect()
                cur = conn.cursor()
                cur.execute("""
                    SELECT
                        customer_number,
                        company_name,
                        customer_name,
                        phone_number,
                        address,
                        current_balance,
                        is_active,
                        CASE
                            WHEN current_balance >= 10000 THEN 'Gold'
                            WHEN current_balance >= 5000  THEN 'Silver'
                            WHEN current_balance >= 1000  THEN 'Bronze'
                            ELSE ''
                        END AS balance_tier
                    FROM customers
                    ORDER BY company_name, customer_name;
                """)
                rows = cur.fetchall()
                cur.close()
                conn.close()
            except Exception as e:
                print("Error loading customers:", e)
                rows = []

        self.base_rows = rows
        self._render_rows()

    # -------------------------
    # Search
    # -------------------------
    def search_customers(self):
        """Search DB by customer_number (exact) or company/customer_name (ILIKE)."""
        term = self.search_var.get().strip()
        if not term:
            self.load_customers()
            return

        try:
            cust_id = int(term)
        except Exception:
            cust_id = None

        try:
            conn = self._connect()
            cur = conn.cursor()
            if cust_id is not None:
                cur.execute(
                    """
                    SELECT
                        customer_number,
                        company_name,
                        customer_name,
                        phone_number,
                        address,
                        current_balance,
                        is_active,
                        CASE
                            WHEN current_balance >= 10000 THEN 'Gold'
                            WHEN current_balance >= 5000  THEN 'Silver'
                            WHEN current_balance >= 1000  THEN 'Bronze'
                            ELSE ''
                        END AS balance_tier
                    FROM customers
                    WHERE customer_number = %s
                    ORDER BY company_name;
                """,
                    (cust_id,),
                )
            else:
                like_term = f"%{term}%"
                cur.execute(
                    """
                    SELECT
                        customer_number,
                        company_name,
                        customer_name,
                        phone_number,
                        address,
                        current_balance,
                        is_active,
                        CASE
                            WHEN current_balance >= 10000 THEN 'Gold'
                            WHEN current_balance >= 5000  THEN 'Silver'
                            WHEN current_balance >= 1000  THEN 'Bronze'
                            ELSE ''
                        END AS balance_tier
                    FROM customers
                    WHERE company_name ILIKE %s OR customer_name ILIKE %s
                    ORDER BY company_name;
                """,
                    (like_term, like_term),
                )
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            print("Error searching customers:", e)
            rows = []

        self.load_customers(rows=rows)

    def clear_search(self):
        self.search_var.set("")
        self.load_customers()

    def add_customer(self):
        company = self.company_entry.get().strip()
        contact = self.contact_entry.get().strip()
        phone = self.phone_entry.get().strip()
        address = self.address_entry.get().strip()
        balance_text = self.balance_entry.get().strip()

        if not company or not address:
            messagebox.showwarning("Validation", "Company and Address are required.")
            return

        if not contact:
            messagebox.showwarning("Validation", "Contact Name is required.")
            return

        # Parse balance — default 0 kung blank
        try:
            cleaned = balance_text.replace(",", "").replace("₱", "").strip()
            opening_balance = Decimal(cleaned) if cleaned else Decimal("0.00")
            if opening_balance < 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            messagebox.showwarning("Validation", "Enter a valid balance amount (0 or more).")
            return

        try:
            conn = self._connect()
            cur = conn.cursor()

            # Use MAX(customer_number)+1 so the ID always continues from the
            # highest existing value — no dependency on the PostgreSQL sequence.
            cur.execute("""
                INSERT INTO customers (customer_number, company_name, customer_name, phone_number, address, current_balance)
                VALUES (
                    (SELECT COALESCE(MAX(customer_number), 0) + 1 FROM customers),
                    %s, %s, %s, %s, %s
                )
                RETURNING customer_number;
            """, (company, contact, phone, address, opening_balance))
            result = cur.fetchone()
            new_id = result[0] if result else None
            conn.commit()
            cur.close()
            conn.close()

            # Clear inputs
            self.company_entry.delete(0, "end")
            self.contact_entry.delete(0, "end")
            self.phone_entry.delete(0, "end")
            self.address_entry.delete(0, "end")
            self.balance_entry.delete(0, "end")

            messagebox.showinfo("Success", f"Customer added (ID {new_id}) with balance ₱{opening_balance:,.2f}.")
            self.load_customers()
        except Exception as e:
            print("Error adding customer:", e)
            messagebox.showerror("Error", f"Could not add customer: {e}")

    def process_payment(self):
        """
        Apply payment: insert into customer_payments and update current_balance.
        FIX: Uses correct schema columns — amount_paid, payment_method, invoice_id.
             Payment method must be 'cash', 'check', or 'transfer' (DB constraint).
             invoice_id is left NULL (general account credit, allowed by schema).
        """
        sel = self.customer_dropdown.get()
        if not sel or sel == "Select customer...":
            messagebox.showwarning(
                "Validation", "Please select a customer from the dropdown."
            )
            return

        try:
            cust_id = int(sel.split(" - ", 1)[0])
        except Exception:
            messagebox.showwarning("Validation", "Invalid customer selection.")
            return

        amount_text = self.amount_entry.get().strip()
        if not amount_text:
            messagebox.showwarning("Validation", "Enter an amount.")
            return

        try:
            cleaned = amount_text.replace(",", "").replace("₱", "").strip()
            amount = Decimal(cleaned)
            if amount <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            messagebox.showwarning("Validation", "Enter a valid positive amount.")
            return

        method = self.method_dropdown.get().strip().lower()
        if method not in ("cash", "check", "transfer"):
            messagebox.showwarning(
                "Validation", "Payment method must be cash, check, or transfer."
            )
            return

        try:
            conn = self._connect()
            cur = conn.cursor()

            # 1. Insert payment record into customer_payments
            #    invoice_id is NULL = general account credit (allowed by schema)
            cur.execute(
                """
                INSERT INTO customer_payments (
                    customer_number,
                    invoice_id,
                    payment_date,
                    amount_paid,
                    payment_method
                )
                VALUES (%s, NULL, CURRENT_DATE, %s, %s);
            """,
                (cust_id, amount, method),
            )

            # 2. Update the customer's running balance (decrease by amount paid)
            cur.execute(
                """
                UPDATE customers
                SET current_balance = current_balance - %s
                WHERE customer_number = %s
                RETURNING current_balance;
            """,
                (amount, cust_id),
            )
            result = cur.fetchone()
            if result is None:
                raise Exception("Customer not found.")
            new_balance = result[0]

            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo(
                "Payment Processed",
                f"Payment of ₱{amount:,.2f} applied.\nNew balance: ₱{new_balance:,.2f}",
            )
            self.amount_entry.delete(0, "end")
            self.note_entry.delete(0, "end")
            # Reset filter to All so customer stays visible regardless of new balance
            self.active_filter = "all"
            self._refresh_filter_chip_styles()
            self.load_customers()

        except Exception as e:
            print("Error processing payment:", e)
            messagebox.showerror("Error", f"Could not process payment: {e}")

    def _open_ledger_popup(self, cust_id, company):
        """
        Show payment history for a customer.
        FIX: Queries customer_payments using correct schema columns:
             payment_date, amount_paid, payment_method (no payment_note or balance_after).
        """
        lines = []
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    payment_date,
                    amount_paid,
                    payment_method,
                    COALESCE(invoice_id::text, 'General Credit') AS invoice_ref
                FROM customer_payments
                WHERE customer_number = %s
                ORDER BY payment_date DESC, payment_id DESC
                LIMIT 100;
            """,
                (cust_id,),
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()

            if not rows:
                lines.append("No payment records for this customer yet.")
            else:
                for (payment_date, amount_paid, payment_method, invoice_ref) in rows:
                    lines.append(
                        f"{payment_date} | -₱{amount_paid:,.2f} | {payment_method} | Ref: {invoice_ref}"
                    )

        except Exception as e:
            lines = [f"Could not load payment ledger: {e}"]

        popup = ctk.CTkToplevel(self)
        popup.title(f"Payment Ledger - {cust_id} {company}")
        popup.geometry("700x420")
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        ctk.CTkLabel(
            popup,
            text=f"Payment Ledger: {company} (ID {cust_id})",
            font=("Segoe UI", 16, "bold"),
            text_color="#2c3e50",
        ).pack(anchor="w", padx=14, pady=(12, 8))

        ledger_box = ctk.CTkTextbox(
            popup,
            fg_color="#f8f9fa",
            border_width=1,
            border_color="#d0d7de",
        )
        ledger_box.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        ledger_box.insert("1.0", "\n".join(lines))
        ledger_box.configure(state="disabled")

    # -------------------------
    # Edit customer workflow
    # -------------------------
    def edit_customer(self):
        """Open edit popup for selected row."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "No customer selected.")
            return
        cust_id = self.tree.item(selected[0])["values"][0]
        self._open_edit_popup(cust_id)

    def _on_row_double_click(self, event):
        """Double-click a row to edit."""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        cust_id = self.tree.item(item)["values"][0]
        self._open_edit_popup(cust_id)

    def _open_edit_popup(self, cust_id):
        """
        Popup window to edit customer fields.
        FIX: Uses customer_name (correct column) instead of contact_name (wrong).
        """
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT customer_number, company_name, customer_name,
                       phone_number, address, current_balance, is_active
                FROM customers
                WHERE customer_number = %s;
            """,
                (cust_id,),
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            if not row:
                messagebox.showerror("Error", "Customer not found.")
                return
        except Exception as e:
            print("Error fetching customer for edit:", e)
            messagebox.showerror("Error", f"Could not fetch customer: {e}")
            return

        popup = ctk.CTkToplevel(self)
        popup.title(f"Edit Customer {cust_id}")
        popup.geometry("500x560")
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        _, company, contact, phone, address, balance, is_active = row

        ctk.CTkLabel(popup, text="Company", anchor="w").pack(
            fill="x", padx=12, pady=(12, 4)
        )
        company_e = ctk.CTkEntry(popup)
        company_e.pack(fill="x", padx=12, pady=4)
        company_e.insert(0, company or "")

        ctk.CTkLabel(popup, text="Contact Name", anchor="w").pack(
            fill="x", padx=12, pady=(8, 4)
        )
        contact_e = ctk.CTkEntry(popup)
        contact_e.pack(fill="x", padx=12, pady=4)
        contact_e.insert(0, contact or "")

        ctk.CTkLabel(popup, text="Phone", anchor="w").pack(
            fill="x", padx=12, pady=(8, 4)
        )
        phone_e = ctk.CTkEntry(popup)
        phone_e.pack(fill="x", padx=12, pady=4)
        phone_e.insert(0, phone or "")

        ctk.CTkLabel(popup, text="Address", anchor="w").pack(
            fill="x", padx=12, pady=(8, 4)
        )
        address_e = ctk.CTkEntry(popup)
        address_e.pack(fill="x", padx=12, pady=4)
        address_e.insert(0, address or "")

        ctk.CTkLabel(popup, text="Current Balance", anchor="w").pack(
            fill="x", padx=12, pady=(8, 4)
        )
        balance_e = ctk.CTkEntry(popup)
        balance_e.pack(fill="x", padx=12, pady=4)
        balance_e.insert(0, str(balance))

        active_var = ctk.StringVar(value="Yes" if is_active else "No")
        ctk.CTkLabel(popup, text="Active", anchor="w").pack(
            fill="x", padx=12, pady=(8, 4)
        )
        active_cb = ctk.CTkComboBox(popup, values=["Yes", "No"], variable=active_var)
        active_cb.pack(fill="x", padx=12, pady=4)

        def save_changes():
            new_company = company_e.get().strip()
            new_contact = contact_e.get().strip()
            new_phone = phone_e.get().strip()
            new_address = address_e.get().strip()
            new_balance_text = balance_e.get().strip()
            new_active = True if active_var.get() == "Yes" else False

            if not new_company or not new_address or not new_contact:
                messagebox.showwarning(
                    "Validation", "Company, Contact Name, and Address are required."
                )
                return

            try:
                cleaned = new_balance_text.replace(",", "").replace("₱", "").strip()
                new_balance = Decimal(cleaned)
            except Exception:
                messagebox.showwarning("Validation", "Enter a valid numeric balance.")
                return

            try:
                conn = self._connect()
                cur = conn.cursor()
                # FIX: Uses customer_name (correct) not contact_name (wrong)
                cur.execute(
                    """
                    UPDATE customers
                    SET company_name     = %s,
                        customer_name   = %s,
                        phone_number    = %s,
                        address         = %s,
                        current_balance = %s,
                        is_active       = %s
                    WHERE customer_number = %s;
                """,
                    (
                        new_company,
                        new_contact,
                        new_phone,
                        new_address,
                        new_balance,
                        new_active,
                        cust_id,
                    ),
                )
                conn.commit()
                cur.close()
                conn.close()
                messagebox.showinfo("Saved", "Customer updated successfully.")
                popup.destroy()
                self.load_customers()
            except Exception as e:
                print("Error saving customer:", e)
                messagebox.showerror("Error", f"Could not save changes: {e}")

        for _e in (company_e, contact_e, phone_e, address_e, balance_e):
            _e.bind("<Return>", lambda event: save_changes())

        save_btn = ctk.CTkButton(
            popup, text="Save Changes", fg_color="#3498db", command=save_changes
        )
        save_btn.pack(pady=12, padx=12, fill="x")

        cancel_btn = ctk.CTkButton(
            popup,
            text="Cancel",
            fg_color="#bdc3c7",
            hover_color="#95a5a6",
            command=popup.destroy,
        )
        cancel_btn.pack(padx=12, pady=(0, 12), fill="x")