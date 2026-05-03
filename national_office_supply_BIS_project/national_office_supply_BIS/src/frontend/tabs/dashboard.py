import customtkinter as ctk
from frontend.modular.metric_card import MetricCard

class DashboardView(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller, username="User", role="Staff"):
        # Removing border_width here is usually enough to stop the line
        super().__init__(parent, fg_color="#f8f9fa", corner_radius=0, border_width=0)
        self.controller = controller
        
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
            text_color="#2c3e50"
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
        self.rev_card = MetricCard(self.grid_frame, "Total Revenue", "$---", "Waiting for data...", "💰", "#7f8c8d")
        self.rev_card.grid(row=0, column=0, sticky="nsew")

        self.orders_card = MetricCard(self.grid_frame, "Active Orders", "0", "Waiting for data...", "🛒", "#7f8c8d")
        self.orders_card.grid(row=0, column=1, sticky="nsew")

        self.cust_card = MetricCard(self.grid_frame, "Total Customers", "0", "Waiting for data...", "👥", "#7f8c8d")
        self.cust_card.grid(row=0, column=2, sticky="nsew")

        self.stock_card = MetricCard(self.grid_frame, "Low Stock Items", "---", "Checking inventory...", "📦", "#7f8c8d")
        self.stock_card.grid(row=0, column=3, sticky="nsew")

        # --- 4. RECENT ACTIVITY TABLE ---
        self.table_frame = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12, border_width=1, border_color="#e0e0e0")
        self.table_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=20, ipady=80)
        
        ctk.CTkLabel(self.table_frame, text="Recent Sales Activity", 
                     font=("Segoe UI", 16, "bold"), text_color="#2c3e50").pack(anchor="w", padx=20, pady=15)
        
        ctk.CTkLabel(self.table_frame, text="Connect PostgreSQL to populate this table...", 
                     font=("Segoe UI", 12, "italic"), text_color="#7f8c8d").pack(expand=True)