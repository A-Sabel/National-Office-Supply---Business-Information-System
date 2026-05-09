import sys
import os
import customtkinter as ctk
from frontend.modular.navigation_bar import NavigationSidebar
from frontend.modular.top_bar import TopBar
from frontend.tabs.dashboard import DashboardView
from frontend.tabs.customers import CustomersView
from frontend.tabs.inventory import InventoryView
from frontend.tabs.orders_and_invoices import OrdersView
from frontend.tabs.reports_tab.reports import DBConfig, ReportsHubView

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class NationalOfficeApp(ctk.CTk):
    def __init__(self, role="Manager"):
        super().__init__()
        self.role = role
        self.username = "Andrea Ysabela"
        # Ensure the base window matches the sidebar/dashboard to hide gaps
        self.configure(fg_color="#ffffff")
        self.title("National Office Supplies BIS")
        self.geometry("1200x800")

        # 1. Setup Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)  # TopBar
        self.grid_rowconfigure(1, weight=1)  # Content

        # 2. Sidebar
        self.sidebar = NavigationSidebar(self, self, role=role)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")

        # 3. Top Bar
        self.top_bar = TopBar(self, role=role)
        self.top_bar.grid(row=0, column=1, sticky="ew")

        # 4. Content Container
        self.content_container = ctk.CTkFrame(self, fg_color="#f8f9fa", border_width=0)
        self.content_container.grid(row=1, column=1, sticky="nsew")
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        # 5. Load the Dashboard
        self.show_dashboard(self.username, self.role)

    def _clear_content(self):
        for widget in self.content_container.winfo_children():
            widget.destroy()

    def show_dashboard(self, username=None, role=None):
        self._clear_content()
        if username is None:
            username = self.username
        if role is None:
            role = self.role
        self.current_view = DashboardView(
            self.content_container, self, username=username, role=role
        )
        self.current_view.grid(row=0, column=0, sticky="nsew")

    # --- Navigation Methods ---

    def show_customers(self):
        self._clear_content()
        db_config = {
            "dbname": "nos_customerdb",
            "user": "postgres",
            "password": "maomao220",
            "host": "localhost",
            "port": 5432,
        }
        self.current_view = CustomersView(self.content_container, self, db_config)
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_orders(self):
        self._clear_content()
        db_config = {
            "dbname": "databasename_here",  # Update with your actual database name
            "user": "postgres",
            "password": "your_password_here",  # Update with your actual password
            "host": "localhost",
            "port": 5432,
        }
        self.current_view = OrdersView(
            self.content_container, controller=self, db_config=db_config
        )
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_inventory(self):
        self._clear_content()
        db_config = {
            "dbname": "nos_stockdb",
            "user": "postgres",
            "password": "maomao220",
            "host": "localhost",
            "port": 5432,
        }
        self.current_view = InventoryView(
            self.content_container, controller=self, db_config=db_config
        )
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_reports(self):
        self._clear_content()
        # Updated to your nos_stockdb
        db_config: DBConfig = {
            "dbname": "nos_stockdb",
            "user": "postgres",
            "password": "maomao220",
            "host": "localhost",
            "port": 5432,
        }
        self.current_view = ReportsHubView(
            self.content_container, controller=self, db_config=db_config
        )
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_payroll(self):
        # Added this method to prevent the sidebar from crashing the app
        print("Navigation: Payroll")

    def logout(self):
        self.destroy()


if __name__ == "__main__":
    app = NationalOfficeApp(role="Manager")
    app.mainloop()
