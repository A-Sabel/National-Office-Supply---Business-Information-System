import customtkinter as ctk


class ReportsSidebar(ctk.CTkFrame):
    def __init__(self, parent, sections, on_select):
        super().__init__(
            parent,
            fg_color="#ffffff",
            corner_radius=10,
            border_width=1,
            border_color="#e5e7eb",
            width=230,
        )
        self.grid_propagate(False)
        self._on_select = on_select
        self._buttons = {}
        self._active_key = None  # Track currently active section

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Reports",
            font=("Segoe UI", 18, "bold"),
            text_color="#1f2937",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 10))

        ctk.CTkLabel(
            self,
            text="Choose a section",
            font=("Segoe UI", 11),
            text_color="#6b7280",
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 12))

        for idx, (key, label) in enumerate(sections, start=2):
            btn = ctk.CTkButton(
                self,
                text=label,
                height=34,
                anchor="w",
                corner_radius=7,
                fg_color="#f3f4f6",
                hover_color="#e5e7eb",
                text_color="#374151",
                font=("Segoe UI", 11, "bold"),
                command=lambda k=key: self._select_section(k),
            )
            btn.grid(row=idx, column=0, sticky="ew", padx=10, pady=(0, 7))
            self._buttons[key] = btn

    def _select_section(self, key):
        """Select a section; clicking the same item keeps it selected."""
        self._on_select(key)
        self._active_key = key
        self._update_button_states()

    def _update_button_states(self):
        """Update visual state of all buttons based on active section."""
        for section_key, btn in self._buttons.items():
            if section_key == self._active_key:
                btn.configure(
                    fg_color="#dbeafe",
                    hover_color="#cfe2ff",
                    text_color="#1d4ed8",
                    border_width=1,
                    border_color="#7dd3fc",
                )
            else:
                btn.configure(
                    fg_color="#f3f4f6",
                    hover_color="#e5e7eb",
                    text_color="#374151",
                    border_width=0,
                )

    def set_active(self, key):
        """External method to set active section (updates internal state)."""
        self._active_key = key
        self._update_button_states()
