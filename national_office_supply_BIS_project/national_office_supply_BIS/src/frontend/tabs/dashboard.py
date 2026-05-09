import customtkinter as ctk
from tkinter import ttk

psycopg2 = None
try:
    import psycopg2
    HAS_DB = True
except ImportError:
    HAS_DB = False

from frontend.modular.metric_card import MetricCard

class DashboardView(ctk.CTkScrollableFrame):
    def __init__(
        self, parent, controller, username="User", role="Staff", db_config=None
    ):
        super().__init__(parent, fg_color="#f8f9fa", corner_radius=0, border_width=0)
        self.controller = controller
        self.db_config = db_config
        self.username = username
        self.role = role

        self.columnconfigure(0, weight=1)

        # --- 1. WELCOME HEADER ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(25, 0))

        self.welcome_label = ctk.CTkLabel(
            self.header_frame,
            text=f"Welcome back, {self.username} - {self.role}",
            font=("Segoe UI", 28, "bold"),
            text_color="#2c3e50",
        )
        self.welcome_label.pack(side="left")
        
        # --- RIGHT-ALIGNED STATUS CONTAINER ---
        # Moving this to side="right" creates a cleaner "Status Bar" look
        self.status_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.status_container.pack(side="right", pady=(10, 0))

        # Refresh Button (Small and subtle)
        self.refresh_btn = ctk.CTkButton(
            self.status_container,
            text="🔄",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#e0e0e0",
            text_color="#7f8c8d",
            command=self._load_dashboard_data # Re-runs queries and connection check
        )
        self.refresh_btn.pack(side="right", padx=(10, 0))

        self.conn_status = ctk.CTkLabel(
            self.status_container,
            text=" ●  DB: CHECKING...",
            font=("Segoe UI", 12, "bold"),
            text_color="#7f8c8d"
        )
        self.conn_status.pack(side="right")

        # --- 2. DYNAMIC NOTICE CONTAINER ---
        # Used to display FS-Sec6 Critical Stock Alerts
        self.notice_frame = ctk.CTkFrame(self, fg_color="transparent", height=0)
        self.notice_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=0)

        # --- 3. METRIC GRID ---
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=(10, 20))
        self.grid_frame.columnconfigure((0, 1, 2, 3), weight=1, pad=20)

        # Metric Cards (Dynamic Titles based on Role)
        card_titles = {
            "Manager": ["Total Revenue (Paid)", "Pending Orders", "Total Customers", "Critical Stock"],
            "Sales Rep": ["My YTD Sales", "Est. Commission", "My Pending Orders", "Active Customers"],
            "Hourly": ["Hours This Week", "Next Payday", "Company Updates", "Status"]
        }.get(self.role, ["Metric 1", "Metric 2", "Metric 3", "Metric 4"])

        self.rev_card = MetricCard(
            self.grid_frame, card_titles[0], "$---", "Waiting for data...", "💰", "#7f8c8d"
        )
        self.rev_card.grid(row=0, column=0, sticky="nsew")

        self.orders_card = MetricCard(
            self.grid_frame, card_titles[1], "0", "Waiting for data...", "🛒", "#7f8c8d"
        )
        self.orders_card.grid(row=0, column=1, sticky="nsew")

        self.cust_card = MetricCard(
            self.grid_frame, card_titles[2], "0", "Waiting for data...", "👥", "#7f8c8d"
        )
        self.cust_card.grid(row=0, column=2, sticky="nsew")

        self.stock_card = MetricCard(
            self.grid_frame, card_titles[3], "---", "Checking inventory...", "📦", "#7f8c8d"
        )
        self.stock_card.grid(row=0, column=3, sticky="nsew")

        # --- 4. RECENT ACTIVITY TABLE ---
        self.table_frame = ctk.CTkFrame(
            self, fg_color="#ffffff", corner_radius=12, border_width=1, border_color="#e0e0e0"
        )
        self.table_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=20)

        ctk.CTkLabel(
            self.table_frame,
            text="Recent Sales Activity" if self.role == "Manager" else "My Recent Invoices",
            font=("Segoe UI", 16, "bold"),
            text_color="#2c3e50",
        ).pack(anchor="w", padx=20, pady=15)

        # --- RECENT ACTIVITY TREEVIEW ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dashboard.Treeview",
            font=("Segoe UI", 11),
            rowheight=34,
            background="#ffffff",
            fieldbackground="#ffffff",
            borderwidth=0,
        )
        style.configure(
            "Dashboard.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            background="#f8f9fa",
            foreground="#2c3e50",
            relief="flat",
        )

        cols = ("Invoice #", "Customer", "Amount", "Status", "Date")
        self.recent_tree = ttk.Treeview(
            self.table_frame, columns=cols, show="headings", height=8, style="Dashboard.Treeview"
        )

        column_widths = {
            "Invoice #": 100, "Customer": 250, "Amount": 120, "Status": 100, "Date": 120,
        }
        for col in cols:
            self.recent_tree.heading(col, text=col)
            self.recent_tree.column(col, width=column_widths[col], anchor="w")

        self.recent_tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._load_dashboard_data()

    def _load_dashboard_data(self):
        if not HAS_DB or psycopg2 is None or not self.db_config:
            self._update_ui_on_error("Library Missing")
            return
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # --- UPDATE STATUS BADGE: CONNECTED ---
            db_name = self.db_config.get('dbname', 'PostgreSQL')
            self.conn_status.configure(text=f" ● CONNECTED", text_color="#2ecc71")

            # Identify the logged-in user's ID for RBAC queries
            emp_id = self.controller.session.employee_number if hasattr(self.controller, 'session') else 0

            if self.role == "Manager":
                # --- MANAGER QUERIES ---
                # Fixed: Use status = 'paid' instead of is_paid = TRUE
                cur.execute("SELECT COALESCE(SUM(total_amount), 0) FROM invoices WHERE status = 'paid';")
                revenue = cur.fetchone()[0]

                # Fixed: Your schema uses 'active' for pending orders
                cur.execute("SELECT COUNT(*) FROM invoices WHERE status = 'active';")
                orders = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM customers WHERE is_active = TRUE;")
                customers = cur.fetchone()[0]

                # Req 5 & FS-Sec6: Critical Stock Check
                cur.execute("SELECT COUNT(*) FROM parts WHERE stock_count <= 1 AND on_order = FALSE;")
                critical_stock = cur.fetchone()[0]

                # Update Cards
                self.rev_card.update_value(f"₱{revenue:,.2f}")
                self.orders_card.update_value(str(orders))
                self.cust_card.update_value(str(customers))
                self.stock_card.update_value(str(critical_stock))
                
                # Trigger Action Center Alert
                if critical_stock > 0:
                    self._show_critical_alert(critical_stock)

                # Recent Sales (Company-wide)
                # Fixed: Used date_written and customer_number to match your schema
                cur.execute("""
                    SELECT i.invoice_id, c.company_name, i.total_amount, i.status, i.date_written
                    FROM invoices i
                    JOIN customers c ON i.customer_number = c.customer_number
                    ORDER BY i.date_written DESC, i.invoice_id DESC
                    LIMIT 10;
                """)

            elif self.role == "Sales Rep":
                # --- SALES REP QUERIES ---
                # Fixed: employee_number instead of rep_id, status='paid'
                cur.execute("SELECT COALESCE(SUM(total_amount), 0) FROM invoices WHERE employee_number = %s AND status = 'paid';", (emp_id,))
                my_revenue = cur.fetchone()[0]
                commission = my_revenue * 0.05 # 5% Commission Logic

                cur.execute("SELECT COUNT(*) FROM invoices WHERE employee_number = %s AND status = 'active';", (emp_id,))
                my_orders = cur.fetchone()[0]

                cur.execute("SELECT COUNT(DISTINCT customer_number) FROM invoices WHERE employee_number = %s;", (emp_id,))
                my_customers = cur.fetchone()[0]

                # Update Cards
                self.rev_card.update_value(f"₱{my_revenue:,.2f}")
                self.orders_card.update_value(f"₱{commission:,.2f}") 
                self.cust_card.update_value(str(my_orders))
                self.stock_card.update_value(str(my_customers))

                # Recent Sales (Personal)
                # Fixed: Matching schema column names
                cur.execute("""
                    SELECT i.invoice_id, c.company_name, i.total_amount, i.status, i.date_written
                    FROM invoices i
                    JOIN customers c ON i.customer_number = c.customer_number
                    WHERE i.employee_number = %s
                    ORDER BY i.date_written DESC, i.invoice_id DESC
                    LIMIT 10;
                """, (emp_id,))
            else:
                # Hourly Staff
                cur.execute("SELECT 1;") # Dummy query to prevent fetchall error

            # Populate Treeview
            recent_sales = cur.fetchall()
            for row in self.recent_tree.get_children():
                self.recent_tree.delete(row)

            for row in recent_sales:
                # Handle dummy query for Hourly
                if len(row) == 1:
                    continue
                    
                inv_id, cust_name, amt, status, d_written = row
                self.recent_tree.insert(
                    "", "end",
                    values=(f"INV-{inv_id}", cust_name, f"₱{amt:,.2f}", str(status).title(), d_written),
                )

            cur.close()
            conn.close()

        except Exception as e:
            print(f"[DashboardView] Error loading dashboard data: {e}")
            
    def _show_critical_alert(self, count):
        """Displays the FS-Sec6 Critical Alert in the Notice Frame."""
        self.notice_frame.configure(height=50)
        self.notice_frame.grid_configure(pady=(10, 0))
        
        alert_bg = ctk.CTkFrame(self.notice_frame, fg_color="#fdeceb", border_color="#f5c6cb", border_width=1, corner_radius=8)
        alert_bg.pack(fill="x", expand=True)
        
        ctk.CTkLabel(
            alert_bg, 
            text=f"⚠️ CRITICAL INVENTORY ALERT: {count} parts have stock levels at or below 1 with no active purchase orders.", 
            text_color="#721c24", 
            font=("Segoe UI", 12, "bold")
        ).pack(side="left", padx=15, pady=10)
        
    def _update_ui_on_error(self, error_msg):
        """Updates UI to reflect that the database is offline."""
        self.conn_status.configure(text=f" ●  DB: {error_msg}", text_color="#e74c3c")
        
        # Set cards to an "N/A" state so the user knows they aren't seeing live data
        error_val = "N/A"
        self.rev_card.update_value(error_val)
        self.orders_card.update_value(error_val)
        self.cust_card.update_value(error_val)
        self.stock_card.update_value(error_val)