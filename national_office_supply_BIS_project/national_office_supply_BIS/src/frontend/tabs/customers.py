import customtkinter as ctk
from tkinter import ttk, messagebox
import psycopg2
from decimal import Decimal, InvalidOperation

class CustomersView(ctk.CTkFrame):
    def __init__(self, parent, controller, db_config):
        super().__init__(parent, fg_color="#f8f9fa")
        self.controller = controller
        self.db_config = db_config

        # Layout: 2 columns (table | right panels)
        # Start with right column collapsed so table fills screen
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # -----------------------
        # SEARCH BAR (top left)
        # -----------------------
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="new", padx=20, pady=(20, 6))
        search_frame.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search by ID, Company, or Contact",
            textvariable=self.search_var
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self.search_customers())

        search_btn = ctk.CTkButton(search_frame, text="Search", width=90, command=self.search_customers)
        search_btn.grid(row=0, column=1, padx=(0, 6))

        clear_btn = ctk.CTkButton(
            search_frame,
            text="Clear",
            width=90,
            fg_color="#bdc3c7",
            hover_color="#95a5a6",
            command=self.clear_search
        )
        clear_btn.grid(row=0, column=2)

        # --- LEFT: Customer Table (below search bar) ---
        self.table_frame = ctk.CTkFrame(self, fg_color="#ffffff",
                                        corner_radius=12, border_width=1,
                                        border_color="#e0e0e0")
        # leave space for search bar by adding top padding
        self.table_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(60, 20))

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"))

        self.tree = ttk.Treeview(self.table_frame, columns=(
            "ID", "Company", "Contact", "Phone", "Address", "Balance", "Active", "Tier"
        ), show="headings", height=20)

        # Headings + alignment
        self.tree.heading("ID", text="ID")
        self.tree.column("ID", width=60, anchor="center")

        self.tree.heading("Company", text="Company")
        self.tree.column("Company", width=220, anchor="w")

        self.tree.heading("Contact", text="Contact")
        self.tree.column("Contact", width=160, anchor="w")

        self.tree.heading("Phone", text="Phone")
        self.tree.column("Phone", width=130, anchor="w")

        self.tree.heading("Address", text="Address")
        self.tree.column("Address", width=300, anchor="w")

        self.tree.heading("Balance", text="Balance")
        self.tree.column("Balance", width=110, anchor="center")

        self.tree.heading("Active", text="Active")
        self.tree.column("Active", width=80, anchor="center")

        self.tree.heading("Tier", text="Tier")
        self.tree.column("Tier", width=100, anchor="w")

        # Pack tree with scrollbar
        vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Bind double-click to edit
        self.tree.bind("<Double-1>", self._on_row_double_click)

        # --- RIGHT: container for Add Customer (top) and Payment (bottom) ---
        self.right_frame = ctk.CTkFrame(self, fg_color="#ffffff",
                                        corner_radius=12, border_width=1,
                                        border_color="#e0e0e0")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.right_frame.grid_remove()  # hidden by default

        # Make right_frame use vertical stacking
        self.right_frame.grid_rowconfigure(0, weight=0)  # add panel
        self.right_frame.grid_rowconfigure(1, weight=1)  # payment panel
        self.right_frame.grid_columnconfigure(0, weight=1)

        # --- Add Customer Panel (top of right_frame) ---
        self.add_frame = ctk.CTkFrame(self.right_frame, fg_color="#f9f9f9",
                                      corner_radius=8, border_width=1,
                                      border_color="#d0d0d0")
        self.add_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        self.add_frame.grid_remove()  # hidden initially

        ctk.CTkLabel(self.add_frame, text="Add Customer",
                     font=("Segoe UI", 14, "bold")).pack(pady=(8, 6))

        self.company_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Company Name")
        self.company_entry.pack(fill="x", padx=12, pady=4)

        self.contact_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Contact Name")
        self.contact_entry.pack(fill="x", padx=12, pady=4)

        self.phone_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Phone Number")
        self.phone_entry.pack(fill="x", padx=12, pady=4)

        self.address_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Address")
        self.address_entry.pack(fill="x", padx=12, pady=4)

        add_btn = ctk.CTkButton(self.add_frame, text="Add Customer",
                                fg_color="#27ae60", hover_color="#1e8449",
                                command=self.add_customer)
        add_btn.pack(pady=10)

        # --- Payment Panel (below add_frame) ---
        self.payment_frame = ctk.CTkFrame(self.right_frame, fg_color="#f9f9f9",
                                          corner_radius=8, border_width=1,
                                          border_color="#d0d0d0")
        self.payment_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 12))
        self.payment_frame.grid_remove()  # hidden initially

        ctk.CTkLabel(self.payment_frame, text="Receive Payment",
                     font=("Segoe UI", 14, "bold")).pack(pady=(8, 6))

        self.customer_dropdown = ctk.CTkComboBox(self.payment_frame, values=[])
        self.customer_dropdown.pack(fill="x", padx=12, pady=6)

        self.amount_entry = ctk.CTkEntry(self.payment_frame, placeholder_text="Enter amount")
        self.amount_entry.pack(fill="x", padx=12, pady=6)

        self.method_dropdown = ctk.CTkComboBox(self.payment_frame,
                                               values=["Cash", "Credit Card", "Bank Transfer"])
        self.method_dropdown.pack(fill="x", padx=12, pady=6)

        process_btn = ctk.CTkButton(self.payment_frame, text="Process Payment",
                                    fg_color="#3498db", hover_color="#2980b9",
                                    command=self.process_payment)
        process_btn.pack(fill="x", padx=12, pady=12)

        # --- ACTION BUTTONS (bottom row) ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=10)

        ctk.CTkButton(btn_frame, text="Refresh", fg_color="#3498db",
                      hover_color="#2980b9", command=self.load_customers).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Toggle Add Customer", fg_color="#8e44ad",
                      hover_color="#6c3483", command=self.toggle_add_panel).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Toggle Payment Receive", fg_color="#2b9430",
                      hover_color="#1c7421", command=self.toggle_payment_panel).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Edit Customer", fg_color="#f39c12",
                      hover_color="#d68910", command=self.edit_customer).pack(side="left", padx=6)

        # Load initial data
        self.load_customers()

    # -------------------------
    # Database / UI operations
    # -------------------------
    def _connect(self):
        return psycopg2.connect(**self.db_config)

    def load_customers(self, rows=None):
        """Load rows from customer_list_view and populate tree and dropdown.
           If rows is provided, use it (used by search)."""
        if rows is None:
            try:
                conn = self._connect()
                cur = conn.cursor()
                cur.execute("""
                    SELECT customer_number, company_name, contact_name, phone_number,
                           address, current_balance, is_active, balance_tier
                    FROM customer_list_view;
                """)
                rows = cur.fetchall()
                cur.close()
                conn.close()
            except Exception as e:
                print("Error loading customers:", e)
                rows = []

        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert rows
        for row in rows:
            cust_no, company, contact, phone, address, balance, is_active, tier = row
            balance_str = f"₱{balance:,.2f}" if isinstance(balance, (int, float, Decimal)) else str(balance)
            active_str = "Yes" if is_active else "No"
            self.tree.insert("", "end", values=(cust_no, company, contact, phone, address, balance_str, active_str, tier))

        # Populate customer dropdown (id - company)
        dropdown_values = ["Select customer..."]
        for r in rows:
            dropdown_values.append(f"{r[0]} - {r[1]}")
        self.customer_dropdown.configure(values=dropdown_values)
        if len(dropdown_values) > 0:
            self.customer_dropdown.set(dropdown_values[0])

    # -------------------------
    # Search
    # -------------------------
    def search_customers(self):
        """Search DB by customer_number (exact) or company/contact (ILIKE)."""
        term = self.search_var.get().strip()
        if not term:
            self.load_customers()
            return

        # If term is integer, search by customer_number first
        try:
            cust_id = int(term)
        except Exception:
            cust_id = None

        try:
            conn = self._connect()
            cur = conn.cursor()
            if cust_id is not None:
                cur.execute("""
                    SELECT customer_number, company_name, contact_name, phone_number,
                           address, current_balance, is_active, balance_tier
                    FROM customer_list_view
                    WHERE customer_number = %s
                    ORDER BY company_name;
                """, (cust_id,))
            else:
                like_term = f"%{term}%"
                cur.execute("""
                    SELECT customer_number, company_name, contact_name, phone_number,
                           address, current_balance, is_active, balance_tier
                    FROM customer_list_view
                    WHERE company_name ILIKE %s OR contact_name ILIKE %s
                    ORDER BY company_name;
                """, (like_term, like_term))
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            print("Error searching customers:", e)
            # Fallback: client-side filter of currently loaded rows
            rows = []
            for item in self.tree.get_children():
                vals = self.tree.item(item)["values"]
                if any(term.lower() in str(v).lower() for v in (vals[0], vals[1], vals[2])):
                    rows.append((vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], vals[6], vals[7]))

        self.load_customers(rows=rows)

    def clear_search(self):
        self.search_var.set("")
        self.load_customers()

    # -------------------------
    # Panels toggles and helpers
    # -------------------------
    def _ensure_right_visible(self):
        """Ensure right_frame is visible and column weights set for two-column layout."""
        if not self.right_frame.winfo_viewable():
            self.right_frame.grid()
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)

    def _maybe_hide_right(self):
        """Hide right_frame entirely if both panels are hidden; otherwise ensure visible."""
        add_visible = self.add_frame.winfo_viewable()
        pay_visible = self.payment_frame.winfo_viewable()
        if not add_visible and not pay_visible:
            # hide whole right frame and let table fill
            if self.right_frame.winfo_viewable():
                self.right_frame.grid_remove()
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=0)
        else:
            # ensure right frame visible and set weights
            self._ensure_right_visible()

    def toggle_add_panel(self):
        """
        Toggle only the Add Customer panel.
        Behavior:
          - If right_frame hidden, show right_frame and show only add panel.
          - If add panel visible, hide it (and possibly hide right_frame if payment also hidden).
          - If add panel hidden and payment visible, show add panel above payment.
        """
        if not self.right_frame.winfo_viewable():
            # show right frame and show only add panel
            self.right_frame.grid()
            self.add_frame.grid()
            self.payment_frame.grid_remove()
            self.grid_columnconfigure(0, weight=3)
            self.grid_columnconfigure(1, weight=2)
            return

        if self.add_frame.winfo_viewable():
            # hide add panel
            self.add_frame.grid_remove()
            self._maybe_hide_right()
        else:
            # show add panel; keep payment panel as-is (if payment visible, add will be on top)
            self.add_frame.grid()
            self._ensure_right_visible()

    def toggle_payment_panel(self):
        """
        Toggle only the Payment panel.
        Behavior:
          - If right_frame hidden, show right_frame and show only payment panel.
          - If payment panel visible, hide it (and possibly hide right_frame if add also hidden).
          - If payment panel hidden and add visible, show payment panel below add.
        """
        if not self.right_frame.winfo_viewable():
            # show right frame and show only payment panel
            self.right_frame.grid()
            self.payment_frame.grid()
            self.add_frame.grid_remove()
            self.grid_columnconfigure(0, weight=3)
            self.grid_columnconfigure(1, weight=2)
            return

        if self.payment_frame.winfo_viewable():
            # hide payment panel
            self.payment_frame.grid_remove()
            self._maybe_hide_right()
        else:
            # show payment panel; keep add panel as-is (if add visible, payment will be below)
            self.payment_frame.grid()
            self._ensure_right_visible()

    def add_customer(self):
        """Insert a new customer into customers table and refresh."""
        company = self.company_entry.get().strip()
        contact = self.contact_entry.get().strip()
        phone = self.phone_entry.get().strip()
        address = self.address_entry.get().strip()

        if not company or not address:
            messagebox.showwarning("Validation", "Company and Address are required.")
            return

        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO customers (company_name, contact_name, phone_number, address)
                VALUES (%s, %s, %s, %s)
                RETURNING customer_number;
            """, (company, contact, phone, address))
            new_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            # Clear inputs
            self.company_entry.delete(0, "end")
            self.contact_entry.delete(0, "end")
            self.phone_entry.delete(0, "end")
            self.address_entry.delete(0, "end")
            messagebox.showinfo("Success", f"Customer added (ID {new_id}).")
            self.load_customers()
        except Exception as e:
            print("Error adding customer:", e)
            messagebox.showerror("Error", f"Could not add customer: {e}")

    def process_payment(self):
        """Apply payment: subtract amount from current_balance for selected customer."""
        sel = self.customer_dropdown.get()
        if not sel or sel == "Select customer...":
            messagebox.showwarning("Validation", "Please select a customer from the dropdown.")
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

        method = self.method_dropdown.get()
        if not method:
            messagebox.showwarning("Validation", "Select a payment method.")
            return

        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("""
                UPDATE customers
                SET current_balance = current_balance - %s
                WHERE customer_number = %s
                RETURNING current_balance;
            """, (amount, cust_id))
            result = cur.fetchone()
            if result is None:
                raise Exception("Customer not found.")
            new_balance = result[0]
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo("Payment Processed", f"Payment of {amount:,.2f} applied. New balance: ₱{new_balance:,.2f}")
            self.amount_entry.delete(0, "end")
            self.load_customers()
        except Exception as e:
            print("Error processing payment:", e)
            messagebox.showerror("Error", f"Could not process payment: {e}")

    # -------------------------
    # Edit customer workflow
    # -------------------------
    def edit_customer(self):
        """Open edit popup for selected row (Edit Customer button)."""
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
        """Popup window to edit customer fields and save changes."""
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("""
                SELECT customer_number, company_name, contact_name, phone_number, address, current_balance, is_active
                FROM customers
                WHERE customer_number = %s;
            """, (cust_id,))
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
        popup.geometry("480x420")
        popup.transient(self)
        popup.grab_set()

        _, company, contact, phone, address, balance, is_active = row

        ctk.CTkLabel(popup, text="Company", anchor="w").pack(fill="x", padx=12, pady=(12,4))
        company_e = ctk.CTkEntry(popup)
        company_e.pack(fill="x", padx=12, pady=4)
        company_e.insert(0, company or "")

        ctk.CTkLabel(popup, text="Contact", anchor="w").pack(fill="x", padx=12, pady=(8,4))
        contact_e = ctk.CTkEntry(popup)
        contact_e.pack(fill="x", padx=12, pady=4)
        contact_e.insert(0, contact or "")

        ctk.CTkLabel(popup, text="Phone", anchor="w").pack(fill="x", padx=12, pady=(8,4))
        phone_e = ctk.CTkEntry(popup)
        phone_e.pack(fill="x", padx=12, pady=4)
        phone_e.insert(0, phone or "")

        ctk.CTkLabel(popup, text="Address", anchor="w").pack(fill="x", padx=12, pady=(8,4))
        address_e = ctk.CTkEntry(popup)
        address_e.pack(fill="x", padx=12, pady=4)
        address_e.insert(0, address or "")

        ctk.CTkLabel(popup, text="Current Balance", anchor="w").pack(fill="x", padx=12, pady=(8,4))
        balance_e = ctk.CTkEntry(popup)
        balance_e.pack(fill="x", padx=12, pady=4)
        balance_e.insert(0, str(balance))

        active_var = ctk.StringVar(value="Yes" if is_active else "No")
        ctk.CTkLabel(popup, text="Active", anchor="w").pack(fill="x", padx=12, pady=(8,4))
        active_cb = ctk.CTkComboBox(popup, values=["Yes", "No"], variable=active_var)
        active_cb.pack(fill="x", padx=12, pady=4)

        def save_changes():
            new_company = company_e.get().strip()
            new_contact = contact_e.get().strip()
            new_phone = phone_e.get().strip()
            new_address = address_e.get().strip()
            new_balance_text = balance_e.get().strip()
            new_active = True if active_var.get() == "Yes" else False

            if not new_company or not new_address:
                messagebox.showwarning("Validation", "Company and Address are required.")
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
                cur.execute("""
                    UPDATE customers
                    SET company_name = %s,
                        contact_name = %s,
                        phone_number = %s,
                        address = %s,
                        current_balance = %s,
                        is_active = %s
                    WHERE customer_number = %s;
                """, (new_company, new_contact, new_phone, new_address, new_balance, new_active, cust_id))
                conn.commit()
                cur.close()
                conn.close()
                messagebox.showinfo("Saved", "Customer updated.")
                popup.destroy()
                self.load_customers()
            except Exception as e:
                print("Error saving customer:", e)
                messagebox.showerror("Error", f"Could not save changes: {e}")

        save_btn = ctk.CTkButton(popup, text="Save Changes", fg_color="#3498db", command=save_changes)
        save_btn.pack(pady=12, padx=12, fill="x")

        cancel_btn = ctk.CTkButton(popup, text="Cancel", fg_color="#bdc3c7",
                                   hover_color="#95a5a6", command=popup.destroy)
        cancel_btn.pack(padx=12, pady=(0,12), fill="x")
