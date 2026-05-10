import customtkinter as ctk
from tkinter import ttk
import logging

psycopg2 = None
try:
    import psycopg2

    HAS_DB = True
except ImportError:
    HAS_DB = False

from frontend.modular.metric_card import MetricCard, ProgressMetricCard
from decimal import Decimal, InvalidOperation

# Configure basic logging for debugging dashboard load issues
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DashboardView(ctk.CTkScrollableFrame):
    def __init__(
        self, parent, controller, username="User", role="Staff", db_config=None
    ):
        super().__init__(parent, fg_color="#f8f9fa", corner_radius=0, border_width=0)
        self.controller = controller
        self.db_config = db_config
        self.username = username
        self.role = role

        # Use Decimal for safe arithmetic with DB Decimal types
        try:
            self.sales_goal_target = Decimal(
                str((self.db_config or {}).get("sales_goal_target", 80000))
            )
        except (InvalidOperation, TypeError):
            self.sales_goal_target = Decimal("80000")

        self.is_hourly = self.role == "Hourly"
        self.is_sales_rep = self.role == "Sales Rep"
        self.is_manager = self.role == "Manager"

        self.columnconfigure(0, weight=1)

        # --- 1. WELCOME HEADER ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(25, 0))

        self.welcome_label = ctk.CTkLabel(
            self.header_frame,
            text=f"Welcome back, {self.username} - {self.role}",
            font=("Segoe UI", 28, "bold"),
            text_color="#2c3e50",
        )
        self.welcome_label.pack(side="left")

        # --- RIGHT-ALIGNED STATUS CONTAINER ---
        self.status_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.status_container.pack(side="right", pady=(10, 0))

        # Refresh Button
        self.refresh_btn = ctk.CTkButton(
            self.status_container,
            text="🔄",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#e0e0e0",
            text_color="#7f8c8d",
            command=self._load_dashboard_data,
        )
        self.refresh_btn.pack(side="right", padx=(10, 0))

        self.conn_status = ctk.CTkLabel(
            self.status_container,
            text=" ●  DB: CHECKING...",
            font=("Segoe UI", 12, "bold"),
            text_color="#7f8c8d",
        )
        self.conn_status.pack(side="right")

        # --- 2. NOTICE FRAME ---
        self.notice_frame = ctk.CTkFrame(self, fg_color="transparent", height=0)
        self.notice_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=0)

        # --- 3. METRIC GRID ---
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=(10, 20))
        self.grid_frame.columnconfigure((0, 1, 2, 3), weight=1, pad=20)

        card_titles = {
            "Manager": [
                "Total Revenue",
                "Pending Orders",
                "Active Customers",
                "Critical Stock Alerts",
            ],
            "Sales Rep": [
                "My YTD Sales",
                "Est. Commission (5%)",
                "My Active Customers",
                "Sales Goal Progress",
            ],
            "Hourly": [
                "My Hours (This Week)",
                "Projected Paycheck",
                "Pending Timecards",
                "Announcements",
            ],
        }.get(self.role, ["Metric 1", "Metric 2", "Metric 3", "Metric 4"])

        # Contextual subtitles for each role
        card_subtexts = {
            "Manager": [
                "Period total",
                "Active shipments",
                "Active accounts",
                "Below threshold",
            ],
            "Sales Rep": [
                "Year to date",
                "At 5% rate",
                "Your accounts",
                "Target progress",
            ],
            "Hourly": [
                "This week",
                "Projected pay",
                "Awaiting processing",
                "Current updates",
            ],
        }.get(self.role, ["Metric 1", "Metric 2", "Metric 3", "Metric 4"])

        self.rev_card = MetricCard(
            self.grid_frame,
            card_titles[0],
            "$---",
            card_subtexts[0],
            "💰",
            "#7f8c8d",
        )
        self.rev_card.grid(row=0, column=0, sticky="nsew")

        self.orders_card = MetricCard(
            self.grid_frame,
            card_titles[1],
            "0",
            card_subtexts[1],
            "🛒",
            "#7f8c8d",
        )
        self.orders_card.grid(row=0, column=1, sticky="nsew")

        self.cust_card = MetricCard(
            self.grid_frame, card_titles[2], "0", card_subtexts[2], "👥", "#7f8c8d"
        )
        self.cust_card.grid(row=0, column=2, sticky="nsew")

        # For Sales Rep: use ProgressMetricCard to show goal progress with a tracker
        if self.is_sales_rep:
            self.stock_card = ProgressMetricCard(
                self.grid_frame,
                card_titles[3],
                "0.0%",
                0,
                "🎯",
                "#3498db",
                goal_text=f"Target: ₱{float(self.sales_goal_target):,.0f}",
            )
        else:
            self.stock_card = MetricCard(
                self.grid_frame,
                card_titles[3],
                "---",
                card_subtexts[3],
                "📦",
                "#7f8c8d",
            )
        self.stock_card.grid(row=0, column=3, sticky="nsew")

        # --- 4. RECENT ACTIVITY TABLE ---
        self.table_frame = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )
        self.table_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=20)

        ctk.CTkLabel(
            self.table_frame,
            text=(
                "All Recent Sales"
                if self.is_manager
                else (
                    "My Recent Invoices"
                    if self.is_sales_rep
                    else "My Recent Timecard Logs"
                )
            ),
            font=("Segoe UI", 16, "bold"),
            text_color="#2c3e50",
        ).pack(anchor="w", padx=20, pady=15)

        # Treeview style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dashboard.Treeview",
            font=("Segoe UI", 11),
            rowheight=34,
            background="#ffffff",
            fieldbackground="#ffffff",
            borderwidth=0,
        )
        style.configure(
            "Dashboard.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            background="#f8f9fa",
            foreground="#2c3e50",
            relief="flat",
        )

        cols = (
            ("Week Ending", "Hours Worked", "Rate", "Projected Pay", "Logged Date")
            if self.is_hourly
            else ("Invoice #", "Customer", "Amount", "Status", "Date")
        )
        self.recent_tree = ttk.Treeview(
            self.table_frame,
            columns=cols,
            show="headings",
            height=8,
            style="Dashboard.Treeview",
        )

        column_widths = (
            {
                "Week Ending": 150,
                "Hours Worked": 120,
                "Rate": 100,
                "Projected Pay": 140,
                "Logged Date": 120,
            }
            if self.is_hourly
            else {
                "Invoice #": 100,
                "Customer": 250,
                "Amount": 120,
                "Status": 100,
                "Date": 120,
            }
        )
        for col in cols:
            self.recent_tree.heading(col, text=col)
            self.recent_tree.column(col, width=column_widths[col], anchor="w")

        self.recent_tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Initial load
        self._load_dashboard_data()

    def _to_decimal(self, value):
        """Safely convert DB numeric/float/None to Decimal for arithmetic."""
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value))
        except Exception:
            logger.debug(
                "_to_decimal failed for value=%r (type=%s)", value, type(value)
            )
            return Decimal("0")

    def _load_dashboard_data(self):
        if not HAS_DB or psycopg2 is None or not self.db_config:
            self._update_ui_on_error("Library Missing")
            return

        # Defensive debug
        try:
            logger.debug(
                "_load_dashboard_data called for user=%s role=%s emp=%s db=%s",
                self.username,
                self.role,
                getattr(self.controller.session, "employee_number", None),
                bool(self.db_config),
            )
        except Exception:
            logger.debug("_load_dashboard_data called (failed to access session)")

        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()

            self.conn_status.configure(text=f" ● CONNECTED", text_color="#2ecc71")

            emp_id = (
                self.controller.session.employee_number
                if hasattr(self.controller, "session")
                else None
            )
            logger.debug("Resolved emp_id=%s (role=%s)", emp_id, self.role)

            self._clear_notice()

            recent_rows = []

            if self.is_manager:
                # Manager queries
                cur.execute(
                    "SELECT COALESCE(SUM(total_amount), 0) FROM invoices WHERE status = 'paid';"
                )
                revenue = cur.fetchone()[0]
                revenue_dec = self._to_decimal(revenue)

                cur.execute("SELECT COUNT(*) FROM invoices WHERE status = 'active';")
                orders = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM customers WHERE is_active = TRUE;")
                customers = cur.fetchone()[0]

                cur.execute(
                    "SELECT COUNT(*) FROM parts WHERE stock_count <= 1 AND on_order = FALSE;"
                )
                critical_stock = cur.fetchone()[0]

                try:
                    self.rev_card.update_value(f"₱{float(revenue_dec):,.2f}")
                except Exception:
                    self.rev_card.update_value("₱0.00")
                self.orders_card.update_value(str(orders))
                self.cust_card.update_value(str(customers))
                self.stock_card.update_value(str(critical_stock))

                if critical_stock > 0:
                    self._show_critical_alert(critical_stock)

                cur.execute("""
                    SELECT i.invoice_id, c.company_name, i.total_amount, i.status, i.date_written
                    FROM invoices i
                    JOIN customers c ON i.customer_number = c.customer_number
                    ORDER BY i.date_written DESC, i.invoice_id DESC
                    LIMIT 10;
                """)
                recent_rows = cur.fetchall()

            elif self.is_sales_rep:
                if not emp_id:
                    raise ValueError(
                        "Missing session employee_number for Sales Rep dashboard scoping."
                    )

                cur.execute(
                    "SELECT COALESCE(SUM(total_amount), 0) FROM invoices WHERE employee_number = %s AND status = 'paid';",
                    (emp_id,),
                )
                my_revenue = cur.fetchone()[0]
                my_revenue = self._to_decimal(my_revenue)
                commission = my_revenue * Decimal("0.05")

                cur.execute(
                    "SELECT COUNT(*) FROM invoices WHERE employee_number = %s AND status = 'active';",
                    (emp_id,),
                )
                my_orders = cur.fetchone()[0]

                cur.execute(
                    "SELECT COUNT(DISTINCT customer_number) FROM invoices WHERE employee_number = %s AND status <> 'void';",
                    (emp_id,),
                )
                my_customers = cur.fetchone()[0]

                try:
                    goal_progress = (
                        (my_revenue / self.sales_goal_target) * Decimal("100")
                        if self.sales_goal_target > 0
                        else Decimal("0")
                    )
                except (InvalidOperation, TypeError) as ex:
                    logger.debug("Goal progress calc failed: %s", ex)
                    goal_progress = Decimal("0")

                try:
                    self.rev_card.update_value(f"₱{float(my_revenue):,.2f}")
                except Exception:
                    self.rev_card.update_value("₱0.00")
                try:
                    self.orders_card.update_value(f"₱{float(commission):,.2f}")
                except Exception:
                    self.orders_card.update_value("₱0.00")
                self.cust_card.update_value(str(my_customers))
                try:
                    gp_display = f"{float(goal_progress):.1f}%"
                    gp_value = float(goal_progress)
                except (TypeError, InvalidOperation):
                    gp_display = "0.0%"
                    gp_value = 0.0
                self.stock_card.update_value(gp_display)
                # Update progress bar on ProgressMetricCard for Sales Rep
                try:
                    getattr(self.stock_card, "update_progress")(gp_value)
                except AttributeError:
                    pass

                cur.execute(
                    """
                    SELECT i.invoice_id, c.company_name, i.total_amount, i.status, i.date_written
                    FROM invoices i
                    JOIN customers c ON i.customer_number = c.customer_number
                    WHERE i.employee_number = %s
                    ORDER BY i.date_written DESC, i.invoice_id DESC
                    LIMIT 10;
                """,
                    (emp_id,),
                )
                recent_rows = cur.fetchall()

            else:
                if not emp_id:
                    raise ValueError(
                        "Missing session employee_number for Hourly dashboard scoping."
                    )

                # --- HOURLY WORKER QUERIES (Pending = not yet paid) ---
                # Hours unpaid (timecards without employee_payments entry)
                cur.execute(
                    """
                    SELECT COALESCE(SUM(t.hours_worked), 0)
                    FROM timecards t
                    WHERE t.employee_number = %s
                      AND NOT EXISTS (SELECT 1 FROM employee_payments ep WHERE ep.timecard_id = t.timecard_id);
                    """,
                    (emp_id,),
                )
                hours_this_week = cur.fetchone()[0]
                hours_this_week_dec = self._to_decimal(hours_this_week)
                logger.debug(
                    "hours_this_week raw=%r type=%s",
                    hours_this_week,
                    type(hours_this_week),
                )

                # Projected pay (hours × wage for unpaid timecards)
                cur.execute(
                    """
                    SELECT COALESCE(SUM(t.hours_worked * e.hourly_wage), 0)
                    FROM timecards t
                    JOIN employees e ON t.employee_number = e.employee_number
                    WHERE t.employee_number = %s
                      AND NOT EXISTS (SELECT 1 FROM employee_payments ep WHERE ep.timecard_id = t.timecard_id);
                    """,
                    (emp_id,),
                )
                projected_pay = cur.fetchone()[0]
                projected_pay_dec = self._to_decimal(projected_pay)
                logger.debug(
                    "projected_pay raw=%r type=%s", projected_pay, type(projected_pay)
                )

                # Pending logs count (timecards without payment)
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM timecards t
                    WHERE t.employee_number = %s
                      AND NOT EXISTS (SELECT 1 FROM employee_payments ep WHERE ep.timecard_id = t.timecard_id);
                    """,
                    (emp_id,),
                )
                pending_logs = cur.fetchone()[0]

                # Recent timecard logs with payment status
                cur.execute(
                    """
                    SELECT t.week_date, t.hours_worked,
                           COALESCE(e.hourly_wage, 0) AS rate,
                           ROUND((t.hours_worked * COALESCE(e.hourly_wage, 0))::numeric, 2) AS pay,
                           CASE WHEN ep.payment_id IS NOT NULL THEN 'Processed' ELSE 'Pending' END AS status
                    FROM timecards t
                    JOIN employees e ON e.employee_number = t.employee_number
                    LEFT JOIN employee_payments ep ON ep.timecard_id = t.timecard_id
                    WHERE t.employee_number = %s
                    ORDER BY t.week_date DESC
                    LIMIT 10;
                    """,
                    (emp_id,),
                )
                recent_rows = cur.fetchall()

                try:
                    self.rev_card.update_value(f"{float(hours_this_week_dec):,.2f} h")
                except Exception:
                    self.rev_card.update_value("0.00 h")
                try:
                    self.orders_card.update_value(f"₱{float(projected_pay_dec):,.2f}")
                except Exception:
                    self.orders_card.update_value("₱0.00")
                self.cust_card.update_value(str(pending_logs))

            # Populate Treeview
            for row in self.recent_tree.get_children():
                self.recent_tree.delete(row)

            if self.is_hourly:
                for row in recent_rows:
                    week_ending, hours_worked, rate, pay, status = row
                    self.recent_tree.insert(
                        "",
                        "end",
                        values=(
                            str(week_ending),
                            f"{hours_worked:,.2f}",
                            f"₱{rate:,.2f}",
                            f"₱{pay:,.2f}",
                            str(status),
                        ),
                    )
            else:
                for row in recent_rows:
                    inv_id, cust_name, amt, status, d_written = row
                    self.recent_tree.insert(
                        "",
                        "end",
                        values=(
                            f"INV-{inv_id}",
                            cust_name,
                            f"₱{amt:,.2f}",
                            str(status).title(),
                            d_written,
                        ),
                    )

            cur.close()
            conn.close()

        except Exception as e:
            logger.exception("[DashboardView] Error loading dashboard data")
            self._update_ui_on_error("Query Error")

    def _clear_notice(self):
        """Removes role-specific notices before re-rendering dashboard data."""
        self.notice_frame.grid_configure(pady=0)
        self.notice_frame.configure(height=0)
        for widget in self.notice_frame.winfo_children():
            widget.destroy()

    def _show_critical_alert(self, count):
        """Displays the FS-Sec6 Critical Alert in the Notice Frame."""
        self.notice_frame.configure(height=50)
        self.notice_frame.grid_configure(pady=(10, 0))

        alert_bg = ctk.CTkFrame(
            self.notice_frame,
            fg_color="#fdeceb",
            border_color="#f5c6cb",
            border_width=1,
            corner_radius=8,
        )
        alert_bg.pack(fill="x", expand=True)

        ctk.CTkLabel(
            alert_bg,
            text=f"⚠️ CRITICAL INVENTORY ALERT: {count} parts have stock levels at or below 1 with no active purchase orders.",
            text_color="#721c24",
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left", padx=15, pady=10)

    def _update_ui_on_error(self, error_msg):
        """Updates UI to reflect that the database is offline."""
        try:
            self.conn_status.configure(
                text=f" ●  DB: {error_msg}", text_color="#e74c3c"
            )
        except Exception:
            pass

        error_val = "N/A"
        self.rev_card.update_value(error_val)
        self.orders_card.update_value(error_val)
        self.cust_card.update_value(error_val)
        self.stock_card.update_value(error_val)
