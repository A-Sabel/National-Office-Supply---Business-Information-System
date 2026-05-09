import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
from datetime import datetime, date, timedelta


# ─────────────────────────────────────────────────────────────────────────────
# Small reusable summary card  (matches MetricCard style)
# ─────────────────────────────────────────────────────────────────────────────
class _SummaryCard(ctk.CTkFrame):
    def __init__(self, parent, title, value, sub, color="#3498db"):
        super().__init__(parent, fg_color="#ffffff", corner_radius=12,
                         border_width=1, border_color="#e0e0e0")
        ctk.CTkLabel(self, text=title, font=("Segoe UI", 11, "bold"),
                     text_color="#7f8c8d").pack(anchor="w", padx=14, pady=(12, 0))
        ctk.CTkLabel(self, text=value, font=("Segoe UI", 22, "bold"),
                     text_color="#2c3e50").pack(anchor="w", padx=14, pady=(2, 0))
        ctk.CTkLabel(self, text=sub, font=("Segoe UI", 10),
                     text_color=color).pack(anchor="w", padx=14, pady=(0, 12))


# ─────────────────────────────────────────────────────────────────────────────
# Worker Files panel
# ─────────────────────────────────────────────────────────────────────────────
class _WorkerFilesPanel(ctk.CTkFrame):
    # Only 4 columns: Employee Name, Position, Hourly Wage, SSN
    SAMPLE = [
        ("Antonio Porsild",              "Manager",              "P100.00", "***-**-6789"),
        ("Jacqueline Tonio-Guevarra",    "Manager",              "P100.00", "***-**-4521"),
        ("Marissa Aldana",               "Warehouse Clerk",      "P100.00", "***-**-8832"),
        ("Edilberto Calleja",            "Warehouse Associate",  "P80.00", "***-**-6330"),
        ("Ana Teresa Licaros",           "Sales Representative", "N/A", "***-**-1122"),
        ("Luis Santos",                  "Sales Representative", "N/A", "***-**-9901"),
    ]

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._revealed = {}
        self._search_var = ctk.StringVar()

        # header row
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr, text="Employee Worker Files",
                     font=("Segoe UI", 16, "bold"),
                     text_color="#2c3e50").grid(row=0, column=0, sticky="w")

        sf = ctk.CTkFrame(hdr, fg_color="transparent")
        sf.grid(row=0, column=1, sticky="e")
        self._se = ctk.CTkEntry(sf, textvariable=self._search_var,
                                placeholder_text="Search employees...",
                                width=210, height=32,
                                fg_color="#ffffff", border_color="#d0d7de",
                                border_width=1, text_color="#1c2128",
                                font=("Segoe UI", 12))
        self._se.pack(side="left", padx=(0, 6))
        self._search_var.trace_add("write", lambda *_: self._filter())
        ctk.CTkButton(sf, text="Filter", width=58, height=32,
                      fg_color="#e8eef5", hover_color="#d7e3f0",
                      text_color="#2c3e50", font=("Segoe UI", 11),
                      command=self._filter).pack(side="left")

        # table card
        card = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12,
                            border_width=1, border_color="#e0e0e0")
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Worker.Treeview",
                        font=("Segoe UI", 11), rowheight=34,
                        background="#ffffff", fieldbackground="#ffffff",
                        borderwidth=0)
        style.configure("Worker.Treeview.Heading",
                        font=("Segoe UI", 11, "bold"),
                        background="#2c3e50", foreground="#ffffff",
                        relief="flat")
        style.map("Worker.Treeview.Heading",
                  background=[("active", "#34495e")],
                  foreground=[("active", "#ffffff")])

        cols = ("Employee Name", "Position", "Hourly Wage", "SSN")
        self.tree = ttk.Treeview(card, columns=cols, show="headings",
                                 height=8, style="Worker.Treeview")
        # stretch=True on all cols so they fill the full card width
        for col, w, anc, stretch in [
            ("Employee Name", 250, "w",      True),
            ("Position",      220, "w",      True),
            ("Hourly Wage",   130, "center", False),
            ("SSN",           160, "w",      False),
        ]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anc, stretch=stretch)

        self.tree.tag_configure("even", background="#ffffff", foreground="#2c3e50")
        self.tree.tag_configure("odd",  background="#f2f4f7", foreground="#2c3e50")

        vsb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns", pady=10)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)

        # reveal button row
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        ctk.CTkLabel(btn_row, text="Select a row then:",
                     font=("Segoe UI", 11), text_color="#7f8c8d").pack(side="left")
        ctk.CTkButton(btn_row, text="Show / Hide SSN",
                      width=140, height=28,
                      fg_color="#ebf3fb", hover_color="#dbe9f9",
                      text_color="#1f5f9f", font=("Segoe UI", 11),
                      corner_radius=6, command=self._toggle_ssn).pack(side="left", padx=8)

        self._load(self.SAMPLE)

    def _load(self, rows):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self._revealed.clear()
        for idx, row in enumerate(rows):
            tag = "even" if idx % 2 == 0 else "odd"
            iid = self.tree.insert("", "end", values=row, tags=(tag,))
            self._revealed[iid] = False

    def _filter(self):
        q = self._search_var.get().lower()
        data = [r for r in self.SAMPLE if any(q in str(v).lower() for v in r)]
        self._load(data)

    def _toggle_ssn(self):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        vals = list(self.tree.item(iid, "values"))
        if self._revealed.get(iid, False):
            last4 = vals[3][-4:]
            vals[3] = f"***-**-{last4}"
            self._revealed[iid] = False
        else:
            last4 = vals[3][-4:]
            vals[3] = f"123-45-{last4}"
            self._revealed[iid] = True
        self.tree.item(iid, values=vals)


# ─────────────────────────────────────────────────────────────────────────────
# Payroll Audit & Processing panel
# ─────────────────────────────────────────────────────────────────────────────
class _AuditPanel(ctk.CTkFrame):
    MISSING = [
        ("Miguel Mojado",   "Warehouse Associate",  "Mon-Fri"),
        ("May Jaspe",       "Sales Representative", "Mon-Fri"),
        ("Genna Gracia",    "Sales Representative", "Full Week"),
    ]

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        today = date.today()
        mon   = today - timedelta(days=today.weekday())
        sun   = mon + timedelta(days=6)
        week_str = f"Week: {mon.strftime('%b %d')} - {sun.strftime('%b %d, %Y')}"

        # week banner
        banner = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12,
                              border_width=1, border_color="#e0e0e0")
        banner.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        brow = ctk.CTkFrame(banner, fg_color="transparent")
        brow.pack(fill="x", padx=16, pady=12)
        brow.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(brow, text="Payroll Audit & Processing",
                     font=("Segoe UI", 16, "bold"),
                     text_color="#2c3e50").pack(side="left")
        ctk.CTkLabel(brow, text=week_str,
                     font=("Segoe UI", 11), text_color="#7f8c8d").pack(side="right")

        # two-column body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_rowconfigure(0, weight=1)

        # LEFT – missing timecards
        left_card = ctk.CTkFrame(body, fg_color="#ffffff", corner_radius=12,
                                 border_width=1, border_color="#e0e0e0")
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        ctk.CTkLabel(left_card,
                     text=f"Missing Timecards: {len(self.MISSING)} Hourly Employees",
                     font=("Segoe UI", 13, "bold"),
                     text_color="#e74c3c").pack(anchor="w", padx=16, pady=(14, 8))

        for name, pos, period in self.MISSING:
            row_f = ctk.CTkFrame(left_card, fg_color="#fff8f8", corner_radius=8)
            row_f.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(row_f, text="*", font=("Segoe UI", 18),
                         text_color="#e74c3c").pack(side="left", padx=(10, 6))
            info = ctk.CTkFrame(row_f, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=8)
            ctk.CTkLabel(info, text=name, font=("Segoe UI", 12, "bold"),
                         text_color="#2c3e50").pack(anchor="w")
            ctk.CTkLabel(info, text=pos, font=("Segoe UI", 10),
                         text_color="#7f8c8d").pack(anchor="w")
            badges = ctk.CTkFrame(row_f, fg_color="transparent")
            badges.pack(side="right", padx=10)
            ctk.CTkLabel(badges, text=period, font=("Segoe UI", 9),
                         text_color="#92400e", fg_color="#fef3c7",
                         corner_radius=4, width=70, height=20).pack(pady=(4, 2))
            ctk.CTkLabel(badges, text="Missing", font=("Segoe UI", 9, "bold"),
                         text_color="#ffffff", fg_color="#e74c3c",
                         corner_radius=4, width=70, height=20).pack(pady=(0, 4))

        ctk.CTkFrame(left_card, fg_color="transparent", height=8).pack()

        # RIGHT – totals + button
        right_card = ctk.CTkFrame(body, fg_color="#ffffff", corner_radius=12,
                                  border_width=1, border_color="#e0e0e0",
                                  width=240)
        right_card.grid(row=0, column=1, sticky="ns")
        right_card.grid_propagate(False)

        ctk.CTkLabel(right_card, text="Total Pending (86 Approved)",
                     font=("Segoe UI", 10), text_color="#5d7ab5"
                     ).pack(pady=(18, 0))
        ctk.CTkLabel(right_card, text="P142,500.00",
                     font=("Segoe UI", 22, "bold"),
                     text_color="#1a2d5a").pack(pady=(2, 12))

        warn = ctk.CTkFrame(right_card, fg_color="#fffbeb", corner_radius=8,
                            border_width=1, border_color="#fbbf24")
        warn.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkLabel(warn,
                     text=f"  {len(self.MISSING)} timecards missing\nReview before processing",
                     font=("Segoe UI", 10), text_color="#92400e",
                     justify="center").pack(pady=8, padx=8)

        self._proc_btn = ctk.CTkButton(
            right_card, text="Process Weekly Payroll",
            height=44, fg_color="#27ae60", hover_color="#1e8449",
            text_color="#ffffff", font=("Segoe UI", 13, "bold"),
            corner_radius=10, command=self._process)
        self._proc_btn.pack(fill="x", padx=14, pady=(0, 8))

        ctk.CTkButton(right_card, text="View All Timecards",
                      height=30, fg_color="#ebf3fb", hover_color="#dbe9f9",
                      text_color="#1f5f9f", font=("Segoe UI", 11),
                      corner_radius=8, command=lambda: None
                      ).pack(fill="x", padx=14, pady=(0, 14))

    def _process(self):
        self._proc_btn.configure(text="Payroll Processed",
                                 fg_color="#1a7a40", state="disabled")


# ─────────────────────────────────────────────────────────────────────────────
# Timecard Entry panel
# ─────────────────────────────────────────────────────────────────────────────
class _TimecardPanel(ctk.CTkFrame):
    HISTORY = [
        ("Week of Apr 28", "40 hrs", "P1,200.00", "Approved"),
        ("Week of Apr 21", "38 hrs", "P1,140.00", "Approved"),
        ("Week of Apr 14", "40 hrs", "P1,200.00", "Pending"),
        ("Week of Apr 07", "35 hrs", "P1,050.00", "Approved"),
    ]

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # submit form
        form = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12,
                            border_width=1, border_color="#e0e0e0")
        form.grid(row=0, column=0, sticky="ew", pady=(0, 14))

        ctk.CTkLabel(form, text="Submit Timecard",
                     font=("Segoe UI", 15, "bold"),
                     text_color="#2c3e50").pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkLabel(form, text="Enter hours worked for the current week",
                     font=("Segoe UI", 11), text_color="#7f8c8d"
                     ).pack(anchor="w", padx=16, pady=(0, 10))

        frow = ctk.CTkFrame(form, fg_color="transparent")
        frow.pack(fill="x", padx=16, pady=(0, 14))
        frow.grid_columnconfigure((0, 1, 2), weight=1)

        today = date.today()
        mon   = today - timedelta(days=today.weekday())

        def _field(col, label, default="", placeholder=""):
            f = ctk.CTkFrame(frow, fg_color="transparent")
            f.grid(row=0, column=col, sticky="ew", padx=(0, 10))
            ctk.CTkLabel(f, text=label, font=("Segoe UI", 11, "bold"),
                         text_color="#34495e").pack(anchor="w")
            e = ctk.CTkEntry(f, placeholder_text=placeholder, height=36,
                             fg_color="#f8f9fa", border_color="#d0d7de",
                             border_width=1, text_color="#1c2128",
                             font=("Segoe UI", 12))
            e.pack(fill="x", pady=(4, 0))
            if default:
                e.insert(0, default)
            return e

        _field(0, "Week Starting", mon.strftime("%b %d, %Y"))
        self._hours = _field(1, "Hours Worked", placeholder="e.g. 40")
        _field(2, "Notes (optional)", placeholder="Overtime, sick leave...")

        ctk.CTkButton(form, text="Submit Timecard",
                      height=36, width=170,
                      fg_color="#3498db", hover_color="#2980b9",
                      text_color="#ffffff", font=("Segoe UI", 12, "bold"),
                      corner_radius=8, command=self._submit
                      ).pack(anchor="e", padx=16, pady=(0, 14))

        # history card
        hist = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12,
                            border_width=1, border_color="#e0e0e0")
        hist.grid(row=1, column=0, sticky="nsew")
        hist.grid_columnconfigure(0, weight=1)
        hist.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(hist, text="Submission History",
                     font=("Segoe UI", 14, "bold"),
                     text_color="#2c3e50").grid(row=0, column=0, sticky="w",
                                                padx=16, pady=(14, 6))

        style = ttk.Style()
        style.configure("TC.Treeview",
                        font=("Segoe UI", 11), rowheight=32,
                        background="#ffffff", fieldbackground="#ffffff",
                        borderwidth=0)
        style.configure("TC.Treeview.Heading",
                        font=("Segoe UI", 11, "bold"),
                        background="#2c3e50", foreground="#ffffff",
                        relief="flat")

        cols = ("Week", "Hours", "Gross Pay", "Status")
        self._ht = ttk.Treeview(hist, columns=cols, show="headings",
                                height=5, style="TC.Treeview")
        for col, w, anc in [("Week", 200, "w"), ("Hours", 90, "center"),
                             ("Gross Pay", 120, "e"), ("Status", 90, "center")]:
            self._ht.heading(col, text=col)
            self._ht.column(col, width=w, anchor=anc)
        self._ht.tag_configure("even",     background="#ffffff", foreground="#2c3e50")
        self._ht.tag_configure("odd",      background="#f2f4f7", foreground="#2c3e50")
        self._ht.tag_configure("approved", foreground="#1e8449")
        self._ht.tag_configure("pending",  foreground="#d35400")

        for idx, row in enumerate(self.HISTORY):
            tag  = "even" if idx % 2 == 0 else "odd"
            stag = "approved" if row[3] == "Approved" else "pending"
            self._ht.insert("", "end", values=row, tags=(tag, stag))

        vsb = ttk.Scrollbar(hist, orient="vertical", command=self._ht.yview)
        self._ht.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns", pady=(0, 10))
        self._ht.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(0, 10))

    def _submit(self):
        hrs = self._hours.get().strip()
        if hrs:
            print(f"[Timecard] {hrs} hrs submitted")
            self._hours.delete(0, "end")


# ─────────────────────────────────────────────────────────────────────────────
# PayrollView  — top-level tab, matches CustomersView mounting pattern exactly
# ─────────────────────────────────────────────────────────────────────────────
class PayrollView(ctk.CTkFrame):
    def __init__(self, parent, controller, role="Manager"):
        super().__init__(parent, fg_color="#f8f9fa")
        self.controller = controller
        self.role        = role

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # 1. header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=30, pady=(22, 0))
        hdr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(hdr, text="Payroll Manager",
                     font=("Segoe UI", 26, "bold"),
                     text_color="#2c3e50").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(hdr, text=datetime.now().strftime("%A, %B %d %Y"),
                     font=("Segoe UI", 12),
                     text_color="#7f8c8d").grid(row=0, column=1, sticky="e")

        # 2. summary strip
        if role == "Manager":
            strip = ctk.CTkFrame(self, fg_color="transparent")
            strip.grid(row=1, column=0, sticky="ew", padx=30, pady=(14, 0))
            strip.grid_columnconfigure((0, 1, 2, 3), weight=1)
            for col, (title, val, sub, clr) in enumerate([
                ("Total Employees",  "86",         "Active this week",  "#3498db"),
                ("Pending Approval", "3",           "Missing timecards", "#e74c3c"),
                ("Gross Payroll",    "P142,500.00", "This week estimate","#27ae60"),
                ("Avg Hourly Rate",  "P28.75",      "Across all staff",  "#8e44ad"),
            ]):
                _SummaryCard(strip, title, val, sub, clr).grid(
                    row=0, column=col, sticky="nsew",
                    padx=(0 if col == 0 else 10, 0))

        # 3. tab bar
        tab_row = ctk.CTkFrame(self, fg_color="transparent")
        tab_row.grid(row=2, column=0, sticky="ew", padx=30, pady=(16, 0))

        self._tab_btns = {}
        tabs = (
            [("worker_files", "  Worker Files"),
             ("audit",        "  Payroll Audit & Processing"),
             ("timecard",     "  Timecard Entry")]
            if role == "Manager"
            else [("timecard", "  Timecard Entry")]
        )
        for key, label in tabs:
            btn = ctk.CTkButton(
                tab_row, text=label, height=34, corner_radius=8,
                fg_color="#e8eef5", hover_color="#d7e3f0",
                text_color="#2c3e50", font=("Segoe UI", 12),
                command=lambda k=key: self._switch(k))
            btn.pack(side="left", padx=(0, 8))
            self._tab_btns[key] = btn

        # 4. scrollable content
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0)
        self._scroll.grid(row=3, column=0, sticky="nsew", padx=30, pady=(12, 20))
        self._scroll.grid_columnconfigure(0, weight=1)

        self._switch(tabs[0][0])

    def _switch(self, key):
        for k, b in self._tab_btns.items():
            b.configure(
                fg_color="#3498db" if k == key else "#e8eef5",
                text_color="#ffffff" if k == key else "#2c3e50")

        for w in self._scroll.winfo_children():
            w.destroy()

        {"worker_files": _WorkerFilesPanel,
         "audit":        _AuditPanel,
         "timecard":     _TimecardPanel}[key](self._scroll).grid(
            row=0, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)