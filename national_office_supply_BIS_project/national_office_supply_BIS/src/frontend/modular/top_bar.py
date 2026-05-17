import customtkinter as ctk
from frontend.modular.alert_dropdown import AlertDropdown
from frontend.modular.profile_overlay import ProfileOverlay


class TopBar(ctk.CTkFrame):
    def __init__(self, parent, role="Staff"):
        super().__init__(
            parent, fg_color="#ffffff", height=50, corner_radius=0, border_width=0
        )
        self.parent = parent

        # --- INITIALIZATION ---
        self.profile_popup = None
        self.profile_pinned = False
        self._profile_timer = None

        self.dropdown = None
        self.alerts_pinned = False
        self._alert_timer = None

        self.right_container = ctk.CTkFrame(self, fg_color="transparent")
        self.right_container.pack(side="right", padx=15)

        # --- 1. PROFILE BUTTON (Peek & Pin) ---
        self.avatar_btn = ctk.CTkButton(
            self.right_container,
            text="👤",
            font=("Segoe UI", 20),
            width=35,
            height=35,
            fg_color="transparent",
            text_color="#2c3e50",
            hover_color="#f0f0f0",
        )
        self.avatar_btn.pack(side="right", padx=(5, 10))
        self.avatar_btn.bind("<Enter>", lambda e: self.on_profile_hover())
        self.avatar_btn.bind("<Leave>", lambda e: self.start_profile_timer())
        self.avatar_btn.configure(command=self.toggle_profile_pin)

        # Dynamic Role Label (display mapping: show 'Regular' for internal 'Hourly')
        role_display = "Regular" if role == "Hourly" else role
        self.role_label = ctk.CTkLabel(
            self.right_container,
            text=role_display,
            font=("Segoe UI", 12, "bold"),
            text_color="#7f8c8d",
        )
        self.role_label.pack(side="right", padx=5)

        # --- 2. NOTIFICATION BUTTON (Peek & Pin) ---
        self.btn_frame = ctk.CTkFrame(self.right_container, fg_color="transparent")
        self.btn_frame.pack(side="right", padx=10)

        self.notif_btn = ctk.CTkButton(
            self.btn_frame,
            text="🔔",
            width=28,
            height=28,
            fg_color="transparent",
            text_color="#7f8c8d",
            hover_color="#f0f0f0",
        )
        self.notif_btn.pack(side="right", padx=2)
        self.notif_btn.bind("<Enter>", lambda e: self.on_alert_hover())
        self.notif_btn.bind("<Leave>", lambda e: self.start_alert_timer())
        self.notif_btn.configure(command=self.toggle_alert_pin)

        ctk.CTkButton(
            self.btn_frame,
            text="⚙️",
            width=28,
            height=28,
            fg_color="transparent",
            text_color="#7f8c8d",
            hover_color="#f0f0f0",
        ).pack(side="right", padx=2)

    # --- ALERT LOGIC ---
    def on_alert_hover(self):
        self.cancel_alert_timer()
        if not self.dropdown:
            self.show_alerts(pinned=False)

    def toggle_alert_pin(self):
        self.alerts_pinned = not self.alerts_pinned
        if self.alerts_pinned:
            self.show_alerts(pinned=True)
        else:
            self.hide_alerts(force=True)

    def show_alerts(self, pinned=False):
        self.cancel_alert_timer()
        if self.dropdown:
            self.dropdown.destroy()

        # Provide controller so AlertDropdown can use DB-backed audit logs
        sample_alerts = [
            {"msg": "Inventory: Bond Paper low stock", "type": "critical"},
            {"msg": "Payroll: 2 pending approvals", "type": "warning"},
        ]

        self.dropdown = AlertDropdown(
            self.parent, controller=self.parent, alerts=sample_alerts
        )
        # Positioned closer to the bell icon (x=-80)
        self.dropdown.place(relx=1.0, y=55, x=-80, anchor="ne")

        self.dropdown.bind("<Enter>", lambda e: self.cancel_alert_timer())
        self.dropdown.bind("<Leave>", lambda e: self.start_alert_timer())

    def start_alert_timer(self):
        if not self.alerts_pinned:
            if self._alert_timer:
                self.after_cancel(self._alert_timer)
            self._alert_timer = self.after(300, self.hide_alerts)

    def hide_alerts(self, force=False):
        if self.dropdown and (force or not self.alerts_pinned):
            self.dropdown.destroy()
            self.dropdown = None

    def cancel_alert_timer(self):
        if self._alert_timer:
            self.after_cancel(self._alert_timer)
            self._alert_timer = None

    # --- PROFILE LOGIC (Restored & Fixed) ---
    def on_profile_hover(self):
        self.cancel_profile_timer()
        if not self.profile_popup:
            self.show_profile(pinned=False)

    def toggle_profile_pin(self):
        self.profile_pinned = not self.profile_pinned
        if self.profile_pinned:
            self.show_profile(pinned=True)
        else:
            self.hide_profile(force=True)

    def show_profile(self, pinned=False):
        if hasattr(self, "profile_popup") and self.profile_popup:
            self.profile_popup.destroy()

        from frontend.modular.profile_overlay import ProfileOverlay

        self.profile_popup = ProfileOverlay(
            self.parent,
            controller=self.parent,
            session=self.parent.session,
            db_config=self.parent.db_config,  # <--- Add this line
            is_pinned=pinned,
        )
        self.profile_popup.place(relx=0.98, rely=0.12, anchor="ne")
        if not pinned:
            self.profile_popup.bind("<Leave>", lambda e: self.hide_profile())

    def start_profile_timer(self):
        if not self.profile_pinned:
            if self._profile_timer:
                self.after_cancel(self._profile_timer)
            self._profile_timer = self.after(300, self.hide_profile)

    def hide_profile(self, force=False):
        if self.profile_popup and (force or not self.profile_pinned):
            self.profile_popup.destroy()
            self.profile_popup = None

    def cancel_profile_timer(self):
        if self._profile_timer:
            self.after_cancel(self._profile_timer)
            self._profile_timer = None
