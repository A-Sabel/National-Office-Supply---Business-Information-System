import customtkinter as ctk


class MetricCard(ctk.CTkFrame):
    def __init__(self, parent, title, value, subtext, icon_text="📊", color="#3498db"):
        super().__init__(
            parent,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )

        # Header Row
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=15, pady=(15, 0))

        ctk.CTkLabel(self.header, text=icon_text, font=("Segoe UI", 20)).pack(
            side="left"
        )
        ctk.CTkLabel(
            self.header, text=title, font=("Segoe UI", 13, "bold"), text_color="#7f8c8d"
        ).pack(side="left", padx=10)

        # Value & Subtext
        self.value_label = ctk.CTkLabel(
            self, text=value, font=("Segoe UI", 24, "bold"), text_color="#2c3e50"
        )
        self.value_label.pack(anchor="w", padx=15, pady=(5, 0))
        ctk.CTkLabel(self, text=subtext, font=("Segoe UI", 11), text_color=color).pack(
            anchor="w", padx=15, pady=(0, 15)
        )

    def update_value(self, new_value):
        self.value_label.configure(text=str(new_value))
