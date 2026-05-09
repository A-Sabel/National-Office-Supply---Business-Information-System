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
        # Removing border_width here is usually enough to stop the line
        super().__init__(parent, fg_color="#f8f9fa", corner_radius=0, border_width=0)
        self.controller = controller
        self.db_config = db_config

        # REMOVED: self._canvas.configure(highlightthickness=0)
        # (This was causing your AttributeError)

        self.columnconfigure(0, weight=1)

        # --- 1. WELCOME HEADER ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(25, 0))

        self.welcome_label = ctk.CTkLabel(
            self.header_frame,
            text=f"Welcome back, {username} - {role}",
            font=("Segoe UI", 28, "bold"),
            text_color="#2c3e50",
        )
        self.welcome_label.pack(side="left")

        # --- 2. DYNAMIC NOTICE CONTAINER ---
        self.notice_frame = ctk.CTkFrame(self, fg_color="transparent", height=0)
        self.notice_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=0)

        # --- 3. METRIC GRID ---
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=(10, 20))
        self.grid_frame.columnconfigure((0, 1, 2, 3), weight=1, pad=20)

        # Metric Cards (Blank/Loading State)
        self.rev_card = MetricCard(
            self.grid_frame,
            "Total Revenue",
            "$---",
            "Waiting for data...",
            "💰",
            "#7f8c8d",
        )
        self.rev_card.grid(row=0, column=0, sticky="nsew")

        self.orders_card = MetricCard(
            self.grid_frame,
            "Active Orders",
            "0",
            "Waiting for data...",
            "🛒",
            "#7f8c8d",
        )
        self.orders_card.grid(row=0, column=1, sticky="nsew")

        self.cust_card = MetricCard(
            self.grid_frame,
            "Total Customers",
            "0",
            "Waiting for data...",
            "👥",
            "#7f8c8d",
        )
        self.cust_card.grid(row=0, column=2, sticky="nsew")

        self.stock_card = MetricCard(
            self.grid_frame,
            "Low Stock Items",
            "---",
            "Checking inventory...",
            "📦",
            "#7f8c8d",
        )
        self.stock_card.grid(row=0, column=3, sticky="nsew")

        # --- 4. RECENT ACTIVITY TABLE ---
        self.table_frame = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )
        self.table_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=20)

        ctk.CTkLabel(
            self.table_frame,
            text="Recent Sales Activity",
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
            self.table_frame,
            columns=cols,
            show="headings",
            height=8,
            style="Dashboard.Treeview",
        )

        column_widths = {
            "Invoice #": 100,
            "Customer": 250,
            "Amount": 120,
            "Status": 100,
            "Date": 120,
        }
        for col in cols:
            self.recent_tree.heading(col, text=col)
            self.recent_tree.column(col, width=column_widths[col], anchor="w")

        self.recent_tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._load_dashboard_data()

    def _load_dashboard_data(self):
        if not HAS_DB or psycopg2 is None or not self.db_config:
            return
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()

            # Queries to fetch real data
            cur.execute(
                "SELECT COALESCE(SUM(total_amount), 0) FROM invoices WHERE status != 'void';"
            )
            revenue = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM invoices WHERE status = 'active';")
            orders = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM customers WHERE is_active = TRUE;")
            customers = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM parts WHERE stock_count <= trigger_amount;"
            )
            low_stock = cur.fetchone()[0]

            self.rev_card.update_value(f"₱{revenue:,.2f}")
            self.orders_card.update_value(str(orders))
            self.cust_card.update_value(str(customers))
            self.stock_card.update_value(str(low_stock))

            # Recent Sales Activity Table Population
            cur.execute("""
                SELECT i.invoice_id, c.company_name, i.total_amount, i.status, i.date_written
                FROM invoices i
                JOIN customers c ON i.customer_number = c.customer_number
                ORDER BY i.date_written DESC, i.invoice_id DESC
                LIMIT 10;
            """)
            recent_sales = cur.fetchall()

            for row in self.recent_tree.get_children():
                self.recent_tree.delete(row)

            for row in recent_sales:
                inv_id, cust_name, amt, status, d_written = row
                self.recent_tree.insert(
                    "",
                    "end",
                    values=(
                        f"INV-{inv_id}",
                        cust_name,
                        f"₱{amt:,.2f}",
                        status.title(),
                        d_written,
                    ),
                )

            cur.close()
            conn.close()
        except Exception as e:
            print(f"[DashboardView] Error loading dashboard data: {e}")
