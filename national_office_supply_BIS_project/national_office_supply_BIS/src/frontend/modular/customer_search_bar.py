import customtkinter as ctk
from PIL import Image
import os


class CustomerSearchBar(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        search_var,
        on_search,
        on_clear,
        on_toggle_panels=None,
        on_refresh=None,
        on_edit=None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.search_var = search_var

        # Load icon images
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "assets", "icons"
        )
        self.search_icon = self._load_icon(os.path.join(icon_path, "search.png"), 12)
        self.settings_icon = self._load_icon(
            os.path.join(icon_path, "settings.png"), 12
        )

        self.left_group = ctk.CTkFrame(self, fg_color="transparent")
        self.left_group.grid(row=0, column=0, sticky="w")

        self.search_entry = ctk.CTkEntry(
            self.left_group,
            placeholder_text="Search by ID, Company, or Contact",
            width=340,
            height=34,
            fg_color="#ffffff",  # Pure white background for the input
            border_color="#d0d7de",  # Medium grey border (visible on #f8f9fa)
            placeholder_text_color="#7f8c8d",  # Muted grey for placeholder
            text_color="#1c2128",  # Dark blue-black for typed text
            border_width=1,  # Ensure the border is rendered
            font=("Segoe UI", 12),  # Larger font for visibility
        )
        self.search_entry.grid(row=0, column=0, padx=(0, 6))

        def _sync_search_var(_event=None):
            if self.search_var is not None:
                self.search_var.set(self.search_entry.get())

        def _run_search(_event=None):
            _sync_search_var()
            on_search()

        def _run_clear():
            self.search_entry.delete(0, "end")
            if self.search_var is not None:
                self.search_var.set("")
            on_clear()

        self.search_entry.bind("<KeyRelease>", _sync_search_var)
        self.search_entry.bind("<Return>", _run_search)

        self.search_btn = ctk.CTkButton(
            self.left_group,
            image=self.search_icon,
            text="",
            width=34,
            height=34,
            command=_run_search,
            fg_color="#3498db",
            hover_color="#2980b9",
        )
        self.search_btn.grid(row=0, column=1, padx=(0, 6))

        self.filter_btn = ctk.CTkButton(
            self.left_group,
            image=self.settings_icon,
            text="",
            width=34,
            height=34,
            command=on_search,
            fg_color="#e8eef5",
            hover_color="#d7e3f0",
            text_color="#2c3e50",
        )
        self.filter_btn.grid(row=0, column=2, padx=(0, 6))

        self.clear_btn = ctk.CTkButton(
            self.left_group,
            text="✕",
            width=34,
            height=34,
            fg_color="#e8eef5",
            hover_color="#d7e3f0",
            text_color="#2c3e50",
            command=_run_clear,
        )
        self.clear_btn.grid(row=0, column=3)

        self.right_group = ctk.CTkFrame(self, fg_color="transparent")
        self.right_group.grid(row=0, column=1, sticky="e")

        if on_refresh is not None:
            self.refresh_btn = ctk.CTkButton(
                self.right_group,
                text="↻",
                width=34,
                height=34,
                command=on_refresh,
                fg_color="#e8eef5",
                hover_color="#d7e3f0",
                text_color="#2c3e50",
                font=("Segoe UI", 16, "bold"),
            )
            self.refresh_btn.pack(side="left", padx=(0, 6))

        if on_edit is not None:
            self.edit_btn = ctk.CTkButton(
                self.right_group,
                text="✎",
                width=34,
                height=34,
                command=on_edit,
                fg_color="#fff4e6",
                hover_color="#ffe6c7",
                text_color="#a35d00",
            )
            self.edit_btn.pack(side="left", padx=(0, 6))

        if on_toggle_panels is not None:
            # Toggle-style button: shows expand/collapse state and updates appearance
            self._panel_visible = True

            self.add_new_btn = ctk.CTkButton(
                self.right_group,
                text="◀",
                width=34,
                height=34,
                command=on_toggle_panels,
                fg_color="#2b9430",
                hover_color="#1c7421",
                font=("Segoe UI", 14, "bold"),
            )
            self.add_new_btn.pack(side="left")

            def _update_button(visible: bool):
                # When panel is visible, show a left arrow to indicate collapse
                if visible:
                    self.add_new_btn.configure(text="▶", fg_color="#2b9430")
                else:
                    # When hidden, show a right arrow to indicate expand
                    self.add_new_btn.configure(text="◀", fg_color="#27ae60")

            def set_toggle_state(v: bool):
                self._panel_visible = v
                _update_button(v)

            self.set_toggle_state = set_toggle_state

    def _load_icon(self, icon_path: str, size: int):
        """Load a PNG icon and convert to CTkImage."""
        try:
            if os.path.exists(icon_path):
                img = Image.open(icon_path).convert("RGBA")
                img = img.resize((size, size), Image.Resampling.LANCZOS)
                return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
        except Exception as e:
            print(f"Error loading icon {icon_path}: {e}")
        return None