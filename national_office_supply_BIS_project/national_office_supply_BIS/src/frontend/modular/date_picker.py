from __future__ import annotations

import calendar
from datetime import datetime, date
import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

TEXT_DARK = "#2c3e50"
TEXT_MUTED = "#7f8c8d"
ACCENT_BLUE = "#3498db"
BG_CARD = "#ffffff"
BORDER = "#e0e0e0"


class DatePickerField(ctk.CTkFrame):
    """A compact date field with a calendar popup and editable month/year selectors."""

    def __init__(
        self,
        parent,
        *,
        label: str | None = None,
        default_date: date | None = None,
        on_change=None,
        width: int = 140,
        placeholder_text: str = "YYYY-MM-DD",
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_change = on_change
        self._placeholder_text = placeholder_text
        self._value_var = ctk.StringVar()

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        if label:
            ctk.CTkLabel(
                self,
                text=label,
                font=("Segoe UI", 9),
                text_color=TEXT_MUTED,
            ).grid(row=0, column=0, columnspan=2, sticky="w", padx=2, pady=(0, 4))

        self.entry = ctk.CTkEntry(
            self,
            textvariable=self._value_var,
            placeholder_text=self._placeholder_text,
            height=36,
            width=width,
        )
        self.entry.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        self.calendar_button = ctk.CTkButton(
            self,
            text="📅",
            width=36,
            height=36,
            corner_radius=8,
            fg_color="#e8f4fd",
            hover_color="#d8ebfb",
            text_color=ACCENT_BLUE,
            border_width=1,
            border_color=ACCENT_BLUE,
            command=self.open_picker,
        )
        self.calendar_button.grid(row=1, column=1)

        self._popup = None
        self._month_var = None
        self._year_var = None
        self._selected_date = default_date or datetime.now().date()
        self.variable = self._value_var
        if default_date is not None:
            self.set_date(default_date)

    def get_value(self) -> str:
        return self._value_var.get().strip()

    def get_date(self) -> date | None:
        text = self.get_value()
        if not text:
            return None
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    def set_date(self, value: date | str | None):
        if value is None:
            self._value_var.set("")
            return
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
                try:
                    value = datetime.strptime(value, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                self._value_var.set(value)
                return
        self._selected_date = value
        self._value_var.set(value.strftime("%Y-%m-%d"))

    def open_picker(self):
        if (
            self._popup is not None
            and getattr(self._popup, "winfo_exists", lambda: False)()
        ):
            try:
                self._popup.lift()
            except Exception:
                pass
            return

        popup = ctk.CTkToplevel(self)
        self._popup = popup
        popup.title("Select Date")
        popup.resizable(False, False)
        popup.geometry("380x420")
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        current = self.get_date() or self._selected_date or datetime.now().date()
        months = [calendar.month_name[i] for i in range(1, 13)]
        years = [str(year) for year in range(current.year - 10, current.year + 11)]

        header = ctk.CTkFrame(popup, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)

        self._month_var = ctk.StringVar(value=calendar.month_name[current.month])
        self._year_var = ctk.StringVar(value=str(current.year))

        ctk.CTkLabel(
            header, text="Month", font=("Segoe UI", 9), text_color=TEXT_MUTED
        ).grid(row=0, column=0, sticky="w", padx=2)
        ctk.CTkLabel(
            header, text="Year", font=("Segoe UI", 9), text_color=TEXT_MUTED
        ).grid(row=0, column=1, sticky="w", padx=2)

        month_combo = ttk.Combobox(
            header, values=months, textvariable=self._month_var, state="normal"
        )
        month_combo.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        year_combo = ttk.Combobox(
            header, values=years, textvariable=self._year_var, state="normal"
        )
        year_combo.grid(row=1, column=1, sticky="ew", padx=(6, 0))

        calendar_card = ctk.CTkFrame(
            popup,
            fg_color=BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        calendar_card.pack(fill="both", expand=True, padx=16, pady=(4, 10))

        month_title = ctk.CTkLabel(
            calendar_card,
            text="",
            font=("Segoe UI", 11, "bold"),
            text_color=TEXT_DARK,
        )
        month_title.pack(pady=(10, 6))

        days_frame = ctk.CTkFrame(calendar_card, fg_color="transparent")
        days_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        def _month_index() -> int:
            typed = self._month_var.get().strip()
            for idx, name in enumerate(months, start=1):
                if name.lower().startswith(typed.lower()[:3]):
                    return idx
            return current.month

        def redraw_calendar(*_args):
            for widget in days_frame.winfo_children():
                widget.destroy()

            try:
                year_value = int(self._year_var.get().strip())
            except ValueError:
                year_value = current.year
                self._year_var.set(str(year_value))

            month_index = _month_index()
            month_title.configure(text=f"{months[month_index - 1]} {year_value}")

            weekday_row = ctk.CTkFrame(days_frame, fg_color="transparent")
            weekday_row.pack(fill="x", pady=(0, 4))
            for weekday in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                ctk.CTkLabel(
                    weekday_row,
                    text=weekday,
                    width=42,
                    height=24,
                    anchor="center",
                    font=("Segoe UI", 9, "bold"),
                    text_color=TEXT_MUTED,
                ).pack(side="left", expand=True, fill="x")

            for week in calendar.monthcalendar(year_value, month_index):
                week_row = ctk.CTkFrame(days_frame, fg_color="transparent")
                week_row.pack(fill="x", pady=1)
                for day in week:
                    if day == 0:
                        ctk.CTkLabel(week_row, text="", width=42, height=28).pack(
                            side="left", expand=True, fill="x"
                        )
                        continue

                    is_selected = (
                        self._selected_date.year == year_value
                        and self._selected_date.month == month_index
                        and self._selected_date.day == day
                    )
                    ctk.CTkButton(
                        week_row,
                        text=str(day),
                        width=42,
                        height=28,
                        corner_radius=6,
                        fg_color=ACCENT_BLUE if is_selected else "transparent",
                        hover_color="#d8ebfb",
                        text_color="white" if is_selected else TEXT_DARK,
                        border_width=1,
                        border_color=ACCENT_BLUE,
                        command=lambda d=day: select_day(d),
                    ).pack(side="left", expand=True, fill="x", padx=1)

        def select_day(day: int):
            try:
                self._selected_date = date(
                    int(self._year_var.get()), _month_index(), day
                )
            except ValueError:
                return
            self.set_date(self._selected_date)
            popup.destroy()
            self._popup = None
            if callable(self._on_change):
                self._on_change(self._selected_date)

        month_combo.bind("<KeyRelease>", redraw_calendar)
        year_combo.bind("<KeyRelease>", redraw_calendar)
        month_combo.bind("<<ComboboxSelected>>", redraw_calendar)
        year_combo.bind("<<ComboboxSelected>>", redraw_calendar)

        redraw_calendar()

        footer = ctk.CTkFrame(popup, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkButton(
            footer,
            text="Today",
            width=80,
            height=32,
            fg_color="transparent",
            hover_color="#e8f4fd",
            text_color=ACCENT_BLUE,
            border_width=1,
            border_color=ACCENT_BLUE,
            command=lambda: (
                self._month_var.set(calendar.month_name[datetime.now().month]),
                self._year_var.set(str(datetime.now().year)),
                redraw_calendar(),
            ),
        ).pack(side="left")

        ctk.CTkButton(
            footer,
            text="Close",
            width=80,
            height=32,
            fg_color="#1e2d3d",
            hover_color="#2d3f52",
            text_color="white",
            command=lambda: (popup.destroy(), setattr(self, "_popup", None)),
        ).pack(side="right")
