import customtkinter as ctk
import logging
from datetime import datetime, timedelta
import json

psycopg2 = None
try:
    import psycopg2

    HAS_DB = True
except Exception:
    HAS_DB = False

logger = logging.getLogger(__name__)


class AlertDropdown(ctk.CTkFrame):
    """Alerts dropdown. When a DB is available it reads from the `logs` audit
    table and shows entries newer than the user's last-read timestamp (stored
    in `log_reads`). Managers see all new audit entries; non-managers see
    their own recent actions. Falls back to provided `alerts` mock list when
    no DB is configured.
    """

    def __init__(self, parent, controller=None, alerts=None):
        super().__init__(
            parent,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
            width=360,
        )

        self.controller = controller
        self.alerts = []

        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=15, pady=(12, 8))

        ctk.CTkLabel(
            self.header,
            text="Notifications",
            font=("Segoe UI", 14, "bold"),
            text_color="#2c3e50",
        ).pack(side="left")

        # Alert List Container
        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", height=260
        )
        self.list_frame.pack(fill="x", padx=8, pady=(0, 6))

        # Load alerts (DB-backed if possible)
        try:
            self._load_alerts_from_db()
        except Exception as e:
            logger.debug("Failed to load DB alerts: %s", e)
            # Fallback to provided mock alerts
            self.alerts = alerts or []

        # Manager filter control (toggle severity) - only visible to managers
        session = getattr(self.controller, "session", None)
        role = getattr(session, "role", "") if session else ""
        self._current_filter = "All"
        if role == "Manager":
            try:
                self._filter_box = ctk.CTkComboBox(
                    self.header,
                    values=["All", "Critical/Unauthorized", "Payments"],
                    command=self._on_filter_change,
                    width=180,
                )
                self._filter_box.set("All")
                self._filter_box.pack(side="right", padx=(6, 8))
            except Exception:
                # CTkComboBox may not exist in older CTK versions; ignore silently
                self._filter_box = None

        # Display count
        self._count_label = ctk.CTkLabel(
            self.header,
            text=f"{len(self.alerts)} New",
            font=("Segoe UI", 11),
            text_color="#3498db",
        )
        self._count_label.pack(side="right")

        # Render alerts using filter-aware renderer
        self._render_alerts()

        # Footer: mark all as read (updates `log_reads` for the current user)
        self._mark_btn = ctk.CTkButton(
            self,
            text="Mark all as read",
            font=("Segoe UI", 11),
            fg_color="transparent",
            text_color="#7f8c8d",
            hover_color="#f0f0f0",
            height=34,
            command=self._mark_all_read,
        )
        self._mark_btn.pack(fill="x", pady=10, padx=10)

    def _ensure_log_reads_table(self, cur):
        cur.execute("""
            CREATE TABLE IF NOT EXISTS log_reads (
                reader_id INTEGER PRIMARY KEY,
                last_read TIMESTAMP NOT NULL
            );
            """)

    def _load_alerts_from_db(self):
        # Require a controller with session and db_config
        if not self.controller or not hasattr(self.controller, "db_config"):
            raise RuntimeError("No DB configuration available")

        if not HAS_DB:
            raise RuntimeError("psycopg2 not available")

        session = getattr(self.controller, "session", None)
        reader_id = getattr(session, "employee_number", None) if session else None
        role = getattr(session, "role", "") if session else ""

        # Narrow type for static checkers that psycopg2 is available here
        assert psycopg2 is not None, "psycopg2 unexpectedly None"
        conn = psycopg2.connect(**self.controller.db_config)
        cur = conn.cursor()

        # Ensure helper table exists
        self._ensure_log_reads_table(cur)

        # Get last_read timestamp for this reader (managers have their own marker)
        last_read = None
        if reader_id is not None:
            cur.execute(
                "SELECT last_read FROM log_reads WHERE reader_id = %s", (reader_id,)
            )
            row = cur.fetchone()
            last_read = row[0] if row else None

        # Build query: managers see all logs; others see their own actor_id logs
        if role == "Manager":
            if last_read:
                cur.execute(
                    """
                    SELECT log_id, actor_id, action_type, target_table, target_id, timestamp, details
                    FROM logs
                    WHERE timestamp > %s
                    ORDER BY timestamp DESC
                    LIMIT 50;
                    """,
                    (last_read,),
                )
            else:
                cur.execute("""
                    SELECT log_id, actor_id, action_type, target_table, target_id, timestamp, details
                    FROM logs
                    ORDER BY timestamp DESC
                    LIMIT 50;
                    """)
        else:
            # Non-manager: only show actions performed by this user
            if reader_id is None:
                self.alerts = []
                cur.close()
                conn.close()
                return
            if last_read:
                cur.execute(
                    """
                    SELECT log_id, actor_id, action_type, target_table, target_id, timestamp, details
                    FROM logs
                    WHERE actor_id = %s AND timestamp > %s
                    ORDER BY timestamp DESC
                    LIMIT 50;
                    """,
                    (reader_id, last_read),
                )
            else:
                cur.execute(
                    """
                    SELECT log_id, actor_id, action_type, target_table, target_id, timestamp, details
                    FROM logs
                    WHERE actor_id = %s
                    ORDER BY timestamp DESC
                    LIMIT 50;
                    """,
                    (reader_id,),
                )

        rows = cur.fetchall()
        # Resolve actor names in bulk for friendlier messages
        actor_names: dict[int, str] = {}
        actor_ids = sorted({r[1] for r in rows if r[1] is not None})
        if actor_ids:
            try:
                cur.execute(
                    "SELECT employee_number, employee_name FROM employees WHERE employee_number = ANY(%s)",
                    (actor_ids,),
                )
                for num, name in cur.fetchall():
                    actor_names[num] = name
            except Exception:
                logger.debug("Failed to resolve actor names for alerts")

        self.alerts = []
        for r in rows:
            log_id, actor_id, action_type, target_table, target_id, ts, details = r

            # Try to parse details as JSON (audit records use JSON when possible)
            parsed = None
            details_text = ""
            if details:
                try:
                    parsed = json.loads(details)
                except Exception:
                    # attempt a forgiving replacement of single quotes
                    try:
                        parsed = json.loads(str(details).replace("'", '"'))
                    except Exception:
                        parsed = None

            if isinstance(parsed, dict):
                # Pretty-format known actions
                atype = (action_type or "").lower()
                tt = (target_table or "").lower()
                if "price" in atype and tt.startswith("part"):
                    old_p = parsed.get("old_price") or parsed.get("old")
                    new_p = parsed.get("new_price") or parsed.get("new")
                    try:
                        if old_p is not None and new_p is not None:
                            details_text = f"Price changed from ₱{float(old_p):,.2f} to ₱{float(new_p):,.2f}"
                        else:
                            raise ValueError("price missing")
                    except Exception:
                        details_text = ", ".join(f"{k}: {v}" for k, v in parsed.items())
                else:
                    details_text = ", ".join(f"{k}: {v}" for k, v in parsed.items())
            else:
                details_text = str(details) if details else ""

            actor_name = actor_names.get(actor_id) or (
                f"User #{actor_id}" if actor_id else "System"
            )

            # Build a friendly message with additional mappings
            lower_atype = (action_type or "").lower()
            lower_tt = (target_table or "").lower()
            details_lower = (details_text or "").lower()

            # Precompute stock-related values for friendly messages
            remaining_raw = None
            remaining_qty = None
            is_low_stock = False
            if isinstance(parsed, dict):
                for k in ("remaining", "remaining_stock", "stock_count"):
                    if k in parsed:
                        remaining_raw = parsed.get(k)
                        break
            try:
                if remaining_raw is not None:
                    remaining_qty = int(remaining_raw)
            except Exception:
                remaining_qty = None

            if remaining_qty is not None:
                is_low_stock = remaining_qty <= 5
            elif "low stock" in details_lower or (
                "low" in details_lower and lower_tt.startswith("part")
            ):
                is_low_stock = True

            # Unauthorized / security-related events
            if (
                "unauth" in lower_atype
                or "unauthor" in lower_atype
                or "unauthorized" in lower_atype
            ):
                msg = (
                    f"Unauthorized access detected: {actor_name} — {details_text}"
                    if details_text
                    else f"Unauthorized action recorded by {actor_name}."
                )
                severity = "critical"

            # Part discontinued
            elif (
                "discontinue" in lower_atype
                or "discontinue" in details_lower
                or "discontinued" in details_lower
            ):
                part_label = (
                    parsed.get("part_name") if isinstance(parsed, dict) else None
                )
                name = part_label or f"Part #{target_id}"
                msg = f"Part discontinued: {name} — contact purchasing."
                severity = "critical"

            # Low-stock alerts (when parsed remaining is small or message contains 'low')
            elif is_low_stock:
                remaining = remaining_qty
                rem_text = f" ({remaining} left)" if remaining is not None else ""
                part_label = (
                    parsed.get("part_name") if isinstance(parsed, dict) else None
                )
                name = part_label or f"Part #{target_id}"
                msg = f"Low stock: {name} — reorder soon{rem_text}"
                severity = "warning"

            # Payment failures
            elif (
                "fail" in lower_atype
                or "failed" in details_lower
                or "failure" in details_lower
            ) and (
                "payment" in lower_atype
                or "invoice" in lower_tt
                or "payment" in details_lower
            ):
                msg = f"Payment failed for Invoice #{target_id} — {details_text or 'see details'}"
                severity = "critical"

            # Inventory restock events (friendly)
            elif (
                "restock" in lower_atype
                or ("restock" in (details_text or "").lower())
                or ("stock" in lower_atype and lower_tt.startswith("part"))
            ):
                qty = None
                if isinstance(parsed, dict):
                    qty = (
                        parsed.get("quantity")
                        or parsed.get("qty")
                        or parsed.get("amount")
                    )
                qty_text = f" Qty: {qty}" if qty is not None else ""
                part_label = (
                    parsed.get("part_name") if isinstance(parsed, dict) else None
                )
                name = part_label or f"{target_table}#{target_id}"
                msg = f"{actor_name} restocked {name}.{qty_text} {details_text}".strip()
                severity = "info"

            # Price updates (parts)
            elif "price" in lower_atype and lower_tt.startswith("part"):
                msg = (
                    f"{actor_name} updated price for part #{target_id}: {details_text}"
                )
                severity = "info"

            # Payments / payroll
            elif lower_atype.startswith("payment") or "pay" in lower_atype:
                msg = f"{actor_name}: {action_type.replace('_', ' ').title()} — {details_text}"
                severity = "info"

            # Generic fallback
            else:
                short_action = (action_type or "").replace("_", " ").title()
                msg = f"{actor_name}: {short_action} on {target_table}#{target_id}. {details_text}"
                severity = (
                    "critical"
                    if (action_type or "").lower().startswith("critical")
                    or (action_type or "").lower().startswith("unauth")
                    else "info"
                )

            self.alerts.append(
                {
                    "id": log_id,
                    "actor_id": actor_id,
                    "type": severity,
                    "msg": msg,
                    "timestamp": ts,
                }
            )

        # Additional employee-specific alerts: paychecks (for non-managers) and
        # timecard reminders (Hourly employees only)
        if role != "Manager" and reader_id is not None:
            # Recent payments for this employee
            try:
                if last_read:
                    cur.execute(
                        """
                        SELECT payment_id, employee_number, amount, payment_date
                        FROM employee_payments
                        WHERE employee_number = %s AND payment_date > %s
                        ORDER BY payment_date DESC
                        LIMIT 10;
                        """,
                        (reader_id, last_read),
                    )
                else:
                    cur.execute(
                        """
                        SELECT payment_id, employee_number, amount, payment_date
                        FROM employee_payments
                        WHERE employee_number = %s AND payment_date >= NOW() - INTERVAL '7 days'
                        ORDER BY payment_date DESC
                        LIMIT 10;
                        """,
                        (reader_id,),
                    )
                pay_rows = cur.fetchall()
                for pr in pay_rows:
                    pid, emp, amount, pdate = pr
                    msg = f"Paycheck received: ₱{float(amount):,.2f}"
                    self.alerts.insert(
                        0,
                        {
                            "id": f"pay-{pid}",
                            "actor_id": emp,
                            "type": "info",
                            "msg": msg,
                            "timestamp": pdate,
                        },
                    )
            except Exception:
                logger.debug(
                    "Failed to query employee_payments for reader=%s", reader_id
                )

            # Saturday timecard reminder: only for Hourly employees
            try:
                if role == "Hourly":
                    today = datetime.now().date()
                    if today.weekday() == 5:  # Saturday
                        seven_days_ago = today - timedelta(days=6)
                        cur.execute(
                            """
                            SELECT 1 FROM timecards WHERE employee_number = %s AND week_date >= %s LIMIT 1;
                            """,
                            (reader_id, seven_days_ago),
                        )
                        has_recent = cur.fetchone() is not None
                        if not has_recent:
                            self.alerts.insert(
                                0,
                                {
                                    "id": f"reminder-{reader_id}-{today}",
                                    "actor_id": reader_id,
                                    "type": "warning",
                                    "msg": "Reminder: please submit your timecard today (Saturday).",
                                    "timestamp": datetime.now(),
                                },
                            )
            except Exception:
                logger.debug("Failed to evaluate timecard reminder for %s", reader_id)

        cur.close()
        conn.close()

    def _add_item(self, alert_data):
        """Adds an individual alert row"""
        item = ctk.CTkFrame(self.list_frame, fg_color="#f8f9fa", corner_radius=8)
        item.pack(fill="x", pady=6, padx=6)

        # Indicator dot based on urgency
        color = "#e74c3c" if alert_data.get("type") == "critical" else "#f39c12"

        dot = ctk.CTkLabel(item, text="•", text_color=color, font=("Segoe UI", 20))
        dot.pack(side="left", padx=(8, 8))

        text = alert_data.get("msg", "(no details)")
        ts = alert_data.get("timestamp")
        ts_display = f" — {ts:%Y-%m-%d %H:%M}" if isinstance(ts, datetime) else ""

        msg = ctk.CTkLabel(
            item,
            text=text + ts_display,
            font=("Segoe UI", 11),
            text_color="#2c3e50",
            wraplength=260,
            justify="left",
        )
        msg.pack(side="left", pady=8, padx=6)

    def _on_filter_change(self, value):
        self._current_filter = value
        self._render_alerts()

    def _render_alerts(self):
        # Rebuild list_frame children based on current filter
        for w in list(self.list_frame.winfo_children()):
            w.destroy()

        def keep(a):
            if self._current_filter == "All":
                return True
            if self._current_filter == "Critical/Unauthorized":
                return (
                    a.get("type") == "critical" or "unauth" in a.get("msg", "").lower()
                )
            if self._current_filter == "Payments":
                return (
                    "paycheck" in a.get("msg", "").lower()
                    or "payment" in a.get("msg", "").lower()
                )
            return True

        kept = [a for a in self.alerts if keep(a)]
        if not kept:
            ctk.CTkLabel(
                self.list_frame,
                text="No alerts matching filter",
                font=("Segoe UI", 12, "italic"),
                text_color="#7f8c8d",
            ).pack(pady=20)
        else:
            for alert in kept:
                self._add_item(alert)

        self._count_label.configure(text=f"{len(kept)} New")

    def _mark_all_read(self):
        # Record now() into log_reads for current user
        if not self.controller or not hasattr(self.controller, "db_config"):
            # nothing to persist, just clear UI
            self._clear_items()
            return

        session = getattr(self.controller, "session", None)
        reader_id = getattr(session, "employee_number", None) if session else None
        if reader_id is None:
            self._clear_items()
            return

        if not HAS_DB:
            self._clear_items()
            return
        # Narrow type for static checkers that psycopg2 is available here
        assert psycopg2 is not None, "psycopg2 unexpectedly None"
        conn = psycopg2.connect(**self.controller.db_config)
        cur = conn.cursor()
        self._ensure_log_reads_table(cur)
        # Upsert last_read
        cur.execute(
            """
            INSERT INTO log_reads (reader_id, last_read) VALUES (%s, NOW())
            ON CONFLICT (reader_id) DO UPDATE SET last_read = EXCLUDED.last_read;
            """,
            (reader_id,),
        )
        conn.commit()
        cur.close()
        conn.close()

        self._clear_items()

    def _clear_items(self):
        # Remove existing children and show "No new alerts"
        for w in list(self.list_frame.winfo_children()):
            w.destroy()
        ctk.CTkLabel(
            self.list_frame,
            text="No new alerts",
            font=("Segoe UI", 12, "italic"),
            text_color="#7f8c8d",
        ).pack(pady=20)
        self._count_label.configure(text="0 New")
