"""Audit log report view for sensitive application actions."""

from __future__ import annotations

import csv
from datetime import datetime
import tkinter as tk
import tkinter.filedialog as fd
import tkinter.messagebox as messagebox
from tkinter import ttk

import customtkinter as ctk
import psycopg2

from backend.audit_logger import ensure_audit_log_table
from backend.report_service import ReportService
from .csv_tab import export_audit_log

BG_PAGE = "#f0f2f5"
BG_CARD = "#ffffff"
BORDER = "#e0e0e0"
TEXT_DARK = "#2c3e50"
TEXT_MUTED = "#7f8c8d"
ACCENT_BLUE = "#3498db"
ACCENT_GREEN = "#2ecc71"


class AuditLogReportView(ctk.CTkFrame):
    """Read-only audit report with filter controls and CSV export."""

    def __init__(
        self,
        parent,
        controller=None,
        db_config=None,
        on_toggle_navigation=None,
        is_navigation_visible=True,
        **kwargs,
    ):
        super().__init__(
            parent, fg_color=BG_PAGE, corner_radius=0, border_width=0, **kwargs
        )
        self.controller = controller
        self.db_config = db_config
        self._report_service = ReportService(
            self.db_config or {}, getattr(controller, "session_manager", None)
        )
        self._rows: list[dict] = []
        self._on_toggle_navigation = on_toggle_navigation
        self._is_navigation_visible = is_navigation_visible
        self._nav_toggle_btn = None

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_table()
        self._load_logs()

    def set_navigation_visibility(self, visible: bool):
        self._is_navigation_visible = visible
        if self._nav_toggle_btn is not None:
            self._nav_toggle_btn.configure(text="◀" if visible else "▶")

    def _handle_nav_toggle(self):
        if self._on_toggle_navigation:
            self._on_toggle_navigation()

    def _build_header(self):
        hdr = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        hdr.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        hdr.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(hdr, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 2))

        self._nav_toggle_btn = ctk.CTkButton(
            title_row,
            text="◀" if self._is_navigation_visible else "▶",
            width=30,
            height=30,
            corner_radius=8,
            fg_color="#2f9e44",
            hover_color="#2b8a3e",
            text_color="white",
            border_width=0,
            font=("Segoe UI", 12, "bold"),
            command=self._handle_nav_toggle,
        )
        self._nav_toggle_btn.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            title_row,
            text="Audit Log",
            font=("Segoe UI", 22, "bold"),
            text_color=TEXT_DARK,
        ).pack(side="left")

        subtitle = ctk.CTkLabel(
            hdr,
            text="Sensitive actions only: price changes, payroll issuance, invoice shipments, balance updates.",
            font=("Segoe UI", 11),
            text_color=TEXT_MUTED,
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 10))

        filter_row = ctk.CTkFrame(hdr, fg_color="transparent")
        filter_row.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        for idx in range(6):
            filter_row.grid_columnconfigure(idx, weight=1 if idx < 4 else 0)

        self.action_var = ctk.StringVar(value="All Actions")
        self.actor_var = ctk.StringVar()
        self.from_var = ctk.StringVar()
        self.to_var = ctk.StringVar()

        self.action_combo = ctk.CTkComboBox(
            filter_row,
            values=[
                "All Actions",
                "PRICE_UPDATE",
                "PAYROLL_ISSUED",
                "INVOICE_SHIPPED",
                "BALANCE_UPDATE",
            ],
            variable=self.action_var,
        )
        self.action_combo.grid(row=0, column=0, sticky="ew", padx=4)

        actor_entry = ctk.CTkEntry(
            filter_row, textvariable=self.actor_var, placeholder_text="Actor ID"
        )
        actor_entry.grid(row=0, column=1, sticky="ew", padx=4)

        from_entry = ctk.CTkEntry(
            filter_row, textvariable=self.from_var, placeholder_text="From YYYY-MM-DD"
        )
        from_entry.grid(row=0, column=2, sticky="ew", padx=4)

        to_entry = ctk.CTkEntry(
            filter_row, textvariable=self.to_var, placeholder_text="To YYYY-MM-DD"
        )
        to_entry.grid(row=0, column=3, sticky="ew", padx=4)

        ctk.CTkButton(
            filter_row, text="↺  Refresh",
            width=110,
            height=36,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#e8f4fd",
            text_color=ACCENT_BLUE,
            border_width=1,
            border_color=ACCENT_BLUE,
            font=("Segoe UI", 12, "bold"),
            command=self._load_logs
        ).grid(row=0, column=4, padx=4)
        ctk.CTkButton(
            filter_row,
            text="⬇  Export CSV",
            width=140,
            height=36,
            font=("Segoe UI", 12, "bold"),
            fg_color="#1e2d3d",
            hover_color="#2d3f52",
            command=self._export_csv,
            text_color="white",
        ).grid(row=0, column=5, padx=4)

    def _build_table(self):
        card = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)

        cols = (
            "timestamp",
            "action_type",
            "actor_id",
            "target_table",
            "target_id",
            "details",
        )
        self.tree = ttk.Treeview(card, columns=cols, show="headings", height=14)
        headings = {
            "timestamp": "Timestamp",
            "action_type": "Action",
            "actor_id": "Actor",
            "target_table": "Target Table",
            "target_id": "Target ID",
            "details": "Details",
        }
        widths = {
            "timestamp": 160,
            "action_type": 140,
            "actor_id": 90,
            "target_table": 120,
            "target_id": 90,
            "details": 480,
        }
        for col in cols:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        vsb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        vsb.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)

    def _ensure_table(self):
        assert self.db_config is not None
        conn = psycopg2.connect(**self.db_config)
        try:
            with conn:
                ensure_audit_log_table(conn)
        finally:
            conn.close()

    def _load_logs(self):
        if not self.db_config:
            self._rows = []
            self._render_rows([])
            return

        try:
            self._ensure_table()
            sql = """
                SELECT log_id, timestamp, action_type, actor_id, target_table, target_id, details
                FROM logs
                WHERE 1=1
            """
            params: list[object] = []

            action = self.action_var.get().strip()
            if action and action != "All Actions":
                sql += " AND action_type = %s"
                params.append(action)

            actor_text = self.actor_var.get().strip()
            if actor_text:
                sql += " AND actor_id = %s"
                params.append(int(actor_text))

            from_text = self.from_var.get().strip()
            if from_text:
                sql += " AND timestamp >= %s::date"
                params.append(from_text)

            to_text = self.to_var.get().strip()
            if to_text:
                sql += " AND timestamp < (%s::date + INTERVAL '1 day')"
                params.append(to_text)

            sql += " ORDER BY timestamp DESC, log_id DESC LIMIT 500"
            rows = self._report_service.execute_query(sql, tuple(params))
            self._rows = rows
            self._render_rows(rows)
        except Exception as e:
            messagebox.showerror("Audit Log", f"Could not load audit logs:\n{e}")

    def _render_rows(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row.get("timestamp"),
                    row.get("action_type"),
                    row.get("actor_id"),
                    row.get("target_table"),
                    row.get("target_id"),
                    row.get("details"),
                ),
            )

    def _export_csv(self):
        export_audit_log(self, self._rows)