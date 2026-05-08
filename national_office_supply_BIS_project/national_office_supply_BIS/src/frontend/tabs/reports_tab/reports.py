"""
reports.py
National Office Supplies BIS — Reports Hub
Modular reports interface with dedicated sections for various analytics.

Sections:
  1. Weekly Sales Report (QD-Sec7, 9, 12) — imported from weekly_sales.py
  2. Inventory Report (QD-Sec3, 4, 5) — placeholder
  3. Stock Ordering Report (QD-Sec6, 13) — placeholder
  4. Customer List & Balances — placeholder
  5. Customer Payment History — placeholder
"""

import customtkinter as ctk
from typing import TypedDict

from frontend.tabs.reports_tab.weekly_sales import WeeklySalesReportView
from frontend.tabs.reports_tab.stock_ordering import StockOrderingReportView
from frontend.modular.reports_sidebar import ReportsSidebar
from frontend.tabs.reports_tab.inventory_report import InventorySalesReportView


class DBConfig(TypedDict):
    dbname: str
    user: str
    password: str
    host: str
    port: int


class ReportsHubView(ctk.CTkFrame):
    """Reports hub container with sidebar navigation and section panels."""

    SECTIONS = [
        ("inventory_report", "Inventory Report"),
        ("weekly_sales", "Weekly Sales Report"),
        ("stock_ordering", "Stock Ordering Report"),
        ("customer_balances", "Customer List & Balances"),
        ("customer_payments", "Customer Payment History"),
    ]

    META = {
        "inventory_report": {
            "subtitle": "QD-Sec3, 4, 5",
            "description": "Inventory status, movement trends, and item-level insights.",
        },
        "weekly_sales": {
            "subtitle": "Total sales, metrics, and rep filtering - QD-Sec7, 9, 12",
            "description": "Interactive weekly performance dashboard for sales reps.",
        },
        "stock_ordering": {
            "subtitle": "QD-Sec6, 13",
            "description": "Reorder recommendations, shortages, and ordering summary.",
        },
        "customer_balances": {
            "subtitle": "Customer receivables snapshot",
            "description": "Outstanding balances by customer with status grouping.",
        },
        "customer_payments": {
            "subtitle": "Tracking changes and payments - Point 1",
            "description": "Payment timeline, amount changes, and audit trail snapshots.",
        },
    }

    def __init__(self, parent, controller=None, db_config: DBConfig | None = None):
        super().__init__(parent, fg_color="#f8f9fa")
        self.controller = controller
        self.db_config = db_config
        self._section_frames = {}
        self._active_key = None
        self._sidebar_visible = True

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left sidebar with section buttons
        self.sidebar = ReportsSidebar(
            self,
            sections=self.SECTIONS,
            on_select=self.show_section,
        )
        self.sidebar.grid(row=0, column=0, sticky="ns", padx=(12, 10), pady=12)

        # Right panel for content
        self.content_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.content_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=12)
        self.content_panel.grid_columnconfigure(0, weight=1)
        self.content_panel.grid_rowconfigure(0, weight=1)

        self.view_host = ctk.CTkFrame(self.content_panel, fg_color="transparent")
        self.view_host.grid(row=0, column=0, sticky="nsew")
        self.view_host.grid_columnconfigure(0, weight=1)
        self.view_host.grid_rowconfigure(0, weight=1)

        # Show welcome state initially
        self.show_section(None)

    def toggle_navigation(self):
        """Hide or unhide the reports navigation sidebar."""
        if self._sidebar_visible:
            self.sidebar.grid_remove()
            self._sidebar_visible = False
        else:
            self.sidebar.grid(row=0, column=0, sticky="ns", padx=(12, 10), pady=12)
            self._sidebar_visible = True

        weekly_view = self._section_frames.get("weekly_sales")
        if weekly_view is not None and hasattr(
            weekly_view, "set_navigation_visibility"
        ):
            weekly_view.set_navigation_visibility(self._sidebar_visible)

    def show_section(self, section_key: str | None):
        """Show the requested report section, creating if needed.
        If section_key is None, show welcome/empty state."""
        # Hide all existing frames
        for frame in self._section_frames.values():
            frame.grid_remove()

        # If None (toggled off), show empty state
        if section_key is None:
            if "welcome" not in self._section_frames:
                self._section_frames["welcome"] = self._create_welcome_state()
            self._section_frames["welcome"].grid(row=0, column=0, sticky="nsew")
            self._active_key = None
            self.sidebar.set_active(None)
            return

        # Create or show the requested section
        if section_key not in self._section_frames:
            self._section_frames[section_key] = self._create_section_view(section_key)

        self._section_frames[section_key].grid(row=0, column=0, sticky="nsew")
        self._active_key = section_key
        self.sidebar.set_active(section_key)

    def _create_welcome_state(self) -> ctk.CTkScrollableFrame:
        """Create a welcome/empty state shown when no section is selected."""
        frame = ctk.CTkScrollableFrame(self.view_host, fg_color="#f0f2f5")

        container = ctk.CTkFrame(frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28, pady=28)

        inner = ctk.CTkFrame(container, fg_color="transparent")
        inner.pack(fill="both", expand=True)

        ctk.CTkLabel(
            inner,
            text="📊",
            font=("Segoe UI", 64),
        ).pack(pady=(40, 20))

        ctk.CTkLabel(
            inner,
            text="Reports Dashboard",
            font=("Segoe UI", 28, "bold"),
            text_color="#1a1f2e",
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            inner,
            text="Select a report from the sidebar to get started",
            font=("Segoe UI", 13),
            text_color="#8a94a6",
        ).pack(pady=(0, 40))

        ctk.CTkLabel(
            inner,
            text="Available Reports:",
            font=("Segoe UI", 12, "bold"),
            text_color="#374151",
        ).pack(anchor="w", pady=(0, 12))

        for key, label in self.SECTIONS:
            meta = self.META.get(key, {})
            frame_item = ctk.CTkFrame(
                inner,
                fg_color="#ffffff",
                corner_radius=8,
                border_width=1,
                border_color="#e8eaed",
            )
            frame_item.pack(fill="x", pady=(0, 8))

            title = ctk.CTkLabel(
                frame_item,
                text=label,
                font=("Segoe UI", 11, "bold"),
                text_color="#1f2937",
            )
            title.pack(anchor="w", padx=12, pady=(8, 2))

            ctk.CTkLabel(
                frame_item,
                text=meta.get("subtitle", ""),
                font=("Segoe UI", 10),
                text_color="#6b7280",
            ).pack(anchor="w", padx=12, pady=(0, 8))

        return frame

    def _create_section_view(
        self, section_key: str
    ) -> ctk.CTkScrollableFrame | ctk.CTkFrame:
        """Factory method to create views for each section."""
        if section_key == "weekly_sales":
            return WeeklySalesReportView(
                self.view_host,
                controller=self.controller,
                db_config=self.db_config,
                on_toggle_navigation=self.toggle_navigation,
                is_navigation_visible=self._sidebar_visible,
            )
        elif section_key == "inventory_report":
            return InventorySalesReportView(
                self.view_host,
                controller=self.controller,
                db_config=self.db_config,
                on_toggle_navigation=self.toggle_navigation,
                is_navigation_visible=self._sidebar_visible,
            )
        elif section_key == "stock_ordering":
            return StockOrderingReportView(
                self.view_host,
                controller=self.controller,
                db_config=self.db_config,
            )
        elif section_key == "customer_balances":
            return self._create_placeholder("Customer List & Balances", section_key)
        elif section_key == "customer_payments":
            return self._create_placeholder("Customer Payment History", section_key)
        else:
            return self._create_placeholder("Unknown Section", section_key)

    def _create_placeholder(
        self, title: str, section_key: str
    ) -> ctk.CTkScrollableFrame:
        """Create a placeholder frame for unimplemented sections."""
        frame = ctk.CTkScrollableFrame(self.view_host, fg_color="#f0f2f5")

        container = ctk.CTkFrame(frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28, pady=28)

        # Title
        ctk.CTkLabel(
            container,
            text=title,
            font=("Segoe UI", 26, "bold"),
            text_color="#1a1f2e",
        ).pack(anchor="w", pady=(0, 4))

        # Subtitle
        meta = self.META.get(section_key, {})
        ctk.CTkLabel(
            container,
            text=meta.get("subtitle", ""),
            font=("Segoe UI", 11),
            text_color="#8a94a6",
        ).pack(anchor="w", pady=(0, 16))

        # Placeholder message
        placeholder_frame = ctk.CTkFrame(
            container,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e8eaed",
        )
        placeholder_frame.pack(fill="both", expand=True, pady=(20, 0))

        inner = ctk.CTkFrame(placeholder_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=40, pady=60)

        ctk.CTkLabel(
            inner,
            text="🚀",
            font=("Segoe UI", 48),
        ).pack(pady=(0, 16))

        ctk.CTkLabel(
            inner,
            text=f"{title} — Coming Soon",
            font=("Segoe UI", 18, "bold"),
            text_color="#1a1f2e",
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            inner,
            text=meta.get("description", "This section is under development."),
            font=("Segoe UI", 11),
            text_color="#8a94a6",
            wraplength=400,
        ).pack()

        return frame