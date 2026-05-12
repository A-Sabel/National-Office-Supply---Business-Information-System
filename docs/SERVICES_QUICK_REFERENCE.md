# Backend Services Quick Reference Card

## Import Services

```python
# Option 1: Use ServiceLocator (Recommended)
from backend.service_integration import ServiceLocator
services = ServiceLocator(db_config, session_manager)

# Option 2: Use View Adapters
from backend.service_integration import get_view_adapters
adapters = get_view_adapters(db_config, session_manager)

# Option 3: Direct imports
from backend.part_service import PartService
from backend.invoice_service import InvoiceService
from backend.timecard_service import TimecardService
from backend.employee_service import EmployeeService
from backend.supplier_cost_service import SupplierCostService
from backend.report_service import ReportService
from backend.crypto_utils import CryptoUtils
from backend.session_manager import SessionManager
```

## PartService Cheat Sheet

```python
services.parts.get_all()                           # → List[Dict]
services.parts.get_by_id(part_number)             # → Optional[Dict]
services.parts.create(number, desc, price, ...)   # → Optional[int]
services.parts.update(part_number, desc=..., ..)  # → None
services.parts.delete(part_number)                # → None
services.parts.get_low_stock()                    # → List[Dict]
services.parts.update_stock(part_number, 5)       # → Optional[int]
services.parts.get_supplier_cost(number, supp_id) # → Optional[Decimal]
```

## InvoiceService Cheat Sheet

```python
services.invoices.create(customer_id, emp_id)                   # → Optional[int]
services.invoices.add_line_item(invoice_id, part_num, qty)      # → None
services.invoices.get_invoice_total(invoice_id)                 # → Decimal
services.invoices.update_status(invoice_id, 'shipped')          # → None
services.invoices.get_customer_invoices(customer_id)            # → List[Dict]
services.invoices.get_invoice_details(invoice_id)               # → Optional[Dict]
services.invoices.get_invoice_lines(invoice_id)                 # → List[Dict]
```

## TimecardService Cheat Sheet

```python
services.timecards.check_if_week_exists(week_date)              # → bool
services.timecards.create_weekly_timecards(week_date)           # → int
services.timecards.get_missing_timecards(week_date)             # → List[Dict]
services.timecards.mark_complete(timecard_id)                   # → None
services.timecards.update_hours(timecard_id, 40.0)              # → None
services.timecards.get_timecard(timecard_id)                    # → Optional[Dict]
services.timecards.get_timecards_for_week(week_date)            # → List[Dict]
```

## EmployeeService Cheat Sheet

```python
services.employees.get_all()                       # → List[Dict]
services.employees.get_by_id(emp_number)          # → Optional[Dict]
services.employees.get_by_username(username)      # → Optional[Dict]
services.employees.get_hourly_staff()             # → List[Dict]
services.employees.get_active_staff()             # → List[Dict]
```

## ReportService Cheat Sheet

```python
# Use with adapter or directly
report = adapters['reports']

report.filter_data(data, 'status', 'active', 'eq')               # → List[Dict]
report.filter_data(data, 'price', 100, 'gt')                    # Filter > 100
report.sort_data(data, [('date', False), ('amount', True)])     # → List[Dict]
report.limit_rows(data, limit=50, offset=0)                     # → List[Dict]
report.paginate(data, page=2, page_size=50)                     # → Dict
report.export_to_csv(data, 'report.csv')                        # → str
report.export_to_json(data, 'report.json')                      # → str
report.summarize(data, 'category', 'amount', 'sum')             # → List[Dict]
```

## CryptoUtils Cheat Sheet

```python
encrypted_ssn = CryptoUtils.encrypt_ssn("123-45-6789")           # → str
plaintext_ssn = CryptoUtils.decrypt_ssn(encrypted_ssn)           # → str
new_key = CryptoUtils.generate_encryption_key()                  # → str
```

## SessionManager Cheat Sheet

```python
# Initialization
session_mgr = SessionManager(timeout_minutes=30)

# Session control
session_mgr.start_session(emp_num, emp_name, role)              # → AppSession
session_mgr.logout()                                             # → None
session_mgr.touch()  # Refresh inactivity timer                  # → None

# Authentication checks
session_mgr.is_authenticated()                                   # → bool
session_mgr.is_expired()                                         # → bool
status = session_mgr.get_status()  # Session snapshot           # → SessionStatus

# Role-based access control
session_mgr.has_role(['Manager'])                                # → bool
session_mgr.is_manager()                                         # → bool
session_mgr.is_sales_rep()                                       # → bool
session_mgr.is_hourly()                                          # → bool

# Permission checks
session_mgr.can_edit_payroll()                                   # → bool
session_mgr.can_edit_prices()                                    # → bool
session_mgr.can_create_invoices()                                # → bool
session_mgr.can_view_timecards()                                 # → bool

# Time tracking
session_mgr.get_session_age_minutes()                            # → int
session_mgr.get_inactivity_minutes()                             # → int
session_mgr.get_remaining_minutes()                              # → int

# Enforcement
session_mgr.ensure_active(['Manager'])  # Raises PermissionError  # → None
```

## View Adapter Cheat Sheet

### Invoice Adapter

```python
adapters['invoices'].get_invoice_list(status_filter='active')
adapters['invoices'].create_invoice_with_lines(cust_id, emp_id, items)
adapters['invoices'].get_invoice_details(invoice_id)
```

### Payroll Adapter

```python
adapters['payroll'].get_week_timecards(week_date)
adapters['payroll'].auto_generate_weekly_timecards(week_date)
adapters['payroll'].get_missing_timecards_for_week(week_date)
adapters['payroll'].get_hourly_staff_for_payroll()
```

### Inventory Adapter

```python
adapters['inventory'].get_all_parts()
adapters['inventory'].get_low_stock_alert()
adapters['inventory'].adjust_stock(part_number, qty_delta)
```

### Dashboard Adapter

```python
adapters['dashboard'].get_inventory_metrics()  # KPIs
```

### Report Adapter

```python
adapters['reports'].filter_data(data, col, val, op)
adapters['reports'].sort_data(data, [('col', True)])
adapters['reports'].paginate(data, page=1, page_size=50)
adapters['reports'].export_to_csv(data, filename)
adapters['reports'].export_to_json(data, filename)
adapters['reports'].summarize(data, group_by, agg_col, agg_func)
```

## Common Patterns

### Load and Display

```python
try:
    data = services.parts.get_all()
    if data:
        display_in_treeview(data)
    else:
        show_message("No data available")
except Exception as e:
    show_error(f"Failed to load: {e}")
```

### Create with Validation

```python
try:
    # Service validates internally
    id = services.invoices.create(customer_id, employee_id)
    if id:
        show_success(f"Created with ID {id}")
    else:
        show_warning("Creation returned None")
except PermissionError as e:
    show_error("Access Denied: " + str(e))
except ValueError as e:
    show_warning("Validation Error: " + str(e))
```

### Update with Permission Check

```python
try:
    session_manager.ensure_active(['Manager'])  # Raises if denied
    services.parts.update(part_number, price=new_price)
    show_success("Updated")
except PermissionError as e:
    show_error(str(e))
except Exception as e:
    show_error(f"Update failed: {e}")
```

### Export Data

```python
try:
    data = services.parts.get_all()
    report = adapters['reports']

    # Filter first
    data = report.filter_data(data, 'stock_count', 0, 'gt')

    # Export
    csv_file = report.export_to_csv(data, 'inventory.csv')
    show_info(f"Exported to {csv_file}")
except Exception as e:
    show_error(f"Export failed: {e}")
```

## Error Handling

```python
# Service returns None on not found
part = services.parts.get_by_id(invalid_id)
if part is None:
    # Not found or permission denied

# Services raise exceptions for access denied
try:
    services.invoices.update_status(id, 'paid')
except PermissionError as e:
    # Access denied - log and display to user
    show_error(f"Cannot perform action: {e}")

# Services raise ValueError for validation errors
try:
    services.invoices.create(invalid_customer, emp_id)
except ValueError as e:
    # Validation failed
    show_warning(f"Invalid input: {e}")
```

## Testing

```bash
# Run all integration tests
pytest tests/test_services_integration.py -v

# Run specific service tests
pytest tests/test_services_integration.py::TestPartService -v

# Run with detailed output
pytest tests/test_services_integration.py -vv --tb=short

# Run and show print statements
pytest tests/test_services_integration.py -v -s
```

## Constants

```python
# Invoice statuses
INVOICE_STATUSES = ['active', 'shipped', 'paid', 'void']

# Employee positions
POSITIONS = ['Manager', 'Sales Rep', 'Hourly']

# Session timeout (minutes)
DEFAULT_TIMEOUT = 30

# Report filter operators
OPERATORS = ['eq', 'ne', 'gt', 'lt', 'gte', 'lte', 'in', 'contains']

# Aggregation functions
AGG_FUNCTIONS = ['sum', 'avg', 'count', 'min', 'max']
```

## File Structure

```text
src/
├── backend/
│   ├── database.py              # Connection factory
│   ├── part_service.py          # PartService
│   ├── employee_service.py      # EmployeeService
│   ├── invoice_service.py       # InvoiceService
│   ├── timecard_service.py      # TimecardService
│   ├── supplier_cost_service.py # SupplierCostService
│   ├── report_service.py        # ReportService
│   ├── crypto_utils.py          # SSN encryption
│   ├── session_manager.py       # SessionManager
│   └── service_integration.py   # ⭐ Locators and adapters
│
├── frontend/
│   ├── service_integration_examples.py  # ⭐ View examples
│   └── tabs/
│       ├── inventory.py
│       ├── orders_and_invoices.py
│       ├── payroll.py
│       ├── dashboard.py
│       └── reports_tab/
│
└── utils/
    └── session.py               # AppSession base class

tests/
└── test_services_integration.py # ⭐ Integration tests

docs/
├── SERVICE_INTEGRATION_GUIDE.md      # Detailed guide
├── SERVICE_WIRING_COMPLETE.md        # Summary
└── [this file]                        # Quick reference
```

## Need Help?

1. **See examples:** `src/frontend/service_integration_examples.py`
2. **Read guide:** `docs/SERVICE_INTEGRATION_GUIDE.md`
3. **Check tests:** `tests/test_services_integration.py`
4. **Review completion:** `docs/SERVICE_WIRING_COMPLETE.md`

---

**Version:** 1.0 | **Last Updated:** May 12, 2026 | **Status:** Complete ✅
