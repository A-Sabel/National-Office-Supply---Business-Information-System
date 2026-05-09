import sys
import os
import customtkinter as ctk
from dotenv import load_dotenv

# --- ADD THESE IMPORTS ---
from utils.session import AppSession
from frontend.tabs.login import LoginView

# -------------------------

from frontend.modular.navigation_bar import NavigationSidebar
from frontend.modular.top_bar import TopBar
from frontend.tabs.dashboard import DashboardView
from frontend.tabs.customers import CustomersView
from frontend.tabs.inventory import InventoryView
from frontend.tabs.orders_and_invoices import OrdersView
from frontend.tabs.reports_tab.reports import DBConfig, ReportsHubView
from frontend.tabs.payroll import PayrollView

load_dotenv()

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class NationalOfficeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("National Office Supplies BIS")
        self.geometry("1200x800")

        # 1. Initialize DB Config
        self.db_config: DBConfig = {
            "dbname": os.getenv("DB_NAME", "postgres"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASS", ""),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 5432)),
        }

        # 2. Initialize the Global Session
        self.session = AppSession()

        # 3. Start at the Login Screen
        self.show_login()

    # ==========================================
    # APP LIFECYCLE METHODS
    # ==========================================

    def show_login(self):
        """Clears the screen and shows the login frame."""
        for widget in self.winfo_children():
            widget.destroy()

        self.login_view = LoginView(self, self)
        self.login_view.pack(fill="both", expand=True)

    def build_main_application(self):
        """Called by LoginView AFTER a successful login to build the UI."""
        # 1. Clear the login screen
        for widget in self.winfo_children():
            widget.destroy()

        # 2. Setup Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)  # TopBar
        self.grid_rowconfigure(1, weight=1)  # Content

        # 3. Sidebar (Safely uses the populated session role)
        self.sidebar = NavigationSidebar(
            self, self, role=self.session.role or "Manager"
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")

        # 4. Top Bar
        self.top_bar = TopBar(self, role=self.session.role or "Staff")
        self.top_bar.grid(row=0, column=1, sticky="ew")

        # 5. Content Container
        self.content_container = ctk.CTkFrame(self, fg_color="#f8f9fa", border_width=0)
        self.content_container.grid(row=1, column=1, sticky="nsew")
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        # 6. Load the Dashboard
        self.show_dashboard()

    def logout(self):
        """Clears session and returns to login."""
        self.session.logout()
        self.show_login()

    # ==========================================
    # NAVIGATION METHODS
    # ==========================================

    def _clear_content(self):
        for widget in self.content_container.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self._clear_content()
        self.current_view = DashboardView(
            self.content_container,
            self,
            username=self.session.employee_name or "User",
            role=self.session.role or "Staff",
            db_config=self.db_config,
        )
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_customers(self):
        self._clear_content()
        self.current_view = CustomersView(self.content_container, self, self.db_config)
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_orders(self):
        self._clear_content()
        self.current_view = OrdersView(
            self.content_container, controller=self, db_config=self.db_config
        )
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_inventory(self):
        self._clear_content()
        self.current_view = InventoryView(
            self.content_container, controller=self, db_config=self.db_config
        )
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_reports(self):
        self._clear_content()
        self.current_view = ReportsHubView(
            self.content_container, controller=self, db_config=self.db_config
        )
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_payroll(self):
        self._clear_content()
        self.current_view = PayrollView(
            self.content_container,
            controller=self,
            role=self.session.role or "Manager",
            db_config=self.db_config,
        )
        self.current_view.grid(row=0, column=0, sticky="nsew")
        

if __name__ == "__main__":
    app = NationalOfficeApp()
    app.mainloop()
