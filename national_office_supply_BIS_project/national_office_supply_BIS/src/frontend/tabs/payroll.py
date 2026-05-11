import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None


# ─────────────────────────────────────────────────────────────────────────────
# DB Helper
# ─────────────────────────────────────────────────────────────────────────────
def _get_conn(db_config):
    if psycopg2 is None:
        raise RuntimeError("psycopg2 not installed.")
    return psycopg2.connect(**db_config)


def auto_generate_timecards(db_config):
    """
    Call this on app startup (from __main__.py build_main_application).
    Creates blank timecard rows for all active hourly employees
    that don't yet have one for the current week. Safe to call multiple
    times — won't create duplicates.
    """
    if psycopg2 is None:
        return

    today = date.today()
    week = today - timedelta(days=today.weekday())  # Monday

    try:
        conn = _get_conn(db_config)
        cur = conn.cursor()

        # Find active hourly employees with no timecard this week
        cur.execute(
            """
            SELECT e.employee_number
            FROM   employees e
            LEFT JOIN timecards t
                   ON  t.employee_number = e.employee_number
                   AND t.week_date = %s
            WHERE  e.is_active = TRUE
              AND  e.position  = 'Hourly'
              AND  t.timecard_id IS NULL
        """,
            (week,),
        )
        missing_emps = cur.fetchall()

        inserted = 0
        for (emp_num,) in missing_emps:
            cur.execute(
                """
                INSERT INTO timecards (employee_number, week_date, hours_worked)
                VALUES (%s, %s, 0)
                ON CONFLICT DO NOTHING
            """,
                (emp_num, week),
            )
            inserted += 1

        conn.commit()
        cur.close()
        conn.close()

        if inserted:
            print(
                f"[Payroll] Auto-generated {inserted} blank timecard(s) "
                f"for week of {week}."
            )
        else:
            print(f"[Payroll] All timecards exist for week of {week}.")

    except Exception as e:
        print(f"[Payroll] Auto-timecard generation failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Reusable Summary Card
# ─────────────────────────────────────────────────────────────────────────────
class _SummaryCard(ctk.CTkFrame):
    def __init__(self, parent, title, value, sub, color="#3498db"):
        super().__init__(
            parent,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )
        ctk.CTkLabel(
            self, text=title, font=("Segoe UI", 11, "bold"), text_color="#7f8c8d"
        ).pack(anchor="w", padx=14, pady=(12, 0))
        self._val_lbl = ctk.CTkLabel(
            self, text=value, font=("Segoe UI", 22, "bold"), text_color="#2c3e50"
        )
        self._val_lbl.pack(anchor="w", padx=14, pady=(2, 0))
        ctk.CTkLabel(self, text=sub, font=("Segoe UI", 10), text_color=color).pack(
            anchor="w", padx=14, pady=(0, 12)
        )

    def update_value(self, value):
        self._val_lbl.configure(text=value)


# ─────────────────────────────────────────────────────────────────────────────
# PANEL 1 — Worker Files  (Manager only)
# REVISED: show-all SSN button, per-row eye icon, tighter table spacing
# ─────────────────────────────────────────────────────────────────────────────
class _WorkerFilesPanel(ctk.CTkFrame):
    def __init__(self, parent, db_config):
        super().__init__(parent, fg_color="transparent")
        self.db_config = db_config
        self._revealed = {}
        self._all_revealed = False
        self._search_var = ctk.StringVar()
        self._all_rows = []
        self._full_ssns = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            hdr,
            text="Employee Worker Files",
            font=("Segoe UI", 16, "bold"),
            text_color="#2c3e50",
        ).grid(row=0, column=0, sticky="w")

        sf = ctk.CTkFrame(hdr, fg_color="transparent")
        sf.grid(row=0, column=1, sticky="e")
        ctk.CTkEntry(
            sf,
            textvariable=self._search_var,
            placeholder_text="Search employees...",
            width=200,
            height=30,
            fg_color="#ffffff",
            border_color="#d0d7de",
            border_width=1,
            text_color="#1c2128",
            font=("Segoe UI", 11),
        ).pack(side="left", padx=(0, 5))
        self._search_var.trace_add("write", lambda *_: self._filter())
        ctk.CTkButton(
            sf,
            text="Filter",
            width=54,
            height=30,
            fg_color="#e8eef5",
            hover_color="#d7e3f0",
            text_color="#2c3e50",
            font=("Segoe UI", 11),
            command=self._filter,
        ).pack(side="left")
        ctk.CTkButton(
            sf,
            text="Refresh",
            width=64,
            height=30,
            fg_color="#ebf3fb",
            hover_color="#dbe9f9",
            text_color="#1f5f9f",
            font=("Segoe UI", 11),
            command=self._load_db,
        ).pack(side="left", padx=(5, 0))

        # ── table card ────────────────────────────────────────────────────────
        card = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Worker.Treeview",
            font=("Segoe UI", 11),
            rowheight=30,
            background="#ffffff",
            fieldbackground="#ffffff",
            borderwidth=0,
        )
        style.configure(
            "Worker.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            background="#2c3e50",
            foreground="#ffffff",
            relief="flat",
            padding=(6, 4),
        )
        style.map(
            "Worker.Treeview.Heading",
            background=[("active", "#34495e")],
            foreground=[("active", "#ffffff")],
        )
        style.map(
            "Worker.Treeview",
            background=[("selected", "#d6eaf8")],
            foreground=[("selected", "#1a252f")],
        )

        cols = ("Employee Name", "Position", "Hourly Wage", "SSN", "👁")
        self.tree = ttk.Treeview(
            card, columns=cols, show="headings", height=9, style="Worker.Treeview"
        )

        for col, w, anc, stretch in [
            ("Employee Name", 150, "w", True),
            ("Position", 90, "w", True),
            ("Hourly Wage", 110, "center", True),
            ("SSN", 155, "center", True),
            ("👁", 36, "center", False),
        ]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anc, stretch=stretch, minwidth=w)  # type: ignore[arg-type]

        self.tree.tag_configure("even", background="#ffffff", foreground="#2c3e50")
        self.tree.tag_configure("odd", background="#f7f9fb", foreground="#2c3e50")

        vsb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns", padx=(0, 6), pady=8)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        self.tree.bind("<ButtonRelease-1>", self._on_click)

        # ── bottom toolbar ────────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(
            card, fg_color="#f7f9fb", corner_radius=0, border_width=0
        )
        toolbar.grid(row=1, column=0, columnspan=2, sticky="ew")

        ctk.CTkLabel(
            toolbar,
            text="Click 👁 on any row to reveal its SSN individually",
            font=("Segoe UI", 10),
            text_color="#95a5a6",
        ).pack(side="left", padx=12, pady=6)

        self._toggle_all_btn = ctk.CTkButton(
            toolbar,
            text="👁  Show All SSNs",
            width=150,
            height=28,
            fg_color="#ebf3fb",
            hover_color="#dbe9f9",
            text_color="#1f5f9f",
            font=("Segoe UI", 11, "bold"),
            corner_radius=6,
            command=self._toggle_all_ssn,
        )
        self._toggle_all_btn.pack(side="right", padx=10, pady=6)

        self._load_db()

    def _load_db(self):
        try:
            conn = _get_conn(self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[attr-defined]
            cur.execute("""
                SELECT employee_name,
                       position,
                       COALESCE('P' || hourly_wage::text, 'N/A') AS hourly_wage,
                       ssn
                FROM   employees
                WHERE  is_active = TRUE
                ORDER  BY employee_name
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            self._all_rows = [
                (
                    r["employee_name"],
                    r["position"],
                    r["hourly_wage"],
                    "***-**-" + r["ssn"][-4:],
                    "👁",
                )
                for r in rows
            ]
            self._full_ssns = {i: r["ssn"] for i, r in enumerate(rows)}

        except Exception as e:
            messagebox.showerror("DB Error", f"Could not load employees:\n{e}")
            self._all_rows = []
            self._full_ssns = {}

        self._all_revealed = False
        self._toggle_all_btn.configure(text="👁  Show All SSNs")
        self._render(self._all_rows)

    def _render(self, rows):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self._revealed.clear()
        for idx, row in enumerate(rows):
            tag = "even" if idx % 2 == 0 else "odd"
            iid = self.tree.insert("", "end", values=row, tags=(tag,))
            self._revealed[iid] = False

    def _filter(self):
        q = self._search_var.get().lower()
        data = [r for r in self._all_rows if any(q in str(v).lower() for v in r[:4])]
        self._all_revealed = False
        self._toggle_all_btn.configure(text="👁  Show All SSNs")
        self._render(data)

    def _on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        col = self.tree.identify_column(event.x)
        iid = self.tree.identify_row(event.y)
        if region != "cell" or col != "#5" or not iid:
            return
        self._toggle_row_ssn(iid)

    def _toggle_row_ssn(self, iid):
        vals = list(self.tree.item(iid, "values"))
        children = list(self.tree.get_children())
        idx = children.index(iid)
        if self._revealed.get(iid, False):
            last4 = str(vals[3])[-4:]
            vals[3] = f"***-**-{last4}"
            self._revealed[iid] = False
        else:
            vals[3] = self._full_ssns.get(idx, vals[3])
            self._revealed[iid] = True
        self.tree.item(iid, values=vals)

    def _toggle_all_ssn(self):
        self._all_revealed = not self._all_revealed
        children = list(self.tree.get_children())
        for idx, iid in enumerate(children):
            vals = list(self.tree.item(iid, "values"))
            if self._all_revealed:
                vals[3] = self._full_ssns.get(idx, vals[3])
                self._revealed[iid] = True
            else:
                last4 = str(vals[3])[-4:]
                vals[3] = f"***-**-{last4}"
                self._revealed[iid] = False
            self.tree.item(iid, values=vals)
        self._toggle_all_btn.configure(
            text="🔒  Hide All SSNs" if self._all_revealed else "👁  Show All SSNs",
            fg_color="#fdecea" if self._all_revealed else "#ebf3fb",
            hover_color="#f5c6cb" if self._all_revealed else "#dbe9f9",
            text_color="#c0392b" if self._all_revealed else "#1f5f9f",
        )


# ─────────────────────────────────────────────────────────────────────────────
# PANEL 2 — Payroll Audit & Processing  (Manager only)
# REVISED: scrollable left list, sticky right panel, commission section added
# ─────────────────────────────────────────────────────────────────────────────
class _AuditPanel(ctk.CTkFrame):
    def __init__(self, parent, db_config, session_manager=None):
        super().__init__(parent, fg_color="transparent")
        self.db_config = db_config
        self._session_manager = session_manager
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        today = date.today()
        self._week = today - timedelta(days=today.weekday())
        # self._week = date(2006, 8, 7)
        sun = self._week + timedelta(days=6)
        week_str = f"Week: {self._week.strftime('%b %d')} - {sun.strftime('%b %d, %Y')}"

        # ── week banner ───────────────────────────────────────────────────────
        banner = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )
        banner.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        brow = ctk.CTkFrame(banner, fg_color="transparent")
        brow.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(
            brow,
            text="Payroll Audit & Processing",
            font=("Segoe UI", 16, "bold"),
            text_color="#2c3e50",
        ).pack(side="left")
        ctk.CTkLabel(
            brow, text=week_str, font=("Segoe UI", 11), text_color="#7f8c8d"
        ).pack(side="right")

        # ── two-column body ───────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_rowconfigure(0, weight=1)

        # ── LEFT — missing timecards (scrollable) ─────────────────────────────
        self._left_card = ctk.CTkFrame(
            body,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )
        self._left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._left_card.grid_columnconfigure(0, weight=1)
        self._left_card.grid_rowconfigure(1, weight=1)

        self._missing_title = ctk.CTkLabel(
            self._left_card,
            text="Missing Timecards: loading...",
            font=("Segoe UI", 13, "bold"),
            text_color="#e74c3c",
        )
        self._missing_title.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        self._missing_body = ctk.CTkScrollableFrame(
            self._left_card, fg_color="transparent", corner_radius=0, height=260
        )
        self._missing_body.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._missing_body.grid_columnconfigure(0, weight=1)

        # ── RIGHT — totals + buttons (sticky) ────────────────────────────────
        right_card = ctk.CTkFrame(
            body,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
            width=240,
            height=260,
        )
        right_card.grid(row=0, column=1, sticky="ns")
        right_card.grid_propagate(False)

        ctk.CTkLabel(
            right_card,
            text="Estimated Gross Payroll",
            font=("Segoe UI", 10),
            text_color="#5d7ab5",
        ).pack(pady=(18, 0))
        self._total_lbl = ctk.CTkLabel(
            right_card,
            text="P0.00",
            font=("Segoe UI", 22, "bold"),
            text_color="#1a2d5a",
        )
        self._total_lbl.pack(pady=(2, 12))

        self._warn_lbl = ctk.CTkLabel(
            right_card,
            text="",
            font=("Segoe UI", 10),
            text_color="#92400e",
            fg_color="#fffbeb",
            corner_radius=8,
            wraplength=200,
            justify="center",
        )
        self._warn_lbl.pack(fill="x", padx=14, pady=(0, 12))

        self._proc_btn = ctk.CTkButton(
            right_card,
            text="Generate Weekly Checks",
            height=44,
            fg_color="#27ae60",
            hover_color="#1e8449",
            text_color="#ffffff",
            font=("Segoe UI", 12, "bold"),
            corner_radius=10,
            command=self._generate_payroll,
        )
        self._proc_btn.pack(fill="x", padx=14, pady=(0, 8))

        ctk.CTkButton(
            right_card,
            text="Export to CSV",
            height=30,
            fg_color="#e8f5e9",
            hover_color="#c8e6c9",
            text_color="#1b5e20",
            font=("Segoe UI", 11),
            corner_radius=8,
            command=self._export_csv,
        ).pack(fill="x", padx=14, pady=(0, 8))

        ctk.CTkButton(
            right_card,
            text="Refresh",
            height=30,
            fg_color="#ebf3fb",
            hover_color="#dbe9f9",
            text_color="#1f5f9f",
            font=("Segoe UI", 11),
            corner_radius=8,
            command=self._load_db,
        ).pack(fill="x", padx=14, pady=(0, 14))

        # ── BOTTOM — sales rep commission section ─────────────────────────────
        comm_card = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )
        comm_card.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        comm_card.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=0)

        ctk.CTkLabel(
            comm_card,
            text="Sales Rep Commissions — This Week",
            font=("Segoe UI", 13, "bold"),
            text_color="#2c3e50",
        ).pack(anchor="w", padx=16, pady=(14, 6))

        style2 = ttk.Style()
        style2.configure(
            "Comm.Treeview",
            font=("Segoe UI", 11),
            rowheight=30,
            background="#ffffff",
            fieldbackground="#ffffff",
            borderwidth=0,
        )
        style2.configure(
            "Comm.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            background="#2c3e50",
            foreground="#ffffff",
            relief="flat",
        )

        comm_cols = (
            "Sales Rep",
            "Invoices",
            "Total Sales",
            "Commission (5%)",
            "Status",
        )
        self._comm_tree = ttk.Treeview(
            comm_card,
            columns=comm_cols,
            show="headings",
            height=5,
            style="Comm.Treeview",
        )
        for col, w, anc, stretch in [
            ("Sales Rep", 110, "w", True),
            ("Invoices", 80, "center", True),
            ("Total Sales", 130, "w", True),
            ("Commission (5%)", 130, "w", True),
            ("Status", 100, "center", True),
        ]:
            self._comm_tree.heading(col, text=col)
            self._comm_tree.column(col, width=w, anchor=anc, stretch=stretch)  # type: ignore[arg-type]

        self._comm_tree.tag_configure(
            "even", background="#ffffff", foreground="#2c3e50"
        )
        self._comm_tree.tag_configure("odd", background="#f7f9fb", foreground="#2c3e50")
        self._comm_tree.tag_configure("paid", foreground="#1e8449")
        self._comm_tree.tag_configure("pending", foreground="#d35400")

        cvsb = ttk.Scrollbar(
            comm_card, orient="vertical", command=self._comm_tree.yview
        )
        self._comm_tree.configure(yscrollcommand=cvsb.set)
        cvsb.pack(side="right", fill="y", pady=(0, 8))
        self._comm_tree.pack(fill="x", padx=(8, 0), pady=(0, 8))

        self._load_db()

    def _ensure_active_session(self, allowed_roles=None):
        """Enforce session validity before audit/payroll mutations."""
        if self._session_manager is not None:
            self._session_manager.ensure_active(allowed_roles)

    # ── DB load ───────────────────────────────────────────────────────────────
    def _load_db(self):
        try:
            conn = _get_conn(self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[attr-defined]

            cur.execute(
                """
                SELECT e.employee_name, e.position
                FROM   employees e
                LEFT JOIN timecards t
                    ON  t.employee_number = e.employee_number
                    AND t.week_date = %s
                WHERE  e.is_active = TRUE
                  AND  e.position  = 'Hourly'
                  AND  t.timecard_id IS NULL
                ORDER  BY e.employee_name
            """,
                (self._week,),
            )
            missing = cur.fetchall()

            cur.execute(
                """
                SELECT COALESCE(SUM(t.hours_worked * COALESCE(e.hourly_wage,0)),0)
                       AS gross
                FROM   timecards t
                JOIN   employees e ON e.employee_number = t.employee_number
                WHERE  e.is_active = TRUE
                  AND  e.position  = 'Hourly'
                  AND  t.week_date = %s
            """,
                (self._week,),
            )
            result = cur.fetchone()
            gross = result[0] if result else 0

            cur.close()
            conn.close()

        except Exception as e:
            messagebox.showerror("DB Error", f"Audit load failed:\n{e}")
            missing, gross = [], 0

        for w in self._missing_body.winfo_children():
            w.destroy()

        self._missing_title.configure(
            text=f"Missing Timecards: {len(missing)} Hourly Employees"
        )

        for row in missing:
            f = ctk.CTkFrame(self._missing_body, fg_color="#fff8f8", corner_radius=8)
            f.pack(fill="x", pady=3)
            ctk.CTkLabel(
                f, text="!", font=("Segoe UI", 14, "bold"), text_color="#e74c3c"
            ).pack(side="left", padx=(10, 6))
            info = ctk.CTkFrame(f, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=8)
            ctk.CTkLabel(
                info,
                text=row["employee_name"],
                font=("Segoe UI", 12, "bold"),
                text_color="#2c3e50",
            ).pack(anchor="w")
            ctk.CTkLabel(
                info, text=row["position"], font=("Segoe UI", 10), text_color="#7f8c8d"
            ).pack(anchor="w")
            ctk.CTkLabel(
                f,
                text="Missing",
                font=("Segoe UI", 9, "bold"),
                text_color="#ffffff",
                fg_color="#e74c3c",
                corner_radius=4,
                width=60,
                height=20,
            ).pack(side="right", padx=10)

        self._total_lbl.configure(text=f"P{gross:,.2f}")
        if missing:
            self._warn_lbl.configure(
                text=f"{len(missing)} timecards missing\nReview before processing"
            )
        else:
            self._warn_lbl.configure(text="All timecards submitted!")

        self._load_commissions()

    def _load_commissions(self):
        """Load this week's sales rep commission data."""
        for iid in self._comm_tree.get_children():
            self._comm_tree.delete(iid)

        try:
            conn = _get_conn(self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[attr-defined]
            week_end = self._week + timedelta(days=6)
            cur.execute(
                """
                SELECT e.employee_number,
                       e.employee_name,
                       COUNT(i.invoice_id)               AS invoice_count,
                       COALESCE(SUM(i.total_amount), 0)  AS total_sales,
                       COALESCE(SUM(i.total_amount), 0) * 0.05 AS commission,
                       CASE WHEN EXISTS (
                           SELECT 1 FROM employee_payments ep
                           WHERE  ep.employee_number    = e.employee_number
                             AND  ep.payment_type       = 'commission'
                             AND  ep.invoice_period_end = %(week_end)s
                       ) THEN 'Paid' ELSE 'Pending' END AS status
                FROM   employees e
                LEFT JOIN invoices i
                       ON  i.employee_number = e.employee_number
                       AND i.date_written BETWEEN %(week_start)s AND %(week_end)s
                       AND i.status <> 'void'
                WHERE  e.is_active = TRUE
                  AND  e.position  = 'Sales Rep'
                GROUP  BY e.employee_number, e.employee_name
                ORDER  BY total_sales DESC, e.employee_name
            """,
                {"week_start": self._week, "week_end": week_end},
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()

        except Exception as e:
            messagebox.showerror("DB Error", f"Commission load failed:\n{e}")
            return

        for idx, r in enumerate(rows):
            tag = "even" if idx % 2 == 0 else "odd"
            stag = "paid" if r["status"] == "Paid" else "pending"
            self._comm_tree.insert(
                "",
                "end",
                values=(
                    r["employee_name"],
                    r["invoice_count"],
                    f"P{float(r['total_sales']):,.2f}",
                    f"P{float(r['commission']):,.2f}",
                    r["status"],
                ),
                tags=(tag, stag),
            )

    def _generate_payroll(self):
        """Insert employee_payments for hourly timecards AND sales rep commissions."""
        self._ensure_active_session(["Manager"])

        try:
            conn = _get_conn(self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[attr-defined]

            import random, string

            def _check_no():
                return "CHK-" + "".join(random.choices(string.digits, k=6))

            inserted = 0
            week_end = self._week + timedelta(days=6)

            # ── hourly employees ──────────────────────────────────────────────
            cur.execute(
                """
                SELECT e.employee_number, t.timecard_id,
                       ROUND((t.hours_worked * COALESCE(e.hourly_wage,0))::numeric,2)
                           AS gross_pay
                FROM   timecards t
                JOIN   employees e ON e.employee_number = t.employee_number
                WHERE  e.is_active = TRUE
                  AND  e.position  = 'Hourly'
                  AND  t.week_date = %s
            """,
                (self._week,),
            )
            for row in cur.fetchall():
                cur.execute(
                    """
                    INSERT INTO employee_payments
                        (employee_number, timecard_id, check_number,
                         amount_paid, date_paid, payment_type)
                    VALUES (%s, %s, %s, %s, CURRENT_DATE, 'hourly')
                    ON CONFLICT DO NOTHING
                """,
                    (
                        row["employee_number"],
                        row["timecard_id"],
                        _check_no(),
                        row["gross_pay"],
                    ),
                )
                inserted += 1

            # ── sales reps — commission ───────────────────────────────────────
            cur.execute(
                """
                SELECT e.employee_number,
                       COALESCE(SUM(i.total_amount), 0) * 0.05 AS commission
                FROM   employees e
                LEFT JOIN invoices i
                       ON  i.employee_number = e.employee_number
                       AND i.date_written BETWEEN %s AND %s
                       AND i.status <> 'void'
                WHERE  e.is_active = TRUE
                  AND  e.position  = 'Sales Rep'
                GROUP  BY e.employee_number
                HAVING COALESCE(SUM(i.total_amount), 0) > 0
            """,
                (self._week, week_end),
            )
            for row in cur.fetchall():
                cur.execute(
                    """
                    SELECT 1 FROM employee_payments
                    WHERE  employee_number    = %s
                      AND  payment_type       = 'commission'
                      AND  invoice_period_end = %s
                """,
                    (row["employee_number"], week_end),
                )
                if cur.fetchone():
                    continue
                cur.execute(
                    """
                    INSERT INTO employee_payments
                        (employee_number, invoice_period_end, check_number,
                         amount_paid, date_paid, payment_type)
                    VALUES (%s, %s, %s, %s, CURRENT_DATE, 'commission')
                """,
                    (row["employee_number"], week_end, _check_no(), row["commission"]),
                )
                inserted += 1

            # ── update YTD sales for all reps ─────────────────────────────────
            cur.execute("""
                UPDATE employees e
                SET    ytdsales = COALESCE(sub.total_sales, 0)
                FROM (
                    SELECT e2.employee_number,
                           SUM(i.total_amount) AS total_sales
                    FROM   employees e2
                    LEFT JOIN invoices i
                           ON  i.employee_number = e2.employee_number
                           AND i.date_written >= DATE_TRUNC('year', CURRENT_DATE)
                           AND i.status <> 'void'
                    WHERE  e2.position = 'Sales Rep'
                    GROUP  BY e2.employee_number
                ) sub
                WHERE e.employee_number = sub.employee_number
                  AND e.position = 'Sales Rep'
            """)

            conn.commit()
            cur.close()
            conn.close()

            self._proc_btn.configure(
                text="Checks Generated", fg_color="#1a7a40", state="disabled"
            )
            messagebox.showinfo(
                "Payroll",
                f"Payroll generated successfully.\n"
                f"{inserted} check(s) issued "
                f"(hourly + commission).",
            )
            self._load_db()

        except Exception as e:
            messagebox.showerror("DB Error", f"Payroll generation failed:\n{e}")

    def _export_csv(self):
        """Export this week's payroll to CSV: hourly gross + rep commission."""
        import csv
        from tkinter import filedialog

        week_end = self._week + timedelta(days=6)

        try:
            conn = _get_conn(self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[attr-defined]

            # Hourly employees
            cur.execute(
                """
                SELECT e.employee_number, e.employee_name,
                       'Hourly' AS pay_type,
                       ROUND((t.hours_worked * COALESCE(e.hourly_wage,0))::numeric,2)
                           AS gross,
                       0.00 AS commission
                FROM   timecards t
                JOIN   employees e ON e.employee_number = t.employee_number
                WHERE  e.is_active = TRUE
                  AND  e.position  = 'Hourly'
                  AND  t.week_date = %s
            """,
                (self._week,),
            )
            hourly_rows = cur.fetchall()

            # Sales reps
            cur.execute(
                """
                SELECT e.employee_number, e.employee_name,
                       'Sales Rep' AS pay_type,
                       0.00 AS gross,
                       ROUND((COALESCE(SUM(i.total_amount),0) * 0.05)::numeric,2)
                           AS commission
                FROM   employees e
                LEFT JOIN invoices i
                       ON  i.employee_number = e.employee_number
                       AND i.date_written BETWEEN %s AND %s
                       AND i.status <> 'void'
                WHERE  e.is_active = TRUE
                  AND  e.position  = 'Sales Rep'
                GROUP  BY e.employee_number, e.employee_name
            """,
                (self._week, week_end),
            )
            rep_rows = cur.fetchall()

            cur.close()
            conn.close()

        except Exception as e:
            messagebox.showerror("DB Error", f"Export failed:\n{e}")
            return

        # Ask user where to save
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"payroll_{self._week.strftime('%Y-%m-%d')}.csv",
            title="Save Payroll CSV",
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "Employee Number",
                        "Employee Name",
                        "Pay Type",
                        "Gross Pay",
                        "Commission",
                        "Net Pay",
                    ]
                )
                for r in hourly_rows:
                    gross = float(r["gross"])
                    writer.writerow(
                        [
                            r["employee_number"],
                            r["employee_name"],
                            r["pay_type"],
                            f"{gross:.2f}",
                            "0.00",
                            f"{gross:.2f}",
                        ]
                    )
                for r in rep_rows:
                    comm = float(r["commission"])
                    writer.writerow(
                        [
                            r["employee_number"],
                            r["employee_name"],
                            r["pay_type"],
                            "0.00",
                            f"{comm:.2f}",
                            f"{comm:.2f}",
                        ]
                    )
            messagebox.showinfo(
                "Export Successful", f"Payroll exported to:\n{filepath}"
            )
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not write file:\n{e}")


# ─────────────────────────────────────────────────────────────────────────────
# PANEL 3 — Timecard Entry  (Hourly employees)
# ─────────────────────────────────────────────────────────────────────────────
class _TimecardPanel(ctk.CTkFrame):
    def __init__(self, parent, db_config, employee_number=None, session_manager=None):
        super().__init__(parent, fg_color="transparent")
        self.db_config = db_config
        self.employee_number = employee_number
        self._session_manager = session_manager
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        today = date.today()
        self._week = today - timedelta(days=today.weekday())

        if employee_number:
            self._build_profile_card()

        # ── submit form ───────────────────────────────────────────────────────
        form = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )
        form.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        ctk.CTkLabel(
            form,
            text="Submit Timecard",
            font=("Segoe UI", 15, "bold"),
            text_color="#2c3e50",
        ).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkLabel(
            form,
            text="Enter hours worked for the current week",
            font=("Segoe UI", 11),
            text_color="#7f8c8d",
        ).pack(anchor="w", padx=16, pady=(0, 10))

        frow = ctk.CTkFrame(form, fg_color="transparent")
        frow.pack(fill="x", padx=16, pady=(0, 14))
        frow.grid_columnconfigure((0, 1, 2), weight=1)

        def _field(col, label, default="", placeholder=""):
            f = ctk.CTkFrame(frow, fg_color="transparent")
            f.grid(row=0, column=col, sticky="ew", padx=(0, 10))
            ctk.CTkLabel(
                f, text=label, font=("Segoe UI", 11, "bold"), text_color="#34495e"
            ).pack(anchor="w")
            e = ctk.CTkEntry(
                f,
                placeholder_text=placeholder,
                height=36,
                fg_color="#f8f9fa",
                border_color="#d0d7de",
                border_width=1,
                text_color="#1c2128",
                font=("Segoe UI", 12),
            )
            e.pack(fill="x", pady=(4, 0))
            if default:
                e.insert(0, default)
            return e

        week_field = _field(0, "Week Starting", self._week.strftime("%b %d, %Y"))
        week_field.configure(state="disabled", fg_color="#f0f0f0", text_color="#7f8c8d")
        self._hours = _field(1, "Hours Worked", placeholder="e.g. 40")
        self._notes = _field(
            2, "Notes (optional)", placeholder="Overtime, sick leave..."
        )

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(anchor="e", padx=16, pady=(0, 14))

        ctk.CTkButton(
            btn_row,
            text="↻  Refresh",
            height=36,
            width=100,
            fg_color="#ebf3fb",
            hover_color="#dbe9f9",
            text_color="#1f5f9f",
            font=("Segoe UI", 12),
            corner_radius=8,
            command=self._load_history,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="Submit Timecard",
            height=36,
            width=170,
            fg_color="#3498db",
            hover_color="#2980b9",
            text_color="#ffffff",
            font=("Segoe UI", 12, "bold"),
            corner_radius=8,
            command=self._submit,
        ).pack(side="left")

        # ── history table ─────────────────────────────────────────────────────
        hist = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )
        hist.grid(row=2, column=0, sticky="nsew")
        hist.grid_columnconfigure(0, weight=1)
        hist.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            hist,
            text="Submission History",
            font=("Segoe UI", 14, "bold"),
            text_color="#2c3e50",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        style = ttk.Style()
        style.configure(
            "TC.Treeview",
            font=("Segoe UI", 11),
            rowheight=32,
            background="#ffffff",
            fieldbackground="#ffffff",
            borderwidth=0,
        )
        style.configure(
            "TC.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            background="#2c3e50",
            foreground="#ffffff",
            relief="flat",
        )

        cols = ("Week Starting", "Hours", "Gross Pay", "Status")
        self._ht = ttk.Treeview(
            hist, columns=cols, show="headings", height=10, style="TC.Treeview"
        )
        for col, w, anc in [
            ("Week Starting", 200, "w"),
            ("Hours", 90, "center"),
            ("Gross Pay", 120, "center"),
            ("Status", 100, "center"),
        ]:
            self._ht.heading(col, text=col)
            self._ht.column(col, width=w, anchor=anc)  # type: ignore[arg-type]

        self._ht.tag_configure("even", background="#ffffff", foreground="#2c3e50")
        self._ht.tag_configure("odd", background="#f2f4f7", foreground="#2c3e50")
        self._ht.tag_configure("paid", foreground="#1e8449")
        self._ht.tag_configure("pending", foreground="#d35400")

        vsb = ttk.Scrollbar(hist, orient="vertical", command=self._ht.yview)
        self._ht.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns", pady=(0, 10))
        self._ht.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(0, 10))

        self._load_history()

    def _ensure_active_session(self, allowed_roles=None):
        """Enforce session validity before timecard mutations."""
        if self._session_manager is not None:
            self._session_manager.ensure_active(allowed_roles)

    def _build_profile_card(self):
        card = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )
        card.grid(row=0, column=0, sticky="ew", pady=(0, 14))

        if psycopg2 is None:
            return

        try:
            conn = _get_conn(self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[attr-defined]
            cur.execute(
                """
                SELECT employee_name, position, hourly_wage
                FROM   employees
                WHERE  employee_number = %s
            """,
                (self.employee_number,),
            )
            emp = cur.fetchone()
            cur.close()
            conn.close()
        except Exception:
            emp = None

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(row, text="👤", font=("Segoe UI", 36)).pack(
            side="left", padx=(0, 14)
        )
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left")

        if emp:
            ctk.CTkLabel(
                info,
                text=emp["employee_name"],
                font=("Segoe UI", 16, "bold"),
                text_color="#2c3e50",
            ).pack(anchor="w")
            ctk.CTkLabel(
                info,
                text="Regular" if emp["position"] == "Hourly" else emp["position"],
                font=("Segoe UI", 12),
                text_color="#7f8c8d",
            ).pack(anchor="w")
            wage = f"P{emp['hourly_wage']:.2f}/hr" if emp["hourly_wage"] else "N/A"
            ctk.CTkLabel(
                info,
                text=f"Hourly Rate: {wage}",
                font=("Segoe UI", 11, "bold"),
                text_color="#27ae60",
            ).pack(anchor="w")
        else:
            ctk.CTkLabel(
                info,
                text="Employee data unavailable",
                font=("Segoe UI", 12),
                text_color="#e74c3c",
            ).pack(anchor="w")

    def _load_history(self):
        for iid in self._ht.get_children():
            self._ht.delete(iid)

        if psycopg2 is None:
            return

        try:
            conn = _get_conn(self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[attr-defined]

            if self.employee_number:
                cur.execute(
                    """
                    SELECT t.week_date,
                           t.hours_worked,
                           ROUND((t.hours_worked *
                               COALESCE(e.hourly_wage,0))::numeric,2) AS gross,
                           CASE WHEN ep.payment_id IS NOT NULL
                                THEN 'Paid' ELSE 'Pending' END AS status
                    FROM   timecards t
                    JOIN   employees e  ON e.employee_number = t.employee_number
                    LEFT JOIN employee_payments ep
                           ON ep.timecard_id = t.timecard_id
                    WHERE  t.employee_number = %s
                    ORDER  BY t.week_date DESC
                    LIMIT  10
                """,
                    (self.employee_number,),
                )
            else:
                cur.execute("""
                    SELECT t.week_date,
                           e.employee_name,
                           t.hours_worked,
                           ROUND((t.hours_worked *
                               COALESCE(e.hourly_wage,0))::numeric,2) AS gross,
                           CASE WHEN ep.payment_id IS NOT NULL
                                THEN 'Paid' ELSE 'Pending' END AS status
                    FROM   timecards t
                    JOIN   employees e  ON e.employee_number = t.employee_number
                    LEFT JOIN employee_payments ep
                           ON ep.timecard_id = t.timecard_id
                    WHERE  e.position = 'Hourly'
                    ORDER  BY t.week_date DESC
                    LIMIT  20
                """)
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("DB Error", f"History load failed:\n{e}")
            return

        for idx, r in enumerate(rows):
            tag = "even" if idx % 2 == 0 else "odd"
            stag = "paid" if r["status"] == "Paid" else "pending"
            self._ht.insert(
                "",
                "end",
                values=(
                    r["week_date"].strftime("%b %d, %Y"),
                    f"{r['hours_worked']} hrs",
                    f"P{r['gross']:,.2f}",
                    r["status"],
                ),
                tags=(tag, stag),
            )

    def _submit(self):
        hrs_str = self._hours.get().strip()
        if not hrs_str:
            messagebox.showwarning("Input Error", "Please enter hours worked.")
            return
        try:
            hrs = float(hrs_str)
            if hrs < 0 or hrs > 168:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Input", "Hours must be a number between 0 and 168."
            )
            return

        if not self.employee_number:
            messagebox.showwarning("Error", "No employee linked to this session.")
            return

        self._ensure_active_session()

        if psycopg2 is None:
            return

        try:
            conn = _get_conn(self.db_config)
            cur = conn.cursor()
            # UPSERT: insert new or update existing blank timecard for this week
            cur.execute(
                """
                INSERT INTO timecards (employee_number, week_date, hours_worked)
                VALUES (%s, %s, %s)
                ON CONFLICT (employee_number, week_date)
                DO UPDATE SET hours_worked = EXCLUDED.hours_worked
            """,
                (self.employee_number, self._week, hrs),
            )
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo(
                "Success",
                f"Timecard submitted: {hrs} hrs for week of "
                f"{self._week.strftime('%b %d, %Y')}.",
            )
            self._hours.delete(0, "end")
            self._notes.delete(0, "end")
            self._load_history()
        except Exception as e:
            messagebox.showerror("DB Error", f"Timecard submission failed:\n{e}")


# ─────────────────────────────────────────────────────────────────────────────
# PANEL 4 — My Payment History  (Sales Rep self-service)
# ─────────────────────────────────────────────────────────────────────────────
class _SalesRepPanel(ctk.CTkFrame):
    def __init__(self, parent, db_config, employee_number):
        super().__init__(parent, fg_color="transparent")
        self.db_config = db_config
        self.employee_number = employee_number
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_profile()

        card = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text="My Payment History",
            font=("Segoe UI", 14, "bold"),
            text_color="#2c3e50",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        style = ttk.Style()
        style.configure(
            "SR.Treeview",
            font=("Segoe UI", 11),
            rowheight=32,
            background="#ffffff",
            fieldbackground="#ffffff",
            borderwidth=0,
        )
        style.configure(
            "SR.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            background="#2c3e50",
            foreground="#ffffff",
            relief="flat",
        )

        cols = ("Check #", "Type", "Gross Amount", "Date Issued")
        self._tree = ttk.Treeview(
            card, columns=cols, show="headings", height=10, style="SR.Treeview"
        )
        for col, w, anc in [
            ("Check #", 120, "w"),
            ("Type", 110, "w"),
            ("Gross Amount", 130, "center"),
            ("Date Issued", 130, "center"),
        ]:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor=anc, stretch=True)  # type: ignore[arg-type]

        self._tree.tag_configure("even", background="#ffffff", foreground="#2c3e50")
        self._tree.tag_configure("odd", background="#f2f4f7", foreground="#2c3e50")

        vsb = ttk.Scrollbar(card, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns", pady=(0, 10))
        self._tree.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(0, 10))

        self._load_payments()

    def _build_profile(self):
        card = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )
        card.grid(row=0, column=0, sticky="ew", pady=(0, 14))

        try:
            conn = _get_conn(self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[attr-defined]
            cur.execute(
                """
                SELECT employee_name, position, ytdsales, commission_rate
                FROM   employees
                WHERE  employee_number = %s
            """,
                (self.employee_number,),
            )
            emp = cur.fetchone()
            cur.close()
            conn.close()
        except Exception:
            emp = None

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(row, text="👤", font=("Segoe UI", 36)).pack(
            side="left", padx=(0, 14)
        )
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left")

        if emp:
            ctk.CTkLabel(
                info,
                text=emp["employee_name"],
                font=("Segoe UI", 16, "bold"),
                text_color="#2c3e50",
            ).pack(anchor="w")
            ctk.CTkLabel(
                info,
                text=(
                    "Sales Representative"
                    if emp["position"] == "Sales Rep"
                    else emp["position"]
                ),
                font=("Segoe UI", 12),
                text_color="#7f8c8d",
            ).pack(anchor="w")
            comm = float(emp["commission_rate"]) * 100
            ytd = float(emp["ytdsales"])
            ctk.CTkLabel(
                info,
                text=f"Commission Rate: {comm:.1f}%   |   " f"YTD Sales: P{ytd:,.2f}",
                font=("Segoe UI", 11, "bold"),
                text_color="#3498db",
            ).pack(anchor="w")
        else:
            ctk.CTkLabel(
                info,
                text="Employee data unavailable",
                font=("Segoe UI", 12),
                text_color="#e74c3c",
            ).pack(anchor="w")

    def _load_payments(self):
        for iid in self._tree.get_children():
            self._tree.delete(iid)
        try:
            conn = _get_conn(self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[attr-defined]
            cur.execute(
                """
                SELECT check_number, payment_type,
                       amount_paid, date_paid
                FROM   employee_payments
                WHERE  employee_number = %s
                ORDER  BY date_paid DESC
                LIMIT  20
            """,
                (self.employee_number,),
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not load payments:\n{e}")
            return

        if not rows:
            self._tree.insert("", "end", values=("—", "No records yet", "—", "—"))
            return

        for idx, r in enumerate(rows):
            tag = "even" if idx % 2 == 0 else "odd"
            self._tree.insert(
                "",
                "end",
                values=(
                    r["check_number"],
                    r["payment_type"].capitalize(),
                    f"P{r['amount_paid']:,.2f}",
                    r["date_paid"].strftime("%b %d, %Y"),
                ),
                tags=(tag,),
            )


# ─────────────────────────────────────────────────────────────────────────────
# PANEL 5 — Payroll History  (Manager only, 4th tab)
# ─────────────────────────────────────────────────────────────────────────────
class _PayrollHistoryPanel(ctk.CTkFrame):
    """Shows all past employee_payments records — hourly and commission."""

    def __init__(self, parent, db_config):
        super().__init__(parent, fg_color="transparent")
        self.db_config = db_config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            hdr,
            text="Payroll History",
            font=("Segoe UI", 16, "bold"),
            text_color="#2c3e50",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            hdr,
            text="Refresh",
            width=68,
            height=30,
            fg_color="#ebf3fb",
            hover_color="#dbe9f9",
            text_color="#1f5f9f",
            font=("Segoe UI", 11),
            command=self._load_db,
        ).grid(row=0, column=1, sticky="e")

        # ── summary strip ─────────────────────────────────────────────────────
        strip = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )
        strip.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        strip.grid_columnconfigure((0, 1, 2), weight=1)

        self._lbl_total = ctk.CTkLabel(
            strip,
            text="Total Paid: —",
            font=("Segoe UI", 12, "bold"),
            text_color="#1a2d5a",
        )
        self._lbl_total.grid(row=0, column=0, padx=16, pady=12, sticky="w")

        self._lbl_hourly = ctk.CTkLabel(
            strip, text="Hourly Checks: —", font=("Segoe UI", 12), text_color="#27ae60"
        )
        self._lbl_hourly.grid(row=0, column=1, padx=16, pady=12)

        self._lbl_comm = ctk.CTkLabel(
            strip,
            text="Commission Checks: —",
            font=("Segoe UI", 12),
            text_color="#8e44ad",
        )
        self._lbl_comm.grid(row=0, column=2, padx=16, pady=12, sticky="e")

        # ── table card ────────────────────────────────────────────────────────
        card = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )
        card.grid(row=2, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text="All Payment Records",
            font=("Segoe UI", 13, "bold"),
            text_color="#2c3e50",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        style = ttk.Style()
        style.configure(
            "PH.Treeview",
            font=("Segoe UI", 11),
            rowheight=30,
            background="#ffffff",
            fieldbackground="#ffffff",
            borderwidth=0,
        )
        style.configure(
            "PH.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            background="#2c3e50",
            foreground="#ffffff",
            relief="flat",
        )
        style.map(
            "PH.Treeview",
            background=[("selected", "#d6eaf8")],
            foreground=[("selected", "#1a252f")],
        )

        cols = ("Date Paid", "Employee", "Type", "Check #", "Amount")
        self._tree = ttk.Treeview(
            card, columns=cols, show="headings", height=12, style="PH.Treeview"
        )
        for col, w, anc, stretch in [
            ("Date Paid", 150, "center", False),
            ("Employee", 110, "w", True),
            ("Type", 100, "w", True),
            ("Check #", 100, "w", True),
            ("Amount", 120, "w", True),
        ]:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor=anc, stretch=stretch)  # type: ignore[arg-type]

        self._tree.tag_configure("even", background="#ffffff", foreground="#2c3e50")
        self._tree.tag_configure("odd", background="#f7f9fb", foreground="#2c3e50")
        self._tree.tag_configure("hourly", foreground="#1e8449")
        self._tree.tag_configure("commission", foreground="#6c3483")

        vsb = ttk.Scrollbar(card, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns", padx=(0, 6), pady=8)
        self._tree.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=8)

        self._load_db()

    def _load_db(self):
        for iid in self._tree.get_children():
            self._tree.delete(iid)

        try:
            conn = _get_conn(self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[attr-defined]
            cur.execute("""
                SELECT ep.date_paid,
                       e.employee_name,
                       ep.payment_type,
                       ep.check_number,
                       ep.amount_paid
                FROM   employee_payments ep
                JOIN   employees e ON e.employee_number = ep.employee_number
                ORDER  BY ep.date_paid DESC, e.employee_name
            """)
            rows = cur.fetchall()

            cur.execute("""
                SELECT payment_type,
                       COUNT(*)         AS cnt,
                       SUM(amount_paid) AS total
                FROM   employee_payments
                GROUP  BY payment_type
            """)
            summary = {r["payment_type"]: r for r in cur.fetchall()}
            cur.close()
            conn.close()

        except Exception as e:
            messagebox.showerror("DB Error", f"Could not load payroll history:\n{e}")
            return

        h = summary.get("hourly", {})
        c = summary.get("commission", {})
        grand = float(h.get("total", 0) or 0) + float(c.get("total", 0) or 0)
        self._lbl_total.configure(text=f"Total Paid: P{grand:,.2f}")
        self._lbl_hourly.configure(
            text=f"Hourly Checks: {h.get('cnt', 0)}  "
            f"(P{float(h.get('total', 0) or 0):,.2f})"
        )
        self._lbl_comm.configure(
            text=f"Commission Checks: {c.get('cnt', 0)}  "
            f"(P{float(c.get('total', 0) or 0):,.2f})"
        )

        if not rows:
            self._tree.insert(
                "", "end", values=("—", "No payroll records yet", "—", "—", "—")
            )
            return

        for idx, r in enumerate(rows):
            tag = "even" if idx % 2 == 0 else "odd"
            ptag = r["payment_type"]
            self._tree.insert(
                "",
                "end",
                values=(
                    r["date_paid"].strftime("%b %d, %Y"),
                    r["employee_name"],
                    r["payment_type"].capitalize(),
                    r["check_number"],
                    f"P{r['amount_paid']:,.2f}",
                ),
                tags=(tag, ptag),
            )


# ─────────────────────────────────────────────────────────────────────────────
# PayrollView — top-level, RBAC routing
# ─────────────────────────────────────────────────────────────────────────────
class PayrollView(ctk.CTkFrame):
    """
    RBAC routing:
      role="Manager"  → Worker Files + Audit & Processing + Timecard Entry + Payroll History
      role="Hourly"   → Profile card + Timecard Entry + History
      role="Sales Rep"→ Profile card + Payment History
    """

    def __init__(
        self, parent, controller, role="Manager", db_config=None, employee_number=None
    ):
        super().__init__(parent, fg_color="#f8f9fa")
        self.controller = controller
        self.role = role
        self.db_config = db_config or {}
        self.employee_number = employee_number
        self._session_manager = getattr(controller, "session_manager", None)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # ── header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=30, pady=(22, 0))
        hdr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            hdr,
            text="Payroll Manager",
            font=("Segoe UI", 26, "bold"),
            text_color="#2c3e50",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            hdr,
            text=datetime.now().strftime("%A, %B %d %Y"),
            font=("Segoe UI", 12),
            text_color="#7f8c8d",
        ).grid(row=0, column=1, sticky="e")

        # ── summary strip (Manager only) ──────────────────────────────────────
        if role == "Manager":
            strip = ctk.CTkFrame(self, fg_color="transparent")
            strip.grid(row=1, column=0, sticky="ew", padx=30, pady=(14, 0))
            strip.grid_columnconfigure((0, 1, 2, 3), weight=1)
            self._cards = {}
            for col, (key, title, val, sub, clr) in enumerate(
                [
                    ("emp", "Total Employees", "...", "Active", "#3498db"),
                    ("miss", "Missing Timecards", "...", "This week", "#e74c3c"),
                    (
                        "gross",
                        "Est. Gross Payroll",
                        "...",
                        "This week hourly",
                        "#27ae60",
                    ),
                    ("rate", "Avg Hourly Rate", "...", "Hourly employees", "#8e44ad"),
                ]
            ):
                c = _SummaryCard(strip, title, val, sub, clr)
                c.grid(
                    row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 10, 0)
                )
                self._cards[key] = c
            self._refresh_summary()

        # ── tab bar or direct view ────────────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0
        )
        self._scroll.grid(row=3, column=0, sticky="nsew", padx=30, pady=(12, 20))
        self._scroll.grid_columnconfigure(0, weight=1)

        if role == "Manager":
            self._build_tab_bar()
        elif role == "Hourly":
            _TimecardPanel(
                self._scroll,
                self.db_config,
                self.employee_number,
                self._session_manager,
            ).grid(row=0, column=0, sticky="nsew")
        elif role == "Sales Rep":
            _SalesRepPanel(self._scroll, self.db_config, self.employee_number).grid(
                row=0, column=0, sticky="nsew"
            )
        else:
            ctk.CTkLabel(
                self._scroll,
                text="Access restricted for your role.",
                font=("Segoe UI", 14),
                text_color="#e74c3c",
            ).grid(row=0, column=0, pady=40)

    def _build_tab_bar(self):
        tab_row = ctk.CTkFrame(self, fg_color="transparent")
        tab_row.grid(row=2, column=0, sticky="ew", padx=30, pady=(16, 0))

        self._tab_btns = {}
        tabs = [
            ("worker_files", "Worker Files"),
            ("audit", "Payroll Audit & Processing"),
            ("timecard", "Timecard Entry"),
            ("history", "Payroll History"),
        ]
        for key, label in tabs:
            btn = ctk.CTkButton(
                tab_row,
                text=label,
                height=34,
                corner_radius=8,
                fg_color="#e8eef5",
                hover_color="#d7e3f0",
                text_color="#2c3e50",
                font=("Segoe UI", 12),
                command=lambda k=key: self._switch(k),
            )
            btn.pack(side="left", padx=(0, 8))
            self._tab_btns[key] = btn

        self._switch("worker_files")

    def _switch(self, key):
        for k, b in self._tab_btns.items():
            b.configure(
                fg_color="#3498db" if k == key else "#e8eef5",
                text_color="#ffffff" if k == key else "#2c3e50",
            )
        for w in self._scroll.winfo_children():
            w.destroy()

        panel = {
            "worker_files": lambda: _WorkerFilesPanel(self._scroll, self.db_config),
            "audit": lambda: _AuditPanel(
                self._scroll, self.db_config, self._session_manager
            ),
            "timecard": lambda: _TimecardPanel(
                self._scroll, self.db_config, None, self._session_manager
            ),
            "history": lambda: _PayrollHistoryPanel(self._scroll, self.db_config),
        }[key]()
        panel.grid(row=0, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

    def _refresh_summary(self):
        try:
            conn = _get_conn(self.db_config)
            cur = conn.cursor()
            today = date.today()
            week = today - timedelta(days=today.weekday())

            cur.execute("SELECT COUNT(*) FROM employees WHERE is_active=TRUE")
            result = cur.fetchone()
            emp_count = result[0] if result else 0

            cur.execute(
                """
                SELECT COUNT(*) FROM employees e
                LEFT JOIN timecards t
                    ON t.employee_number=e.employee_number AND t.week_date=%s
                WHERE e.is_active=TRUE AND e.position='Hourly'
                  AND t.timecard_id IS NULL
            """,
                (week,),
            )
            result = cur.fetchone()
            missing = result[0] if result else 0  # type: ignore[index]

            cur.execute(
                """
                SELECT COALESCE(SUM(t.hours_worked*COALESCE(e.hourly_wage,0)),0)
                FROM timecards t
                JOIN employees e ON e.employee_number=t.employee_number
                WHERE e.position='Hourly' AND t.week_date=%s
            """,
                (week,),
            )
            result = cur.fetchone()
            gross = result[0] if result else 0  # type: ignore[index]

            cur.execute("""
                SELECT COALESCE(AVG(hourly_wage),0) FROM employees
                WHERE  is_active=TRUE AND position='Hourly'
            """)
            result_avg = cur.fetchone()
            avg_wage = result_avg[0] if result_avg else 0

            cur.close()
            conn.close()

            self._cards["emp"].update_value(str(emp_count))
            self._cards["miss"].update_value(str(missing))
            self._cards["gross"].update_value(f"P{float(gross):,.2f}")
            self._cards["rate"].update_value(f"P{float(avg_wage):,.2f}")

        except Exception:
            pass
