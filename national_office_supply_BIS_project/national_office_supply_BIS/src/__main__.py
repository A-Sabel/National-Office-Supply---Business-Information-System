import sys
import os
import customtkinter as ctk
from frontend.modular.navigation_bar import NavigationSidebar
from frontend.modular.top_bar import TopBar
from frontend.tabs.dashboard import DashboardView

class NationalOfficeApp(ctk.CTk):
    def __init__(self, role="Manager"):
        super().__init__()
        # Ensure the base window matches the sidebar/dashboard to hide gaps
        self.configure(fg_color="#ffffff") 
        self.title("National Office Supplies BIS")
        self.geometry("1200x800")

        # 1. Setup Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0) # TopBar
        self.grid_rowconfigure(1, weight=1) # Content

        # 2. Sidebar
        self.sidebar = NavigationSidebar(self, self, role=role)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        # 3. Top Bar
        self.top_bar = TopBar(self, role=role)
        self.top_bar.grid(row=0, column=1, sticky="ew")
        
        # 4. Content Container (DEFINED BEFORE USE)
        self.content_container = ctk.CTkFrame(self, fg_color="#f8f9fa", border_width=0)
        self.content_container.grid(row=1, column=1, sticky="nsew")
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        # 5. Load the Dashboard
        self.show_dashboard("Andrea Ysabela", role)

    def show_dashboard(self, username, role):
        self._clear_content()
        self.current_view = DashboardView(self.content_container, self, username=username, role=role)
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def _clear_content(self):
        for widget in self.content_container.winfo_children():
            widget.destroy()

    # --- Navigation Placeholders ---
    def show_customers(self): print("Navigation: Customers")
    def show_orders(self): print("Navigation: Orders")
    def show_inventory(self): print("Navigation: Inventory")
    def show_payroll(self): print("Navigation: Payroll")
    def show_reports(self): print("Navigation: Reports")
    def logout(self): self.destroy()

if __name__ == "__main__":
    # You can change "Manager" here to test the dynamic role
    app = NationalOfficeApp(role="Manager")
    app.mainloop()