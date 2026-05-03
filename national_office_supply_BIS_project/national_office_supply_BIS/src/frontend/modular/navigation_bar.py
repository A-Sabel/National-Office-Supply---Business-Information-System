import os
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageColor

class NavigationSidebar(ctk.CTkFrame):
    def __init__(self, parent, controller, role="Manager"):
        super().__init__(parent, fg_color="#001440", width=200, corner_radius=0)
        self.controller = controller
        self.role = role
        self.is_expanded = True
        self.buttons = {}
        self.pack_propagate(False)

        # Base path for your icons
        self.icon_dir = r"national_office_supply_BIS_project\national_office_supply_BIS\src\assets\icons"

        # --- 1. TOP BAR (Toggle Button + Logo) ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", pady=(10, 20), padx=10)

        # The Toggle/Hamburger Button
        self.toggle_btn = ctk.CTkButton(self.top_frame, text="☰", width=35, height=35,
                                        fg_color="transparent", hover_color="#002a80",
                                        text_color="white", command=self.toggle_sidebar)
        self.toggle_btn.pack(side="left")

        # Logo Placement
        try:
            logo_path = r"national_office_supply_BIS_project\national_office_supply_BIS\src\assets\logo3.png"
            self.logo_image = ctk.CTkImage(light_image=Image.open(logo_path),
                                           dark_image=Image.open(logo_path),
                                           size=(100, 50))
            self.logo_label = ctk.CTkLabel(self.top_frame, image=self.logo_image, text="")
        except Exception:
            self.logo_label = ctk.CTkLabel(self.top_frame, text="NOS", text_color="white", font=("Segoe UI", 16, "bold"))
        
        self.logo_label.pack(side="left", padx=10)

        # --- 2. MENU ITEMS ---
        menu_items = [
            {"name": "Dashboard", "file": "layout-dashboard.png", "emoji": "🏠", "cmd": self.controller.show_dashboard, "roles": ["Manager", "Sales Rep"]},
            {"name": "Customers", "file": "user.png", "emoji": "👥", "cmd": self.controller.show_customers, "roles": ["Manager", "Sales Rep"]},
            {"name": "Orders", "file": "shopping-cart.png", "emoji": "🛒", "cmd": self.controller.show_orders, "roles": ["Manager", "Sales Rep"]},
            {"name": "Inventory", "file": "package.png", "emoji": "🏢", "cmd": self.controller.show_inventory, "roles": ["Manager", "Sales Rep"]},
            {"name": "Payroll", "file": "banknote.png", "emoji": "💵", "cmd": self.controller.show_payroll, "roles": ["Manager"]},
            {"name": "Reports", "file": "chart-bar-big.png", "emoji": "📈", "cmd": self.controller.show_reports, "roles": ["Manager"]}
        ]

        for item in menu_items:
            if self.role in item["roles"]:
                
                # Dynamically generate the Gray and White versions of the icon
                icon_inactive = self._load_colored_icon(item["file"], "#aeb9c4") # Gray
                icon_active = self._load_colored_icon(item["file"], "#ffffff")   # White

                if icon_inactive:
                    btn_text = f"   {item['name']}"
                    icon_kwargs = {"image": icon_inactive, "compound": "left"}
                    icon_only_text = ""
                else:
                    btn_text = f"  {item['emoji']}   {item['name']}"
                    icon_kwargs = {}
                    icon_only_text = f"  {item['emoji']}"

                btn = ctk.CTkButton(self, 
                                    text=btn_text, 
                                    anchor="w",
                                    command=lambda n=item["name"], c=item["cmd"]: self._on_click(n, c),
                                    fg_color="transparent", 
                                    text_color="#aeb9c4",
                                    hover_color="#002a80",
                                    corner_radius=8,
                                    height=45,
                                    font=("Segoe UI", 12),
                                    **icon_kwargs)
                btn.pack(fill="x", padx=10, pady=2)
                
                # Store references
                btn.full_text = btn_text
                btn.icon_only = icon_only_text
                btn.img_inactive = icon_inactive 
                btn.img_active = icon_active
                self.buttons[item["name"]] = btn

        # --- 3. LOGOUT ---
        self.logout_btn = ctk.CTkButton(self, text="  🚪   Logout", anchor="w", 
                                        command=self.controller.logout, 
                                        fg_color="transparent", hover_color="#c0392b", 
                                        text_color="#e74c3c", corner_radius=8, height=45)
        self.logout_btn.pack(side="bottom", fill="x", pady=20, padx=10)
        self.logout_btn.full_text = "  🚪   Logout"
        self.logout_btn.icon_only = "  🚪"

    # ==========================================
    # HELPER METHODS (Notice the indentation here)
    # ==========================================

    def _load_colored_icon(self, filename, hex_color):
        """Loads a transparent PNG and overlays a specific hex color onto it."""
        full_path = os.path.join(self.icon_dir, filename)
        if not os.path.exists(full_path):
            return None
            
        try:
            img = Image.open(full_path).convert("RGBA")
            rgb = ImageColor.getrgb(hex_color)
            solid_color = Image.new("RGBA", img.size, rgb)
            
            alpha_mask = img.split()[3]
            colored_img = Image.composite(solid_color, Image.new("RGBA", img.size, (0,0,0,0)), alpha_mask)
            
            return ctk.CTkImage(light_image=colored_img, size=(20, 20))
            
        except Exception as e:
            print(f"Error loading icon {filename}: {e}")
            return None

    def _on_click(self, name, command):
        self.highlight_tab(name)
        command()

    def highlight_tab(self, active_name):
        for name, btn in self.buttons.items():
            if name == active_name:
                # Active State
                btn.configure(fg_color="#3498db", text_color="white", border_width=2, border_color="#5dade2")
                if hasattr(btn, 'img_active') and btn.img_active:
                    btn.configure(image=btn.img_active)
            else:
                # Inactive State
                btn.configure(fg_color="transparent", text_color="#aeb9c4", border_width=0)
                if hasattr(btn, 'img_inactive') and btn.img_inactive:
                    btn.configure(image=btn.img_inactive)

    def toggle_sidebar(self):
        if self.is_expanded:
            self.configure(width=65)
            self.logo_label.pack_forget() 
            
            for btn in self.buttons.values():
                btn.configure(text=btn.icon_only, width=45, anchor="center")
            self.logout_btn.configure(text=self.logout_btn.icon_only, width=45, anchor="center")
            
            self.is_expanded = False
        else:
            self.configure(width=200)
            self.logo_label.pack(side="left", padx=10) 
            
            for btn in self.buttons.values():
                btn.configure(text=btn.full_text, width=180, anchor="w")
            self.logout_btn.configure(text=self.logout_btn.full_text, width=180, anchor="w")
            
            self.is_expanded = True