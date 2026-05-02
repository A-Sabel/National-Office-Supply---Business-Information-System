import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
import customtkinter as ctk
from frontend.modular.navigation_bar import NavigationSidebar

class NationalOfficeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("National Office Supplies Management System")
        self.geometry("1100x700")
        
        # Set the current user role (this would normally come from login.py)
        self.current_role = "Manager" 

        # Layout Containers
        # Pass the role to the sidebar for RBAC filtering
        self.sidebar = NavigationSidebar(self, self, role=self.current_role)
        self.sidebar.pack(side="left", fill="y")

        self.container = ctk.CTkFrame(self, bg_color="#ecf0f1")
        self.container.pack(side="right", expand=True, fill="both")

        self.show_dashboard()

    def _clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self._clear_container()
        tk.Label(self.container, text="Dashboard View", font=("Segoe UI", 18)).pack(pady=20)

    def show_orders(self):
        self._clear_container()
        tk.Label(self.container, text="Orders Management", font=("Segoe UI", 18)).pack(pady=20)

    def show_inventory(self):
        self._clear_container()
        tk.Label(self.container, text="Inventory View", font=("Segoe UI", 18)).pack(pady=20)

    def show_customers(self):
        self._clear_container()
        tk.Label(self.container, text="Customer Management", font=("Segoe UI", 18)).pack(pady=20)

    def show_payroll(self):
        self._clear_container()
        tk.Label(self.container, text="Payroll System (Manager Only)", font=("Segoe UI", 18)).pack(pady=20)

    def show_reports(self):
        self._clear_container()
        tk.Label(self.container, text="Business Reports (Manager Only)", font=("Segoe UI", 18)).pack(pady=20)

    def logout(self):
        self.destroy()

if __name__ == "__main__":
    app = NationalOfficeApp()
    app.mainloop()