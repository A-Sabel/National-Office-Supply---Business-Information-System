# Service Integration Guide

## Overview

This guide shows how to wire backend services into existing frontend views to replace raw SQL queries with type-safe, reusable service methods.

## Quick Start

### 1. Using Service Locator (Recommended)

For most views, import and use the `ServiceLocator`:

```python
from backend.service_integration import ServiceLocator

class MyView(ctk.CTkFrame):
    def __init__(self, parent, db_config, session_manager=None):
        super().__init__(parent)
        self.db_config = db_config

        # Create service locator
        self.services = ServiceLocator(db_config, session_manager)

    def load_data(self):
        # Use services directly
        parts = self.services.parts.get_all()
        low_stock = self.services.parts.get_low_stock()
        invoices = self.services.invoices.get_customer_invoices(customer_id)
```

### 2. Using View-Specific Adapters

For more complex views, use specialized adapters:

```python
from backend.service_integration import get_view_adapters

class OrdersAndInvoicesView(ctk.CTkFrame):
    def __init__(self, parent, db_config, session_manager=None):
        super().__init__(parent)

        adapters = get_view_adapters(db_config, session_manager)
        self.invoice_adapter = adapters['invoices']
        self.report_adapter = adapters['reports']

    def create_order(self, customer_id, line_items):
        invoice = self.invoice_adapter.create_invoice_with_lines(
            customer_id, employee_id, line_items
        )
        return invoice

    def export_data(self, data):
        return self.report_adapter.export_to_csv(data)
```

## Service Reference

### PartService

```python
service = services.parts

# CRUD Operations
parts = service.get_all()                    # → List[Dict]
part = service.get_by_id(part_number)       # → Optional[Dict]
new_id = service.create(...)                # → Optional[int]
service.update(part_number, ...)            # → None
service.delete(part_number)                 # → None

# Stock Management
low_stock = service.get_low_stock()         # → List[Dict]
new_stock = service.update_stock(part_number, quantity_delta)  # → Optional[int]
cost = service.get_supplier_cost(part_number, supplier_id)     # → Optional[Decimal]
```

### EmployeeService

```python
service = services.employees

emp = service.get_by_id(emp_number)        # → Optional[Dict]
all_emps = service.get_all()               # → List[Dict]
hourly = service.get_hourly_staff()        # → List[Dict]
active = service.get_active_staff()        # → List[Dict]
emp = service.get_by_username(username)    # → Optional[Dict]
```

### InvoiceService

```python
service = services.invoices

# Create invoices
invoice_id = service.create(customer_number, employee_number)  # → Optional[int]
service.add_line_item(invoice_id, part_number, quantity)      # → None
total = service.get_invoice_total(invoice_id)                  # → Decimal
service.update_status(invoice_id, new_status)                  # → None

# Query invoices
invoices = service.get_customer_invoices(customer_number)      # → List[Dict]
details = service.get_invoice_details(invoice_id)             # → Optional[Dict]
lines = service.get_invoice_lines(invoice_id)                 # → List[Dict]
```

### TimecardService

```python
service = services.timecards

exists = service.check_if_week_exists(week_date)              # → bool
count = service.create_weekly_timecards(week_date)            # → int
missing = service.get_missing_timecards(week_date)            # → List[Dict]
service.mark_complete(timecard_id)                            # → None
service.update_hours(timecard_id, hours_worked)              # → None
timecards = service.get_timecards_for_week(week_date)        # → List[Dict]
timecard = service.get_timecard(timecard_id)                 # → Optional[Dict]
```

### SupplierCostService

```python
service = services.supplier_costs

best = service.get_lowest_cost_supplier(part_number)          # → Optional[Dict]
all_costs = service.get_all_costs_for_part(part_number)      # → List[Dict]
suppliers = service.get_suppliers_by_part(part_number)        # → List[Dict]
parts = service.get_parts_by_supplier(supplier_id)            # → List[Dict]
recommendations = service.get_best_price_procurement()        # → List[Dict]
summary = service.get_supplier_spending_summary()             # → List[Dict]
```

### ReportService (Static Methods)

```python
# Use with adapter pattern
report = adapters['reports']

filtered = report.filter_data(data, 'status', 'active', 'eq')
sorted_data = report.sort_data(data, [('date', False), ('amount', True)])
report.export_to_csv(data, 'report.csv')
report.export_to_json(data, 'report.json')
paginated = report.paginate(data, page=2, page_size=50)
summary = report.summarize(data, 'category', 'amount', 'sum')
```

## Integration Examples

### Orders & Invoices View

**Before (raw SQL):**

```python
def fetch_invoices(self):
    conn = psycopg2.connect(**self.db_config)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM invoices WHERE status='active'...")
    rows = [dict(r) for r in cur.fetchall()]
    return rows
```

**After (using services):**

```python
def fetch_invoices(self):
    # All invoices (service doesn't filter by default, but you can)
    all_invoices = []

    # Get from service
    from backend.invoice_service import InvoiceService
    service = InvoiceService(self.db_config)

    # Implementation: service doesn't have multi-status fetch yet
    # But each customer's invoices can be fetched and filtered
    return all_invoices
```

### Payroll View

**Integration:**

```python
class PayrollView(ctk.CTkFrame):
    def __init__(self, parent, db_config):
        super().__init__(parent)
        adapters = get_view_adapters(db_config)
        self.payroll = adapters['payroll']

    def load_week(self, week_date):
        # Auto-generate timecards if needed
        self.payroll.auto_generate_weekly_timecards(week_date)

        # Load all timecards
        timecards = self.payroll.get_week_timecards(week_date)

        # Find missing ones
        missing = self.payroll.get_missing_timecards_for_week(week_date)

        return timecards, missing
```

### Inventory View

**Integration:**

```python
class InventoryView(ctk.CTkFrame):
    def __init__(self, parent, db_config):
        super().__init__(parent)
        adapters = get_view_adapters(db_config)
        self.inventory = adapters['inventory']

    def refresh_catalog(self):
        parts = self.inventory.get_all_parts()
        low_stock = self.inventory.get_low_stock_alert()
        return parts, low_stock

    def adjust_quantity(self, part_number, delta):
        new_stock = self.inventory.adjust_stock(part_number, delta)
        return new_stock
```

### Dashboard View

**Integration:**

```python
class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, db_config):
        super().__init__(parent)
        adapters = get_view_adapters(db_config)
        self.dashboard = adapters['dashboard']

    def load_metrics(self):
        metrics = self.dashboard.get_inventory_metrics()

        # Display KPIs
        self.total_parts_label.configure(text=metrics['total_parts'])
        self.total_value_label.configure(text=f"₱{metrics['total_value']:,.2f}")
        self.low_stock_label.configure(text=metrics['low_stock_count'])
        self.out_of_stock_label.configure(text=metrics['out_of_stock_count'])
```

### Reports View

**Integration:**

```python
class ReportsView(ctk.CTkFrame):
    def __init__(self, parent, db_config):
        super().__init__(parent)
        adapters = get_view_adapters(db_config)
        self.reports = adapters['reports']

    def generate_report(self, data, filters, sort_spec):
        # Apply filters
        for column, value in filters.items():
            data = self.reports.filter_data(data, column, value)

        # Apply sorting
        data = self.reports.sort_data(data, sort_spec)

        # Paginate
        page = self.reports.paginate(data, page=1, page_size=50)

        # Export options
        self.reports.export_to_csv(data, 'report.csv')
        self.reports.export_to_json(data, 'report.json')
```

## Session Management Integration

For views that need authentication/authorization:

```python
class SecureView(ctk.CTkFrame):
    def __init__(self, parent, db_config, session_manager):
        super().__init__(parent)
        self.services = ServiceLocator(db_config, session_manager)
        self.session = session_manager

    def perform_action(self):
        try:
            # SessionManager is passed to services automatically
            # Services use session_manager.ensure_active() internally
            self.services.parts.create(...)  # Checks permission
        except PermissionError as e:
            messagebox.showerror("Access Denied", str(e))
```

## Testing Services

See `tests/test_services_integration.py` for comprehensive integration tests:

```bash
# Run all integration tests
python -m pytest tests/test_services_integration.py -v

# Run specific service tests
python -m pytest tests/test_services_integration.py::TestPartService -v

# Run with database
python -m pytest tests/test_services_integration.py -v --tb=short
```

## Migration Checklist

- [ ] Inventory view uses PartService
- [ ] Orders/Invoices view uses InvoiceService
- [ ] Payroll view uses TimecardService
- [ ] Dashboard uses service metrics
- [ ] Reports use ReportService adapters
- [ ] All views pass session_manager to services
- [ ] Error handling uses service exceptions
- [ ] Integration tests passing
- [ ] No raw SQL in views (except special cases)

## Troubleshooting

### ImportError: No module named 'backend'

Solution: Ensure `src/` is in Python path:

```python
import sys
sys.path.insert(0, 'src')
```

### Service returns None unexpectedly

Solution: Check session permissions:

```python
if service.get_by_id(id) is None:
    # Could be: invalid ID, or permission denied
    # Check logs for "Access Denied" errors
```

### Database connection refused

Solution: Ensure db_config is correct:

```python
db_config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'nos_db',
    'user': 'postgres',
    'password': 'your_password'
}
```

## Next Steps

1. Update each view to use ServiceLocator or view adapters
2. Remove OrdersDB, PayrollDB, etc. classes (keep as reference)
3. Run integration tests after each update
4. Verify UI still displays data correctly
5. Check permission enforcement with different user roles
