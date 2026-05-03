import customtkinter as ctk

class AlertDropdown(ctk.CTkFrame):
    def __init__(self, parent, alerts=None):
        # Slim, floating design with a border to distinguish it from the background
        super().__init__(parent, fg_color="#ffffff", corner_radius=12, 
                         border_width=1, border_color="#e0e0e0", width=300)
        
        self.alerts = alerts if alerts else []
        
        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(self.header, text="Notifications", 
                     font=("Segoe UI", 14, "bold"), text_color="#2c3e50").pack(side="left")
        
        ctk.CTkLabel(self.header, text=f"{len(self.alerts)} New", 
                     font=("Segoe UI", 11), text_color="#3498db").pack(side="right")

        # Alert List Container
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", height=250)
        self.list_frame.pack(fill="x", padx=5, pady=5)

        if not self.alerts:
            ctk.CTkLabel(self.list_frame, text="No new alerts", 
                         font=("Segoe UI", 12, "italic"), text_color="#7f8c8d").pack(pady=20)
        else:
            for alert in self.alerts:
                self._add_item(alert)

        # Footer
        ctk.CTkButton(self, text="Mark all as read", font=("Segoe UI", 11),
                      fg_color="transparent", text_color="#7f8c8d", 
                      hover_color="#f0f0f0", height=30).pack(fill="x", pady=10)

    def _add_item(self, alert_data):
        """Adds an individual alert row"""
        item = ctk.CTkFrame(self.list_frame, fg_color="#f8f9fa", corner_radius=8)
        item.pack(fill="x", pady=2, padx=5)

        # Indicator dot based on urgency
        color = "#e74c3c" if alert_data['type'] == 'critical' else "#f39c12"
        
        dot = ctk.CTkLabel(item, text="•", text_color=color, font=("Segoe UI", 24))
        dot.pack(side="left", padx=(10, 5))

        msg = ctk.CTkLabel(item, text=alert_data['msg'], font=("Segoe UI", 11),
                           text_color="#2c3e50", wraplength=200, justify="left")
        msg.pack(side="left", pady=10, padx=5)