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


class ProgressMetricCard(ctk.CTkFrame):
    """Metric card with a progress bar for tracking towards a goal."""

    def __init__(
        self,
        parent,
        title,
        value,
        progress_pct,
        icon_text="📊",
        color="#3498db",
        goal_text="",
    ):
        super().__init__(
            parent,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )

        # Header Row
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=15, pady=(12, 0))

        ctk.CTkLabel(self.header, text=icon_text, font=("Segoe UI", 20)).pack(
            side="left"
        )
        ctk.CTkLabel(
            self.header, text=title, font=("Segoe UI", 13, "bold"), text_color="#7f8c8d"
        ).pack(side="left", padx=10)

        # Value Label (compact)
        self.value_label = ctk.CTkLabel(
            self, text=value, font=("Segoe UI", 24, "bold"), text_color="#2c3e50"
        )
        self.value_label.pack(anchor="w", padx=15, pady=(3, 0))

        # Goal/Target Text (compact)
        self.goal_label = ctk.CTkLabel(
            self, text=goal_text, font=("Segoe UI", 10), text_color=color
        )
        self.goal_label.pack(anchor="w", padx=15, pady=(0, 6))

        # Progress Bar (more compact)
        self.progress_bar_bg = ctk.CTkProgressBar(
            self,
            height=6,
            fg_color="#ecf0f1",
            progress_color="#3498db",
            corner_radius=3,
        )
        self.progress_bar_bg.pack(fill="x", padx=15, pady=(0, 12))
        self.progress_bar_bg.set(0)

    def update_value(self, new_value):
        self.value_label.configure(text=str(new_value))

    def update_goal(self, goal_text):
        """Update the goal/target text."""
        self.goal_label.configure(text=goal_text)

    def update_progress(self, progress_pct):
        """Update the progress bar fill. progress_pct should be 0-100."""
        pct = max(0, min(100, progress_pct)) / 100.0
        self.progress_bar_bg.set(pct)
