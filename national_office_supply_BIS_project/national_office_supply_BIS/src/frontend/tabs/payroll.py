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


# ─────────────────────────────────────────────────────────────────────────────
# Reusable Summary Card
# ─────────────────────────────────────────────────────────────────────────────
class _SummaryCard(ctk.CTkFrame):
    def __init__(self, parent, title, value, sub, color="#3498db"):
        super().__init__(parent, fg_color="#ffffff", corner_radius=12,
                         border_width=1, border_color="#e0e0e0")
        ctk.CTkLabel(self, text=title, font=("Segoe UI", 11, "bold"),
                     text_color="#7f8c8d").pack(anchor="w", padx=14, pady=(12, 0))
        self._val_lbl = ctk.CTkLabel(self, text=value, font=("Segoe UI", 22, "bold"),
                                     text_color="#2c3e50")
        self._val_lbl.pack(anchor="w", padx=14, pady=(2, 0))
        ctk.CTkLabel(self, text=sub, font=("Segoe UI", 10),
                     text_color=color).pack(anchor="w", padx=14, pady=(0, 12))

    def update_value(self, value):
        self._val_lbl.configure(text=value)


# ─────────────────────────────────────────────────────────────────────────────
# PANEL 1 — Worker Files  (Manager only)
# ─────────────────────────────────────────────────────────────────────────────
class _WorkerFilesPanel(ctk.CTkFrame):
    def __init__(self, parent, db_config):
        super().__init__(parent, fg_color="transparent")
        self.db_config   = db_config
        self._revealed   = {}
        self._search_var = ctk.StringVar()
        self._all_rows   = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr, text="Employee Worker Files",
                     font=("Segoe UI", 16, "bold"),
                     text_color="#2c3e50").grid(row=0, column=0, sticky="w")

        sf = ctk.CTkFrame(hdr, fg_color="transparent")
        sf.grid(row=0, column=1, sticky="e")
        ctk.CTkEntry(sf, textvariable=self._search_var,
                     placeholder_text="Search employees...",
                     width=210, height=32, fg_color="#ffffff",
                     border_color="#d0d7de", border_width=1,
                     text_color="#1c2128", font=("Segoe UI", 12)
                     ).pack(side="left", padx=(0, 6))
        self._search_var.trace_add("write", lambda *_: self._filter())
        ctk.CTkButton(sf, text="Filter", width=58, height=32,
                      fg_color="#e8eef5", hover_color="#d7e3f0",
                      text_color="#2c3e50", font=("Segoe UI", 11),
                      command=self._filter).pack(side="left")
        ctk.CTkButton(sf, text="Refresh", width=68, height=32,
                      fg_color="#ebf3fb", hover_color="#dbe9f9",
                      text_color="#1f5f9f", font=("Segoe UI", 11),
                      command=self._load_db).pack(side="left", padx=(6, 0))

        # ── table card ────────────────────────────────────────────────────────
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

        # reveal row
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.grid(row=1, column=0, columnspan=2, sticky="ew",
                     padx=10, pady=(0, 10))
        ctk.CTkLabel(btn_row, text="Select a row then:",
                     font=("Segoe UI", 11), text_color="#7f8c8d").pack(side="left")
        ctk.CTkButton(btn_row, text="Show / Hide SSN",
                      width=140, height=28,
                      fg_color="#ebf3fb", hover_color="#dbe9f9",
                      text_color="#1f5f9f", font=("Segoe UI", 11),
                      corner_radius=6,
                      command=self._toggle_ssn).pack(side="left", padx=8)

        self._load_db()

    # ── DB load ───────────────────────────────────────────────────────────────
    def _load_db(self):
        try:
            conn = _get_conn(self.db_config)
            cur  = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
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
            cur.close(); conn.close()

            # Mask SSN for display
            self._all_rows = [
                (r["employee_name"], r["position"], r["hourly_wage"],
                 "***-**-" + r["ssn"][-4:])
                for r in rows
            ]
            # Store full SSN separately keyed by index
            self._full_ssns = {i: r["ssn"] for i, r in enumerate(rows)}

        except Exception as e:
            messagebox.showerror("DB Error", f"Could not load employees:\n{e}")
            self._all_rows = []
            self._full_ssns = {}

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
        data = [r for r in self._all_rows
                if any(q in str(v).lower() for v in r)]
        self._render(data)

    def _toggle_ssn(self):
        sel = self.tree.selection()
        if not sel:
            return
        iid  = sel[0]
        vals = list(self.tree.item(iid, "values"))
        if self._revealed.get(iid, False):
            last4   = vals[3][-4:]
            vals[3] = f"***-**-{last4}"
            self._revealed[iid] = False
        else:
            # Find full SSN from _full_ssns by matching row index
            children = list(self.tree.get_children())
            idx      = children.index(iid)
            full     = self._full_ssns.get(idx, vals[3])
            vals[3]  = full
            self._revealed[iid] = True
        self.tree.item(iid, values=vals)


# ─────────────────────────────────────────────────────────────────────────────
# PANEL 2 — Payroll Audit & Processing  (Manager only)
# ─────────────────────────────────────────────────────────────────────────────
class _AuditPanel(ctk.CTkFrame):
    def __init__(self, parent, db_config):
        super().__init__(parent, fg_color="transparent")
        self.db_config = db_config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        today      = date.today()
        self._week = today - timedelta(days=today.weekday())   # Monday
        sun        = self._week + timedelta(days=6)
        week_str   = f"Week: {self._week.strftime('%b %d')} - {sun.strftime('%b %d, %Y')}"

        # week banner
        banner = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12,
                              border_width=1, border_color="#e0e0e0")
        banner.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        brow = ctk.CTkFrame(banner, fg_color="transparent")
        brow.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(brow, text="Payroll Audit & Processing",
                     font=("Segoe UI", 16, "bold"),
                     text_color="#2c3e50").pack(side="left")
        ctk.CTkLabel(brow, text=week_str,
                     font=("Segoe UI", 11),
                     text_color="#7f8c8d").pack(side="right")

        # two-column body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_rowconfigure(0, weight=1)

        # LEFT – missing timecards (QD-Sec1)
        self._left_card = ctk.CTkFrame(body, fg_color="#ffffff",
                                       corner_radius=12, border_width=1,
                                       border_color="#e0e0e0")
        self._left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._missing_title = ctk.CTkLabel(
            self._left_card, text="Missing Timecards: loading...",
            font=("Segoe UI", 13, "bold"), text_color="#e74c3c")
        self._missing_title.pack(anchor="w", padx=16, pady=(14, 8))
        self._missing_body = ctk.CTkFrame(self._left_card, fg_color="transparent")
        self._missing_body.pack(fill="x")

        # RIGHT – totals + buttons
        right_card = ctk.CTkFrame(body, fg_color="#ffffff", corner_radius=12,
                                  border_width=1, border_color="#e0e0e0",
                                  width=240)
        right_card.grid(row=0, column=1, sticky="ns")
        right_card.grid_propagate(False)

        ctk.CTkLabel(right_card, text="Estimated Gross Payroll",
                     font=("Segoe UI", 10),
                     text_color="#5d7ab5").pack(pady=(18, 0))
        self._total_lbl = ctk.CTkLabel(right_card, text="P0.00",
                                       font=("Segoe UI", 22, "bold"),
                                       text_color="#1a2d5a")
        self._total_lbl.pack(pady=(2, 12))

        self._warn_lbl = ctk.CTkLabel(right_card, text="",
                                      font=("Segoe UI", 10),
                                      text_color="#92400e",
                                      fg_color="#fffbeb", corner_radius=8,
                                      wraplength=200, justify="center")
        self._warn_lbl.pack(fill="x", padx=14, pady=(0, 12))

        self._proc_btn = ctk.CTkButton(
            right_card, text="Generate Weekly Checks",
            height=44, fg_color="#27ae60", hover_color="#1e8449",
            text_color="#ffffff", font=("Segoe UI", 12, "bold"),
            corner_radius=10, command=self._generate_payroll)
        self._proc_btn.pack(fill="x", padx=14, pady=(0, 8))

        ctk.CTkButton(right_card, text="Refresh",
                      height=30, fg_color="#ebf3fb", hover_color="#dbe9f9",
                      text_color="#1f5f9f", font=("Segoe UI", 11),
                      corner_radius=8, command=self._load_db
                      ).pack(fill="x", padx=14, pady=(0, 14))

        self._load_db()

    def _load_db(self):
        # QD-Sec1: missing timecards
        try:
            conn = _get_conn(self.db_config)
            cur  = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            cur.execute("""
                SELECT e.employee_name, e.position
                FROM   employees e
                LEFT JOIN timecards t
                    ON  t.employee_number = e.employee_number
                    AND t.week_date = %s
                WHERE  e.is_active = TRUE
                  AND  e.position  = 'Hourly'
                  AND  t.timecard_id IS NULL
                ORDER  BY e.employee_name
            """, (self._week,))
            missing = cur.fetchall()

            # QD-Sec2: estimated gross for completed timecards
            cur.execute("""
                SELECT COALESCE(SUM(t.hours_worked * COALESCE(e.hourly_wage,0)),0)
                       AS gross
                FROM   timecards t
                JOIN   employees e ON e.employee_number = t.employee_number
                WHERE  e.is_active = TRUE
                  AND  e.position  = 'Hourly'
                  AND  t.week_date = %s
            """, (self._week,))
            gross = cur.fetchone()[0] or 0

            cur.close(); conn.close()

        except Exception as e:
            messagebox.showerror("DB Error", f"Audit load failed:\n{e}")
            missing, gross = [], 0

        # rebuild missing list
        for w in self._missing_body.winfo_children():
            w.destroy()

        self._missing_title.configure(
            text=f"Missing Timecards: {len(missing)} Hourly Employees")

        for row in missing:
            f = ctk.CTkFrame(self._missing_body, fg_color="#fff8f8",
                             corner_radius=8)
            f.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(f, text="!", font=("Segoe UI", 14, "bold"),
                         text_color="#e74c3c").pack(side="left", padx=(10, 6))
            info = ctk.CTkFrame(f, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=8)
            ctk.CTkLabel(info, text=row["employee_name"],
                         font=("Segoe UI", 12, "bold"),
                         text_color="#2c3e50").pack(anchor="w")
            ctk.CTkLabel(info, text=row["position"],
                         font=("Segoe UI", 10),
                         text_color="#7f8c8d").pack(anchor="w")
            ctk.CTkLabel(f, text="Missing", font=("Segoe UI", 9, "bold"),
                         text_color="#ffffff", fg_color="#e74c3c",
                         corner_radius=4, width=60, height=20
                         ).pack(side="right", padx=10)

        ctk.CTkFrame(self._missing_body,
                     fg_color="transparent", height=8).pack()

        self._total_lbl.configure(text=f"P{gross:,.2f}")
        if missing:
            self._warn_lbl.configure(
                text=f"{len(missing)} timecards missing\nReview before processing")
        else:
            self._warn_lbl.configure(text="All timecards submitted!")

    def _generate_payroll(self):
        """Insert employee_payments rows for all hourly timecards this week."""
        try:
            conn = _get_conn(self.db_config)
            cur  = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Fetch timecards for the week (QD-Sec2)
            cur.execute("""
                SELECT e.employee_number, e.employee_name,
                       t.timecard_id,
                       ROUND((t.hours_worked * COALESCE(e.hourly_wage,0))::numeric,2)
                           AS gross_pay
                FROM   timecards t
                JOIN   employees e ON e.employee_number = t.employee_number
                WHERE  e.is_active = TRUE
                  AND  e.position  = 'Hourly'
                  AND  t.week_date = %s
            """, (self._week,))
            rows = cur.fetchall()

            if not rows:
                messagebox.showinfo("Payroll",
                                    "No completed timecards found for this week.")
                cur.close(); conn.close()
                return

            import random, string
            inserted = 0
            for row in rows:
                check_no = "CHK-" + "".join(
                    random.choices(string.digits, k=6))
                cur.execute("""
                    INSERT INTO employee_payments
                        (employee_number, timecard_id, check_number,
                         amount_paid, date_paid, payment_type)
                    VALUES (%s, %s, %s, %s, CURRENT_DATE, 'hourly')
                    ON CONFLICT DO NOTHING
                """, (row["employee_number"], row["timecard_id"],
                      check_no, row["gross_pay"]))
                inserted += 1

            conn.commit()
            cur.close(); conn.close()
            self._proc_btn.configure(text="Checks Generated",
                                     fg_color="#1a7a40", state="disabled")
            messagebox.showinfo("Payroll",
                                f"Weekly payroll generated.\n"
                                f"{inserted} check(s) issued.")
            self._load_db()

        except Exception as e:
            messagebox.showerror("DB Error", f"Payroll generation failed:\n{e}")


# ─────────────────────────────────────────────────────────────────────────────
# PANEL 3 — Timecard Entry  (Hourly employees)
# ─────────────────────────────────────────────────────────────────────────────
class _TimecardPanel(ctk.CTkFrame):
    def __init__(self, parent, db_config, employee_number=None):
        super().__init__(parent, fg_color="transparent")
        self.db_config       = db_config
        self.employee_number = employee_number
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        today      = date.today()
        self._week = today - timedelta(days=today.weekday())

        # ── profile card (if employee_number given) ───────────────────────────
        if employee_number:
            self._build_profile_card()

        # ── submit form ───────────────────────────────────────────────────────
        form = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12,
                            border_width=1, border_color="#e0e0e0")
        form.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        ctk.CTkLabel(form, text="Submit Timecard",
                     font=("Segoe UI", 15, "bold"),
                     text_color="#2c3e50").pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkLabel(form,
                     text="Enter hours worked for the current week",
                     font=("Segoe UI", 11),
                     text_color="#7f8c8d").pack(anchor="w", padx=16, pady=(0, 10))

        frow = ctk.CTkFrame(form, fg_color="transparent")
        frow.pack(fill="x", padx=16, pady=(0, 14))
        frow.grid_columnconfigure((0, 1, 2), weight=1)

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

        _field(0, "Week Starting", self._week.strftime("%b %d, %Y"))
        self._hours   = _field(1, "Hours Worked", placeholder="e.g. 40")
        self._notes   = _field(2, "Notes (optional)",
                               placeholder="Overtime, sick leave...")

        ctk.CTkButton(form, text="Submit Timecard",
                      height=36, width=170,
                      fg_color="#3498db", hover_color="#2980b9",
                      text_color="#ffffff", font=("Segoe UI", 12, "bold"),
                      corner_radius=8,
                      command=self._submit).pack(anchor="e", padx=16,
                                                 pady=(0, 14))

        # ── history table ─────────────────────────────────────────────────────
        hist = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12,
                            border_width=1, border_color="#e0e0e0")
        hist.grid(row=2, column=0, sticky="nsew")
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

        cols = ("Week Starting", "Hours", "Gross Pay", "Status")
        self._ht = ttk.Treeview(hist, columns=cols, show="headings",
                                height=5, style="TC.Treeview")
        for col, w, anc in [("Week Starting", 200, "w"),
                             ("Hours", 90, "center"),
                             ("Gross Pay", 120, "e"),
                             ("Status", 100, "center")]:
            self._ht.heading(col, text=col)
            self._ht.column(col, width=w, anchor=anc)

        self._ht.tag_configure("even",     background="#ffffff",
                               foreground="#2c3e50")
        self._ht.tag_configure("odd",      background="#f2f4f7",
                               foreground="#2c3e50")
        self._ht.tag_configure("paid",     foreground="#1e8449")
        self._ht.tag_configure("pending",  foreground="#d35400")

        vsb = ttk.Scrollbar(hist, orient="vertical", command=self._ht.yview)
        self._ht.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns", pady=(0, 10))
        self._ht.grid(row=1, column=0, sticky="nsew",
                      padx=(10, 0), pady=(0, 10))

        self._load_history()

    def _build_profile_card(self):
        """Fetch and display employee's own profile from DB."""
        card = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12,
                            border_width=1, border_color="#e0e0e0")
        card.grid(row=0, column=0, sticky="ew", pady=(0, 14))

        try:
            conn = _get_conn(self.db_config)
            cur  = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT employee_name, position, hourly_wage
                FROM   employees
                WHERE  employee_number = %s
            """, (self.employee_number,))
            emp = cur.fetchone()
            cur.close(); conn.close()
        except Exception:
            emp = None

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(row, text="👤", font=("Segoe UI", 36)).pack(side="left",
                                                                   padx=(0, 14))
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left")

        if emp:
            ctk.CTkLabel(info, text=emp["employee_name"],
                         font=("Segoe UI", 16, "bold"),
                         text_color="#2c3e50").pack(anchor="w")
            ctk.CTkLabel(info, text=emp["position"],
                         font=("Segoe UI", 12),
                         text_color="#7f8c8d").pack(anchor="w")
            wage = f"P{emp['hourly_wage']:.2f}/hr" if emp["hourly_wage"] else "N/A"
            ctk.CTkLabel(info, text=f"Hourly Rate: {wage}",
                         font=("Segoe UI", 11, "bold"),
                         text_color="#27ae60").pack(anchor="w")
        else:
            ctk.CTkLabel(info, text="Employee data unavailable",
                         font=("Segoe UI", 12),
                         text_color="#e74c3c").pack(anchor="w")

    def _load_history(self):
        """Load timecard + payment history from DB."""
        for iid in self._ht.get_children():
            self._ht.delete(iid)

        try:
            conn = _get_conn(self.db_config)
            cur  = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            if self.employee_number:
                cur.execute("""
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
                """, (self.employee_number,))
            else:
                # Manager view — all hourly employees, current week
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
            cur.close(); conn.close()
        except Exception as e:
            messagebox.showerror("DB Error", f"History load failed:\n{e}")
            return

        for idx, r in enumerate(rows):
            tag  = "even" if idx % 2 == 0 else "odd"
            stag = "paid" if r["status"] == "Paid" else "pending"
            if self.employee_number:
                self._ht.insert("", "end",
                                values=(r["week_date"].strftime("%b %d, %Y"),
                                        f"{r['hours_worked']} hrs",
                                        f"P{r['gross']:,.2f}",
                                        r["status"]),
                                tags=(tag, stag))
            else:
                self._ht.insert("", "end",
                                values=(r["week_date"].strftime("%b %d, %Y"),
                                        f"{r['hours_worked']} hrs",
                                        f"P{r['gross']:,.2f}",
                                        r["status"]),
                                tags=(tag, stag))

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
            messagebox.showerror("Invalid Input",
                                 "Hours must be a number between 0 and 168.")
            return

        if not self.employee_number:
            messagebox.showwarning("Error", "No employee linked to this session.")
            return

        try:
            conn = _get_conn(self.db_config)
            cur  = conn.cursor()
            cur.execute("""
                INSERT INTO timecards (employee_number, week_date, hours_worked)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (self.employee_number, self._week, hrs))
            conn.commit()
            cur.close(); conn.close()
            messagebox.showinfo("Success",
                                f"Timecard submitted: {hrs} hrs for week of "
                                f"{self._week.strftime('%b %d, %Y')}.")
            self._hours.delete(0, "end")
            self._load_history()
        except Exception as e:
            messagebox.showerror("DB Error", f"Timecard submission failed:\n{e}")


# ─────────────────────────────────────────────────────────────────────────────
# PANEL 4 — My Payment History  (Sales Rep self-service)
# ─────────────────────────────────────────────────────────────────────────────
class _SalesRepPanel(ctk.CTkFrame):
    def __init__(self, parent, db_config, employee_number):
        super().__init__(parent, fg_color="transparent")
        self.db_config       = db_config
        self.employee_number = employee_number
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # profile card
        self._build_profile()

        # payments table
        card = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12,
                            border_width=1, border_color="#e0e0e0")
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(card, text="My Payment History",
                     font=("Segoe UI", 14, "bold"),
                     text_color="#2c3e50").grid(row=0, column=0, sticky="w",
                                                padx=16, pady=(14, 6))

        style = ttk.Style()
        style.configure("SR.Treeview",
                        font=("Segoe UI", 11), rowheight=32,
                        background="#ffffff", fieldbackground="#ffffff",
                        borderwidth=0)
        style.configure("SR.Treeview.Heading",
                        font=("Segoe UI", 11, "bold"),
                        background="#2c3e50", foreground="#ffffff",
                        relief="flat")

        cols = ("Check #", "Type", "Gross Amount", "Date Issued")
        self._tree = ttk.Treeview(card, columns=cols, show="headings",
                                  height=8, style="SR.Treeview")
        for col, w, anc in [("Check #", 120, "w"), ("Type", 110, "w"),
                             ("Gross Amount", 130, "e"),
                             ("Date Issued", 130, "center")]:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor=anc, stretch=True)

        self._tree.tag_configure("even", background="#ffffff",
                                 foreground="#2c3e50")
        self._tree.tag_configure("odd",  background="#f2f4f7",
                                 foreground="#2c3e50")

        vsb = ttk.Scrollbar(card, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns", pady=(0, 10))
        self._tree.grid(row=1, column=0, sticky="nsew",
                        padx=(10, 0), pady=(0, 10))

        self._load_payments()

    def _build_profile(self):
        card = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12,
                            border_width=1, border_color="#e0e0e0")
        card.grid(row=0, column=0, sticky="ew", pady=(0, 14))

        try:
            conn = _get_conn(self.db_config)
            cur  = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT employee_name, position, ytdsales, commission_rate
                FROM   employees
                WHERE  employee_number = %s
            """, (self.employee_number,))
            emp = cur.fetchone()
            cur.close(); conn.close()
        except Exception:
            emp = None

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(row, text="👤", font=("Segoe UI", 36)).pack(
            side="left", padx=(0, 14))
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left")

        if emp:
            ctk.CTkLabel(info, text=emp["employee_name"],
                         font=("Segoe UI", 16, "bold"),
                         text_color="#2c3e50").pack(anchor="w")
            ctk.CTkLabel(info, text=emp["position"],
                         font=("Segoe UI", 12),
                         text_color="#7f8c8d").pack(anchor="w")
            comm = float(emp["commission_rate"]) * 100
            ytd  = float(emp["ytdsales"])
            ctk.CTkLabel(info,
                         text=f"Commission Rate: {comm:.1f}%   |   "
                              f"YTD Sales: P{ytd:,.2f}",
                         font=("Segoe UI", 11, "bold"),
                         text_color="#3498db").pack(anchor="w")
        else:
            ctk.CTkLabel(info, text="Employee data unavailable",
                         font=("Segoe UI", 12),
                         text_color="#e74c3c").pack(anchor="w")

    def _load_payments(self):
        for iid in self._tree.get_children():
            self._tree.delete(iid)
        try:
            conn = _get_conn(self.db_config)
            cur  = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT check_number, payment_type,
                       amount_paid, date_paid
                FROM   employee_payments
                WHERE  employee_number = %s
                ORDER  BY date_paid DESC
                LIMIT  20
            """, (self.employee_number,))
            rows = cur.fetchall()
            cur.close(); conn.close()
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not load payments:\n{e}")
            return

        if not rows:
            self._tree.insert("", "end",
                              values=("—", "No records yet", "—", "—"))
            return

        for idx, r in enumerate(rows):
            tag = "even" if idx % 2 == 0 else "odd"
            self._tree.insert("", "end",
                              values=(r["check_number"],
                                      r["payment_type"].capitalize(),
                                      f"P{r['amount_paid']:,.2f}",
                                      r["date_paid"].strftime("%b %d, %Y")),
                              tags=(tag,))


# ─────────────────────────────────────────────────────────────────────────────
# PayrollView — top-level, RBAC routing
# ─────────────────────────────────────────────────────────────────────────────
class PayrollView(ctk.CTkFrame):
    """
    RBAC routing:
      role="Manager"  → Worker Files + Audit & Processing + Timecard Entry
      role="Hourly"   → Profile card + Timecard Entry + History
      role="Sales Rep"→ Profile card + Payment History
    """

    def __init__(self, parent, controller, role="Manager",
                 db_config=None, employee_number=None):
        super().__init__(parent, fg_color="#f8f9fa")
        self.controller      = controller
        self.role            = role
        self.db_config       = db_config or {}
        self.employee_number = employee_number

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # ── header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=30, pady=(22, 0))
        hdr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(hdr, text="Payroll Manager",
                     font=("Segoe UI", 26, "bold"),
                     text_color="#2c3e50").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(hdr, text=datetime.now().strftime("%A, %B %d %Y"),
                     font=("Segoe UI", 12),
                     text_color="#7f8c8d").grid(row=0, column=1, sticky="e")

        # ── summary strip (Manager only) ──────────────────────────────────────
        if role == "Manager":
            strip = ctk.CTkFrame(self, fg_color="transparent")
            strip.grid(row=1, column=0, sticky="ew", padx=30, pady=(14, 0))
            strip.grid_columnconfigure((0, 1, 2, 3), weight=1)
            self._cards = {}
            for col, (key, title, val, sub, clr) in enumerate([
                ("emp",   "Total Employees",  "...", "Active",          "#3498db"),
                ("miss",  "Missing Timecards","...", "This week",       "#e74c3c"),
                ("gross", "Est. Gross Payroll","...","This week hourly","#27ae60"),
                ("rate",  "Avg Hourly Rate",  "...", "Hourly employees","#8e44ad"),
            ]):
                c = _SummaryCard(strip, title, val, sub, clr)
                c.grid(row=0, column=col, sticky="nsew",
                       padx=(0 if col == 0 else 10, 0))
                self._cards[key] = c
            self._refresh_summary()

        # ── tab bar or direct view ────────────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0)
        self._scroll.grid(row=3, column=0, sticky="nsew", padx=30,
                          pady=(12, 20))
        self._scroll.grid_columnconfigure(0, weight=1)

        if role == "Manager":
            self._build_tab_bar()
        elif role == "Hourly":
            _TimecardPanel(self._scroll, self.db_config,
                           self.employee_number).grid(
                row=0, column=0, sticky="nsew")
        elif role == "Sales Rep":
            _SalesRepPanel(self._scroll, self.db_config,
                           self.employee_number).grid(
                row=0, column=0, sticky="nsew")
        else:
            # Fallback — unknown role, show nothing sensitive
            ctk.CTkLabel(self._scroll,
                         text="Access restricted for your role.",
                         font=("Segoe UI", 14), text_color="#e74c3c"
                         ).grid(row=0, column=0, pady=40)

    def _build_tab_bar(self):
        tab_row = ctk.CTkFrame(self, fg_color="transparent")
        tab_row.grid(row=2, column=0, sticky="ew", padx=30, pady=(16, 0))

        self._tab_btns = {}
        tabs = [
            ("worker_files", "Worker Files"),
            ("audit",        "Payroll Audit & Processing"),
            ("timecard",     "Timecard Entry"),
        ]
        for key, label in tabs:
            btn = ctk.CTkButton(
                tab_row, text=label, height=34, corner_radius=8,
                fg_color="#e8eef5", hover_color="#d7e3f0",
                text_color="#2c3e50", font=("Segoe UI", 12),
                command=lambda k=key: self._switch(k))
            btn.pack(side="left", padx=(0, 8))
            self._tab_btns[key] = btn

        self._switch("worker_files")

    def _switch(self, key):
        for k, b in self._tab_btns.items():
            b.configure(
                fg_color="#3498db" if k == key else "#e8eef5",
                text_color="#ffffff" if k == key else "#2c3e50")
        for w in self._scroll.winfo_children():
            w.destroy()

        panel = {
            "worker_files": lambda: _WorkerFilesPanel(
                self._scroll, self.db_config),
            "audit":        lambda: _AuditPanel(
                self._scroll, self.db_config),
            "timecard":     lambda: _TimecardPanel(
                self._scroll, self.db_config, None),
        }[key]()
        panel.grid(row=0, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

    def _refresh_summary(self):
        """Pull live counts for the 4 summary cards."""
        try:
            conn  = _get_conn(self.db_config)
            cur   = conn.cursor()
            today = date.today()
            week  = today - timedelta(days=today.weekday())

            cur.execute("SELECT COUNT(*) FROM employees WHERE is_active=TRUE")
            emp_count = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*) FROM employees e
                LEFT JOIN timecards t
                    ON t.employee_number=e.employee_number AND t.week_date=%s
                WHERE e.is_active=TRUE AND e.position='Hourly'
                  AND t.timecard_id IS NULL
            """, (week,))
            missing = cur.fetchone()[0]

            cur.execute("""
                SELECT COALESCE(SUM(t.hours_worked*COALESCE(e.hourly_wage,0)),0)
                FROM timecards t
                JOIN employees e ON e.employee_number=t.employee_number
                WHERE e.position='Hourly' AND t.week_date=%s
            """, (week,))
            gross = cur.fetchone()[0] or 0

            cur.execute("""
                SELECT COALESCE(AVG(hourly_wage),0) FROM employees
                WHERE  is_active=TRUE AND position='Hourly'
            """)
            avg_wage = cur.fetchone()[0] or 0

            cur.close(); conn.close()

            self._cards["emp"].update_value(str(emp_count))
            self._cards["miss"].update_value(str(missing))
            self._cards["gross"].update_value(f"P{float(gross):,.2f}")
            self._cards["rate"].update_value(f"P{float(avg_wage):,.2f}")

        except Exception:
            pass   # DB not yet connected — cards stay at "..."