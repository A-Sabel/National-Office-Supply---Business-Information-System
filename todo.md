# National Office Supply BIS - Progress Tracker

Use this file as your live implementation checklist.

## Overall Progress

- [ ] Phase 1: Foundation and Data Layer complete
- [ ] Phase 2: Core Workflows and UI Integration complete
- [ ] Phase 3: Validation, Hardening, and Delivery complete

Completed Requirements: `12 / 17`  
Last Updated: `2026-05-10`

Current Code Snapshot:

- `login.py` now validates credentials against PostgreSQL, populates the active session, and supports password visibility plus Enter-to-login.
- `navigation_bar.py` hides tabs based on the active role.
- `dashboard.py` is role-aware for Manager, Sales Rep, and Hourly users, with Decimal-safe KPI calculations and a compact Sales Rep goal progress card.
- `orders_and_invoices.py` now provides an order/invoice workflow with overselling guards and cancellation handling.
- `payroll.py` is role-based and connected to the database for Manager, Sales Rep, and Hourly views.
- `CustomersView` already supports live balance display, search/filtering, payments, and customer edits.
- `ReportsHubView` routes to live report tabs; implemented reports include Inventory Report, Weekly Sales Report, and Stock Ordering Report.
- PostgreSQL schema migration has already been executed; the database tables are created.
- Placeholder reports still pending: Customer List & Balances, Customer Payment History.
- Remaining gaps are mostly service-layer consolidation, session timeout/session manager work, audit logging, and a few report/workflow finish items.

QD Section Prep:

- [x] Create standalone `queries.sql` with QD-Sec1 to QD-Sec15 using the live schema names
- [x] Add `backend/query_manager.py` to run QD queries from Python
- [ ] Wire QD reads into the existing Reports, Inventory, Payroll, and Orders UI paths
- [ ] Keep QD update actions documented separately from read-only report queries

---

## 3-Phase Breakdown

### Phase 1: Foundation and Data Layer (Weeks 1–2)

**Goal:** Establish all database tables, core services, RBAC structure, and prepare UI for integration.  
**Status:** Foundation for all downstream work; blocks Phase 2.

#### 1A. Database Schema Creation (Week 1, Days 1–2) — **CRITICAL PATH**

Tasks mapped to: Req 1, 2, 3, 10, 14, 16, 17

- [x] Execute SQL migration: Create `Customers` table (`customer_id`, `customer_number`, `company_name`, `address`, `contact`, `balance`, `is_active`)
- [x] Execute SQL migration: Create `Parts` table (`part_id`, `part_number`, `selling_price`, `description`, `stock_count`, `on_order`, `trigger_amount`, `restock_value`)
- [x] Execute SQL migration: Create `Employees` table (`employee_id`, `employee_number`, `name`, `ssn_encrypted`, `position`, `hourly_wage`, `is_active`, `address`)
- [x] Execute SQL migration: Create `Part_Suppliers` junction table (`part_id`, `supplier_id`, `cost`, `UNIQUE(part_id, supplier_id)`)
- [x] Execute SQL migration: Create `Suppliers` table (`supplier_id`, `supplier_name`, `address`, `contact`)
- [x] Execute SQL migration: Create `Invoices` table (`invoice_id`, `customer_id`, `rep_id`, `invoice_date`, `total_amount`, `status`, `shipped_date`, `is_paid`)
- [x] Execute SQL migration: Create `Invoice_Lines` table (`line_id`, `invoice_id`, `part_id`, `quantity_ordered`, FOREIGN KEY constraints)
- [x] Execute SQL migration: Create `Timecards` table (`timecard_id`, `employee_id`, `week_date`, `hours_worked`, `is_complete`)
- [x] Execute SQL migration: Create `Payments` table (`payment_id`, `customer_id`, `payment_date`, `amount`, `payment_method`)
- [x] Execute SQL migration: Create `Logs` table (`log_id`, `actor_id`, `action_type`, `target_table`, `target_id`, `timestamp`, `details`)
- [x] Add constraints: `NOT NULL`, `CHECK (quantity >= 0)`, `CHECK (price >= 0)`, currency fields as `NUMERIC(10,2)`
- [x] Add indices: `Invoices(customer_id)`, `Invoices(rep_id)`, `Parts(stock_count)`, `Timecards(employee_id, week_date)`
- [x] Seed test data: check Document in gdocs
- [x] **Deliverable:** Full schema with constraints, indices, and test data; database ready for queries

#### 1B. Backend Service Layer (Week 1, Days 3–5) — **PRIORITY: HIGH**

Tasks mapped to: All technical implementation items 1–15

- [x] Update `backend/database.py`: Centralized DB connection management (psycopg2 pool or single connection wrapper)
- [x] Implement `CustomerService`: `get_all()`, `get_by_id()`, `create()`, `update()`, `update_balance()`, `delete()` (soft delete with `is_active = FALSE`)
- [ ] Implement `PartService`: `get_all()`, `get_by_id()`, `create()`, `update()`, `get_low_stock()`, `update_stock()`, `get_supplier_cost()`
- [ ] Implement `EmployeeService`: `get_all()`, `get_by_id()`, `get_hourly_staff()`, `get_active_staff()`
- [ ] Implement `InvoiceService`: `create()`, `add_line_item()`, `get_invoice_total()`, `update_status()`, `get_customer_invoices()`
- [ ] Implement `TimecardService`: `create_weekly_timecards()`, `get_missing_timecards()`, `mark_complete()`, `check_if_week_exists()`
- [x] Implement `PaymentService`: `record_payment()`, `get_customer_payments()`, `mark_invoice_paid()`, `update_balance()`
- [ ] Implement `ReportService`: Base class for report queries with reusable filter/sort/export logic
- [ ] Implement `SupplierCostService`: `get_lowest_cost_supplier()`, `get_all_costs_for_part()` (maps to Req 14)
- [ ] **Deliverable:** Service layer with tested basic CRUD and query operations; all tab views can delegate to services

#### 1C. RBAC & Security Foundations (Week 1, Days 4–5 + Week 2, Day 1) — **PRIORITY: HIGH**

Tasks mapped to: FS-Sec1, FS-Sec2, FS-Sec3, Req 16

- [x] Implement login validation: Hash password check against `Employees(position, employee_number)`
- [x] Extend `__main__.py` session state: Track `current_user`, `user_role` (Manager/Rep/Hourly), `session_start_time`
- [x] Create RBAC guard module: `@require_role('Manager')`, `@require_role('Rep')`, etc.
- [x] Update `navigation_bar.py`: Conditionally show/hide tabs based on `current_user.position` (Payroll/Timecards hidden for Reps)
- [ ] Implement `SessionManager`: Session validation, timeout, role-based view access checks
- [ ] Add SSN encryption utility: `encrypt_ssn()`, `decrypt_ssn()` (using `cryptography` library or simple AES)
- [x] Validate automated ID strategy: Ensure all primary keys use `SERIAL`/`BIGSERIAL` (FS-Sec2)
- [ ] **Deliverable:** Login flow secure and session-aware; Managers vs. Reps see different UIs; SSN encrypted in DB

#### 1D. UI Stabilization & Integration Tests (Week 2, Days 1–2)

Tasks mapped to: All existing views (customers, inventory, reports)

<<<<<<< HEAD
- [x] Update `CustomersView`: Wire balance display to `CustomerService.get_by_id()` (live DB pull)
- [x] Update `CustomersView`: Wire payment processing to `PaymentService.record_payment()` and balance update
- [x] Update `InventoryView`: Wire data loaders to `PartService` and `SupplierCostService`
- [x] Update `ReportsHubView`: Wire all report endpoints to `ReportService` base methods
=======
- [ ] Update `CustomersView`: Wire balance display to `CustomerService.get_by_id()` (live DB pull)
- [ ] Update `CustomersView`: Wire payment processing to `PaymentService.record_payment()` and balance update
- [] Update `InventoryView`: Wire data loaders to `PartService` and `SupplierCostService`
- [ ] Update `ReportsHubView`: Wire all report endpoints to `ReportService` base methods
>>>>>>> 1efc4b5 (Checked the to do and modify the inventory)
- [ ] Run integration test: Create order → check invoice total → check invoice in DB
- [ ] Run integration test: Record payment → check customer balance updated → check Payments table
- [ ] Run integration test: Load inventory → verify stock counts match DB
- [ ] **Deliverable:** All existing views pull live data from new service layer; no more hardcoded test data

#### Phase 1 Summary

**Dependencies Cleared:** ✅ Database is source of truth. Services provide consistent query interface. RBAC prevents unauthorized access.  
**Ready for Phase 2:** ✅ All views can be enhanced with new workflows (orders, payroll, etc.).  
**Estimated Duration:** 10 business days (2 weeks, assuming 5 hr/day on project).

---

### Phase 2: Core Workflows and UI Integration (Weeks 3–4)

**Goal:** Implement orders, invoicing, payroll, timecards, and multi-part workflows. Enforce all business rules end-to-end.  
**Status:** Builds on Phase 1; enables Phase 3 testing and hardening.

#### 2A. Orders & Invoices Workflow (Week 3, Days 1–3) — **PRIORITY: CRITICAL**

Tasks mapped to: Req 2, 3, 11, 13, 15; Technical items 10, 11

- [x] Implement `OrdersView` in `orders_and_invoices.py`:
  - [x] "New Order" form: Customer lookup, part multi-select, qty input, dynamic line item UI
  - [x] Over-selling guard: Check `part.stock_count >= line_qty` before allowing confirm (Manager override option)
  - [x] Line item management: Add/remove rows, recalculate invoice total on the fly
  - [ ] Submit order: Call `InvoiceService.create()` → stores invoice + line items → sets status='pending'
  - [x] Invoice list: Display pending/shipped invoices; filter by status
  - [ ] Shipment button: Click → `InvoiceService.update_status('shipped')` → triggers `PartService.update_stock()` for each line
  - [x] Cancellation: Only allow if status != 'shipped'; sets status='void', removes line items
- [ ] Backend order validation:
  - [ ] Quantity must be >= 1
  - [ ] Customer must exist and `is_active = TRUE`
  - [ ] Part must exist and have stock (or Manager override)
  - [ ] Invoice total calculated correctly: `SUM(qty * selling_price)` per line
- [ ] Implement invoice-to-shipment chain: When marked shipped, decrement parts and update customer balance (Req 13)
- [ ] **Deliverable:** Full order-to-shipment flow; parts decrement on ship; customer balance updates; no overselling without Manager override

#### 2B. Payroll & Timecard Workflows (Week 3, Days 3–5 + Week 4, Day 1) — **PRIORITY: CRITICAL**

Tasks mapped to: Req 6, 7, 8, 9, 12; Technical items 1, 2, 8, 9, 12

- [ ] Implement weekly timecard auto-generation:
  - [x] On app startup: `TimecardService.check_if_week_exists(this_week_date)`
  - [x] If missing AND not Sales Rep AND `is_active = TRUE`: Auto-create blank timecards for all hourly staff
  - [x] Prevent duplicates: Validate no existing record before insert
  - [ ] Test: Restart app mid-week → verify no duplicate timecards created

- [x] Implement `PayrollView` in `payroll.py`:
  - [x] "Missing Timecards" panel: Show hourly staff missing entries for current week (using `LEFT JOIN` logic)
  - [x] "Payroll Issuance" section:
    - [x] Button to generate weekly payroll (Monday via manual trigger in demo)
    - [x] For each hourly employee with complete timecard: `gross = hours_worked * hourly_wage`
    - [x] For each Rep this week: `commission = total_invoices_rep_wrote * 0.05` (5%)
    - [x] Export payroll to CSV: `employee_number | name | gross | commission | net`
  - [x] Button to "Issue Check": Records `Payment` for each employee, updates YTD sales
  - [x] Payroll history: List of past payroll runs (date, num checks issued)

- [ ] Implement sales rep commission tracking:
  - [x] Identify invoices written by rep this week (filter by `invoices.rep_id`)
  - [x] Sum invoice totals, multiply by 0.05 → commission amount
  - [ ] Show in payroll export and Reports tab

- [x] Implement YTD sales update:
  - [x] Query `SUM(invoices.total_amount)` per rep since year start
  - [x] Store in employee record (or ephemeral in report)
  - [x] Display in Rep Performance report

- [ ] **Deliverable:** Timecards auto-generate weekly. Payroll form calculates gross (hourly) + commission (5% reps) + YTD. Checks issued and exported.

#### 2C. Advanced Reporting & Analytics (Week 4, Days 2–4) — **PRIORITY: HIGH**

Tasks mapped to: Req 4, 9; Technical items 3, 4, 7, 9, 12, 13

- [x] Complete "Customer List & Balances" report:
  - [ ] Query: `SELECT customer_id, company_name, balance, is_active FROM Customers`
  - [ ] Dynamic search/filter by company name or customer number
  - [ ] Show: Customer #, Company, Address, Current Balance, Status (Active/Closed)
  - [ ] Export to CSV with same columns
- [x] Complete "Customer Payment History" report:
  - [ ] Query: `SELECT customer_id, payment_date, amount, payment_method FROM Payments ORDER BY payment_date DESC`
  - [ ] Optional filter by date range or customer
  - [ ] Display: Customer, Date, Amount, Method, Running Balance
  - [ ] Export to CSV
- [x] Enhance Stock Ordering Report (Technical item 3):
  - [ ] Query: `SELECT part_id, part_number, description, stock_count, trigger_amount, on_order FROM Parts WHERE stock_count <= trigger_amount ORDER BY stock_count ASC`
  - [ ] Show parts due for restock with current vs. target levels
  - [ ] Link to supplier cost data (cheapest supplier per part)
- [ ] Implement Supplier-Centric View (Technical item 7):
  - [ ] Query suppliers, their parts, and costs
  - [ ] Aggregate total spending per supplier this week/month
  - [ ] Sort by supplier ID and part ID
- [x] Implement High-Performance Reps Report (Technical item 12):
  - [ ] Identify reps with > 10 invoices in target week
  - [ ] Show: Rep Name, Invoice Count, Total Sales, Avg Invoice Value
- [ ] Implement Best Price Procurement (Technical item 13):
  - [ ] `SELECT DISTINCT ON (part_id) ... ORDER BY part_id, cost ASC` → lowest cost per part
  - [ ] Display recommended supplier for each part
- [ ] **Deliverable:** All 5 reports in ReportsHubView fully functional with live data, export, and filtering

#### 2D. Inventory & Stock Management (Week 4, Days 3–4) — **PRIORITY: MEDIUM**

Tasks mapped to: Req 5, 13; Technical items 5, 6, 14

- [x] Implement critical stock alerts:
  - [x] Query: `Parts WHERE stock_count <= 1 AND on_order = FALSE AND part_id IN (SELECT DISTINCT part_id FROM Invoice_Lines WHERE invoice_id IN (SELECT invoice_id FROM Invoices WHERE status = 'pending'))`
  - [x] Display as critical alerts in top bar alert dropdown
  - [x] Show: Part #, Current Stock, Linked Unshipped Orders count
- [ ] Implement inventory bottleneck detection (Technical item 5):
  - [x] Join `Invoice_Lines`, `Invoices`, `Parts`
  - [x] Filter: `Invoices.status = 'pending' AND Parts.stock_count <= 1`
  - [ ] Show in alerts: "Order #X blocked: Part Y (stock: 0) needed"
- [ ] Dynamic restocking strategy (Technical item 14):
  - [x] Find top 2 parts by YTD sales volume
  - [x] Double their `restock_value`
  - [x] Verify no unintended parts modified
- [ ] Price inflation logic (Technical item 15):
  - [x] Parts with 0 YTD sales:
    - [x] If `restock_value < 4`: price \*= 1.10
    - [x] If `restock_value >= 4`: price \*= 1.20
  - [x] Run logic on-demand (admin button or scheduled)
- [ ] **Deliverable:** Critical alerts working, bottlenecks shown, dynamic restocking and pricing applied

#### Phase 2 Summary

**Dependencies:** Builds on Phase 1 database and services.  
**New Features:** Orders → Shipment → Stock Decrement → Balance Update → Payroll → Commission. Full invoice lifecycle. All reports live.  
**Ready for Phase 3:** ✅ All workflows implemented; now need testing, audit logging, and final polish.  
**Estimated Duration:** 10 business days (2 weeks, 5 hr/day).

---

### Phase 3: Validation, Hardening, and Delivery (Weeks 5–6)

**Goal:** Comprehensive testing, audit logging, security hardening, and final QA. Ensure all 17 requirements are proven and demo-ready.  
**Status:** Final validation before submission.

#### 3A. Unit & Integration Testing (Week 5, Days 1–3) — **PRIORITY: CRITICAL**

Tasks mapped to: All requirements via test coverage

- [ ] Test database layer:
  - [ ] Test `CustomerService.update_balance()`: Verify balance = invoices - payments
  - [ ] Test `InvoiceService.create()`: Verify invoice total = SUM(lines)
  - [ ] Test `InvoiceService.update_status('shipped')`: Verify parts decrement correctly
  - [ ] Test `PartService.get_low_stock()`: Verify filter logic
  - [ ] Test `TimecardService.create_weekly_timecards()`: Verify no duplicates, excludes Reps
  - [ ] Test `PaymentService.record_payment()`: Verify balance updates, invoice marked paid when total >= sum
  - [ ] Test `SupplierCostService.get_lowest_cost_supplier()`: Verify correct supplier returned
- [ ] Test business rules:
  - [ ] Req 1: Customer balance = invoices - payments ✓
  - [ ] Req 2: Shipping status transitions (pending → shipped) ✓
  - [ ] Req 3: Payment status (not paid → paid when total >= sum) ✓
  - [ ] Req 4: Rep sales totals (SUM by rep_id) ✓
  - [ ] Req 5: Stock vs. On Order alerts (critical when stock <= 1 + unshipped) ✓
  - [ ] Req 6–9: Timecards, payroll, commission (5%), YTD sales ✓
  - [ ] Req 10–17: All CRUD and rule-based logic ✓
- [ ] Test RBAC:
  - [ ] Manager can view/edit payroll, timecards, prices ✓
  - [ ] Rep cannot see payroll or timecard tabs ✓
  - [ ] Unauthorized write attempt → Access Denied alert ✓
- [ ] **Deliverable:** Unit test suite (>30 tests) covering all services, business rules, and RBAC paths; all tests passing

#### 3B. Audit Logging & Safety Nets (Week 5, Days 3–5) — **PRIORITY: HIGH**

Tasks mapped to: FS-Sec1, FS-Sec2; Safety Nets 1–3

- [ ] Implement audit logging in critical flows:
  - [ ] Log every price modification: INSERT `Logs(actor_id, action='PRICE_UPDATE', target_table='Parts', target_id=part_id, details='{old_price, new_price}', timestamp=NOW())`
  - [ ] Log every payroll check issuance: INSERT `Logs(actor_id, action='PAYROLL_ISSUED', target_table='Payments', target_id=payment_id, details='{employee_id, amount}', timestamp=NOW())`
  - [ ] Log every invoice shipment: INSERT `Logs(actor_id, action='INVOICE_SHIPPED', target_table='Invoices', target_id=invoice_id, details='{status_change, stock_decrements}', timestamp=NOW())`
  - [ ] Log customer balance updates: INSERT `Logs(actor_id, action='BALANCE_UPDATE', target_table='Customers', target_id=customer_id, details='{old_balance, new_balance, reason}', timestamp=NOW())`
- [ ] Weekly trigger resilience (Safety Net 2):
  - [ ] Change timecard generation from strict "Monday 12:00 AM" to "on app startup"
  - [ ] Check if timecards for current week exist
  - [ ] Only create if missing (idempotent logic)
  - [ ] Test: Restart app 3 times in same week → verify only 1 timecard set created
- [ ] Data integrity constraints (Safety Net 3):
  - [ ] Add `UNIQUE(part_id, supplier_id)` on `Part_Suppliers`
  - [ ] Verify no duplicate supplier-part entries can be inserted
  - [ ] Test constraint violation → error handling in UI
- [ ] Query audit report:
  - [ ] Expose `Logs` table via read-only query in Reports tab
  - [ ] Filter by action type, date range, actor
  - [ ] Export to CSV for instructor verification
- [ ] **Deliverable:** Audit trail complete for all sensitive actions; resilience patterns in place; all safety nets verified

#### 3C. Controller Layer & Authorization (Week 5, Days 4–5 + Week 6, Day 1) — **PRIORITY: MEDIUM**

Tasks mapped to: FS-Sec3, FS-Sec5, FS-Sec6

- [x] Add transaction guards to all writes:
  - [x] `@auth_required`, `@role_required('Manager')` decorators on sensitive endpoints
  - [x] Re-validate user session before INSERT/UPDATE/DELETE
  - [ ] Wrap multi-step operations (e.g., shipment → stock decrement → balance update) in transaction block
- [ ] Restrict price edits:
  - [ ] `InventoryView` price field: Read-only unless `current_user.position == 'Manager'`
  - [ ] Backend: `PartService.update()` checks role before allowing price change
- [x] Restrict worker file access (timecards, payroll):
  - [x] `PayrollView`, `PayrollView.timecards_panel`: Hidden for non-Managers
  - [ ] Backend: Query endpoints return 403 if non-Manager requests payroll/timecard data
- [ ] Form validation guards:
  - [ ] Invoice line qty >= 1 and <= stock_count (unless Manager override)
  - [ ] Payment amount > 0 and <= outstanding balance
  - [ ] Timecard hours >= 0 and <= 168 (max hours in week)
- [ ] Error handling:
  - [ ] Invalid form data → show validation error message (red banner)
  - [ ] Unauthorized action → show "Access Denied" alert
  - [ ] Database constraint violation → show friendly error (e.g., "Duplicate supplier for this part")
- [ ] **Deliverable:** All sensitive writes protected by role checks; form validation in place; error messages user-friendly

#### 3D. Final QA & Verification Package (Week 6, Days 2–5) — **PRIORITY: CRITICAL**

Tasks mapped to: All 17 requirements + FS-Sec items; Delivery readiness

- [ ] Create verification checklist (screenshot evidence):
  - [ ] Req 1: Show customer detail with balance calculation (screenshot)
  - [ ] Req 2–3: Show shipping status and payment status in invoice list (screenshot)
  - [ ] Req 4: Show rep performance report with totals (screenshot)
  - [ ] Req 5: Show critical stock alert in alerts dropdown (screenshot)
  - [ ] Req 6–9: Show timecard form, payroll issuance, commission calculation, YTD sales (screenshot)
  - [ ] Req 10–17: Show part CRUD, invoice line items, commission, inventory update, supplier costs, customer details, employee profile, hourly wage (screenshot)
- [ ] Run end-to-end workflows:
  - [ ] Workflow 1: New order → multi-part → ship → stock decrement → customer balance update → verify DB
  - [ ] Workflow 2: Record payment → customer balance decreases → invoice marked paid → verify DB
  - [ ] Workflow 3: Timecard auto-generated → payroll issued → commission calculated → check exported → verify DB
  - [ ] Workflow 4: Price updated by Manager → audit log created → verify Logs table
  - [ ] Workflow 5: Rep logs in → payroll tab hidden; Manager logs in → payroll visible → verify RBAC
- [ ] Performance validation:
  - [ ] Generate 1000 invoice records → verify report loads in < 2 sec
  - [ ] Query stock alerts with 100+ parts → verify < 1 sec response
  - [ ] Concurrent payroll generation (if multi-user): Verify no race conditions
- [ ] Documentation:
  - [ ] Update README.md with setup instructions (DB schema, seed data, venv activation)
  - [ ] Create DEPLOYMENT.md with prerequisite checklist (PostgreSQL version, Python 3.9+, CustomTkinter)
  - [ ] Document RBAC model: Manager vs. Rep vs. Hourly roles and restrictions
  - [ ] Screenshot guide: 5–8 key workflows showing all 17 requirements
- [ ] Demo package:
  - [ ] Sample data set: 10 customers, 20 parts, 4 employees, sample invoices
  - [ ] Test account: Manager (user: `manager`, pwd: `demo123`), Rep (user: `rep1`, pwd: `demo123`)
  - [ ] Demo script: "30-minute walkthrough" checklist of key workflows
- [ ] Final sign-off:
  - [ ] All 17 requirements verified in code and screenshots ✓
  - [ ] All FS-Sec items implemented and tested ✓
  - [ ] All 15 technical items completed ✓
  - [ ] All business rules enforced end-to-end ✓
  - [ ] Zero known bugs (all issues resolved or documented as future work)
- [ ] **Deliverable:** Complete demo package with evidence, working system, documentation, and sign-off checklist

#### Phase 3 Summary

**Dependencies:** Builds on Phase 2 complete workflows.  
**Focus:** Quality, security, compliance with all 17 requirements.  
**Outcome:** Submission-ready system with full audit trail, test coverage, and documentation.  
**Estimated Duration:** 10 business days (2 weeks, 5 hr/day).

---

## Phase Dependency Map

```text
Phase 1 (Weeks 1–2)          Phase 2 (Weeks 3–4)          Phase 3 (Weeks 5–6)
├─ Database Schema      →     ├─ Orders & Invoices   →     ├─ Unit/Integration Tests
├─ Service Layer        →     ├─ Payroll & Timecards →     ├─ Audit Logging
├─ RBAC & Security      →     ├─ Reports & Analytics →     ├─ Controller Authorization
└─ UI Integration       →     └─ Stock Management    →     └─ Final QA & Verification
```

Phase 1 must complete before Phase 2 starts (database is prerequisite).  
Phase 2 can proceed in parallel subtasks (Orders, Payroll, Reports, Inventory).  
Phase 3 requires Phase 2 fully complete; focuses on validation and polish.

---

## Quick Reference: Phase-to-Requirement Mapping

| Requirement                  | Phase               | Section              | Status      |
| ---------------------------- | ------------------- | -------------------- | ----------- |
| Req 1: Customer Balance      | 1C (DB) + 2A (Flow) | Orders/Payments      | Integrated  |
| Req 2: Shipping Status       | 2A                  | Orders & Invoices    | In Phase 2  |
| Req 3: Payment Status        | 2A                  | Orders & Invoices    | In Phase 2  |
| Req 4: Rep Sales Tracking    | 2C                  | Advanced Reporting   | In Phase 2  |
| Req 5: Stock vs. On Order    | 2D                  | Inventory & Stock    | In Phase 2  |
| Req 6–9: Payroll & Timecards | 2B                  | Payroll & Timecard   | In Phase 2  |
| Req 10–17: CRUD & Rules      | 1B + 2A-D           | Services + Workflows | Distributed |

---

---

## Technical Implementation Plan

### 1. Missing Timecards

- [ ] Run `LEFT JOIN` between `Employees` and `Timecards` for target week
- [ ] Filter rows where timecard is `NULL`
- [ ] Exclude `position = 'Sales Rep'`
- [ ] Filter for active employees only (QD-Sec1)
- [ ] Validate hourly staff are flagged correctly

### 2. Payroll Issuance

- [ ] Build backend payroll issuance script that iterates `Timecards`
- [ ] Calculate gross amount using `Gross Amount = Hourly Wage * Hours Worked`
- [ ] Export payroll output to structured file (`CSV` or `JSON`)
- [ ] Validate output for bank/check-printing module

### 3. Restock Report

- [ ] Implement query on `Parts` where `stock_count <= trigger_amount`
- [ ] Expose result in backend reporting endpoint/service
- [ ] Populate Alerts dropdown with report output
- [ ] Validate alert data freshness and accuracy

### 4. Critical Stock Check

- [x] Filter inventory where `stock_count <= 1`
- [x] Add condition `on_order = False`
- [x] Surface results as critical alerts
- [ ] Validate no false positives for items already on order

### 5. Inventory Bottleneck

- [ ] Join `Invoice_Lines`, `Invoices`, and `Parts`
- [ ] Identify parts with `stock_count <= 1`
- [ ] Filter invoices where `is_shipped = False`
- [ ] Show bottleneck reason for stuck orders

### 6. Supplier Cost Analysis

- [ ] Join `Parts`, `Part_Suppliers`, and `Suppliers`
- [ ] Filter by `trigger_level`
- [ ] Sort using `ORDER BY part_id, cost ASC`
- [ ] Confirm cheapest supplier appears first per part

### 7. Supplier-Centric View

- [ ] Reuse supplier-cost join logic
- [ ] Sort using `ORDER BY supplier_id, part_id`
- [ ] Run `SUM(total_amount)` on `Invoices` by `rep_id`
- [ ] Filter for week ending August 9, 2006

### 8. YTD Sales Update

- [ ] Write `UPDATE` with subquery for year-to-date totals
- [ ] Compute `SUM` of invoices per rep from year start
- [ ] Store result in `ytd_sales` column
- [ ] Validate values against report output

### 9. Rep Analytics (report1)

- [ ] Compute `SUM(total)`
- [ ] Compute `COUNT(invoice_id)`
- [ ] Compute `MAX(total)` and `AVG(total)`
- [ ] Compute `COUNT(DISTINCT customer_id)`
- [ ] Save analytics to DBF file named `report1` (QD-Sec9)
- [ ] Sync `report1` data back to `SALESREP` table

### 10. Backlog Tracking

- [x] Filter `Invoices` where `is_shipped = False`
- [x] Expose as backend backlog dataset
- [x] Display backlog list in Orders tab
- [ ] Generate part-level list of ordered parts not yet shipped (QD-Sec10)
- [ ] Validate order counts match database

### 11. Shipment Blockers

- [x] Add `OrdersView` rule: compare `Part.stock_count` vs `Invoice_Line.quantity`
- [x] Flag parts where stock is insufficient
- [x] Show blocker reason in order details UI
- [ ] Validate blockers clear after restock

### 12. High-Performance Reps

- [x] Group invoices by rep for target week
- [x] Add `HAVING COUNT(invoice_id) > 10`
- [x] Return list of high-performance reps
- [ ] Validate threshold logic in tests

### 13. Best Price Procurement

- [ ] Use `SELECT DISTINCT ON (part_id)`
- [ ] Sort by `part_id, cost ASC`
- [ ] Return only lowest-cost supplier per part
- [ ] Validate one row per part in output

### 14. Dynamic Restocking Strategy

- [ ] Find top 2 parts by `SUM(quantity)` year-to-date
- [ ] Update those parts: `restock_value = restock_value * 2`
- [ ] Limit update strictly to selected part numbers
- [ ] Validate no unintended rows are modified

### 15. Price Inflation Logic

- [ ] Identify parts with 0 sales YTD
- [ ] If `restock_value < 4`, update `price = price * 1.10`
- [ ] If `restock_value >= 4`, update `price = price * 1.20`
- [ ] Validate updates with before/after report snapshot

## Requirement Checklist

### 1. Customer Account Tracking

- [ ] Add `balance` column to `Customers` table
- [ ] Implement backend balance computation (`total_invoices - total_payments`)
- [x] Show balance in `CustomersView`
- [ ] Add test for correct balance calculation

### 2. Shipping Status

- [x] Add `status` enum (`Pending`, `Shipped`) or `shipped_date` to `Invoices`
- [ ] Update backend when shipment is processed
- [x] Display status badge in Orders tab
- [ ] Add test for status transitions

### 3. Payment Status

- [x] Add `is_paid` boolean to `Invoices`
- [ ] Update payment workflow to set `is_paid`
- [x] Filter dashboard Total Revenue to paid invoices only
- [ ] Add test for paid-only revenue metric

### 4. Rep Sales Tracking

- [ ] Implement SQL `GROUP BY` sales query per sales rep
- [ ] Expose query in backend reports service
- [x] Show Rep Performance section in Reports tab
- [ ] Add test for rep totals

### 5. Stock vs. On Order

- [ ] Ensure inventory table stores `stock_count` and `on_order_count`
- [x] Add low-stock threshold check in alert/notice logic
- [x] Show critical alerts in top bar/alerts UI
- [ ] Add test for low-stock alert trigger

### 6. Weekly Timecards

- [ ] Create `Timecards` table linked to `employee_id`
- [ ] Add weekly scheduler (Monday 12:00 AM) to create blank timecards
- [ ] Ensure only hourly employees receive auto-generated records
- [ ] Add test for Monday timecard generation

### 7. Sales Rep Exclusion

- [ ] Add payroll validation: exclude employees where `position = 'Sales Rep'`
- [ ] Apply exclusion in timecard-required logic
- [ ] Reflect rule in payroll UI messaging
- [ ] Add test for sales rep exclusion behavior

### 8. Weekly Payroll (Checks)

- [ ] Create `Payments` table to log generated checks
- [ ] Implement backend payroll check issuance flow
- [ ] Add Print/Issue Check button in Payroll tab
- [ ] Add test for payment record creation and status update

### 9. Monday Payroll Report

- [ ] Implement `generate_payroll_report()` in database/backend layer
- [ ] Use formula: `Payment = SUM(Hours Worked * Hourly Wage)`
- [ ] Add Reports tab action to generate/view payroll report
- [ ] Add test for payroll report totals

### 10. Part Details CRUD

- [ ] Verify `Parts` fields: `part_number`, `selling_price`, `description`, `stock_count`
- [ ] Implement create/read/update/delete backend methods
- [ ] Build Inventory tab form and table actions
- [ ] Add CRUD tests for parts

### 11. Invoice Line Items

- [ ] Create one-to-many relationship: `Invoices` -> `InvoiceLineItems`
- [ ] Add backend methods for line item add/update/remove
- [x] Build dynamic multi-part line item UI in order/invoice flow
- [ ] Add test for invoice totals from multiple line items

### 12. Sales Commission

- [ ] Implement commission formula in payroll reporting logic
- [ ] Use formula: `Commission = Total Gross Sales * 0.05`
- [ ] Show commission values in payroll/report outputs
- [ ] Add test for commission calculation accuracy

### 13. Inventory Management

- [ ] Centralize stock update logic in inventory service/view model
- [ ] Decrement `stock_count` when invoice status changes to `Shipped`
- [ ] Refresh inventory UI in near real-time after shipment updates
- [ ] Add test for stock updates on shipped invoices

### 14. Multi-Supplier Costing

- [ ] Create `Part_Suppliers` junction table (`part_id`, `supplier_id`, `cost`)
- [ ] Add backend queries for part costs across suppliers
- [ ] Show supplier-specific cost options in inventory/procurement UI
- [ ] Add test for multi-supplier price retrieval

### 15. Customer Details

- [x] Ensure `Customers` includes `customer_number`, `company_name`, `address`
- [x] Populate invoice header fields when customer is selected
- [ ] Validate customer lookup/autocomplete flow in invoice UI
- [ ] Add test for invoice header auto-population

### 16. Employee Profiles

- [ ] Ensure `Employee` includes `ssn` (encrypted), `employee_number`, `address`, `position`
- [ ] Implement encryption/decryption handling for SSN storage
- [ ] Bind profile data to profile overlay UI
- [ ] Add test for secure SSN storage and retrieval behavior

### 17. Hourly Wages

- [ ] Add `hourly_wage` column to `Employee`
- [ ] Set `hourly_wage = 0` or `NULL` for Sales Reps
- [ ] Enforce hourly wage rules in payroll calculation logic
- [ ] Add test for mixed employee type payroll calculations

---

## Functional Specification Plan (FS-Sec)
### FS-Sec1: Security and Access Control

- [x] Create login view module for credential validation against `Employees`
- [x] Restrict worker file access (timecards, payroll) to managers only (FS-Sec1)
- [x] Enforce RBAC checks before opening restricted tabs (Manager-only views)
- [x] Show Access Denied alert when non-manager requests restricted actions
- [x] Re-validate active session permissions before every sensitive `INSERT`/`UPDATE`
- [ ] Add tests for manager and non-manager access paths

### FS-Sec2: Automated Identifiers

- [ ] Ensure primary keys use auto-increment strategy (`SERIAL`/`BIGSERIAL`)
- [x] Remove manual ID entry from create forms
- [ ] Validate generated IDs are unique and sequential
- [ ] Keep `part_number` as a flexible business SKU field

### FS-Sec3-FS-Sec5: Transactional Interface and Form Engine

- [x] Build New Order form flow in Orders tab (placement and cancellation)
- [x] Use entry components for editable text fields (address, descriptions)
- [x] Use dropdown/combobox components for existing customer/supplier selection
- [ ] Add modification workflow for transactional records
- [ ] Restrict price-edit controls in Inventory tab to Manager role only
- [x] Enable customer profile modification (FS-Sec5): company name, address, contact info
- [ ] Add UI and backend tests for form validation and submission

### FS-Sec6: Real-time Critical Alerts

- [ ] Run stock check function whenever an order is placed/updated
- [x] Trigger critical notice when `current_stock <= critical_level`
- [x] Ensure bell icon/banner updates from alert state
- [ ] Add test for critical alert trigger and display timing

### FS-Sec7: Report Generation Views

- [x] Create Inventory Report view (parts, stock counts, costs)
- [x] Create Weekly Sales report (last 7 days invoice total)
- [x] Create Sales Rep Payroll report (commission calculation: `Sales * 0.05`)
- [x] Create Stock Ordering report (`stock <= trigger`)
- [x] Create searchable Customer List report (profiles and balances)
- [ ] Add export option for each report (CSV/JSON)

### Controller Layer (Architectural Impact)

- [ ] Add controller/service layer between UI and database calls
- [ ] Route all restricted writes through authorization guard methods
- [ ] Centralize transaction validation and audit-friendly checks
- [ ] Add integration tests proving unauthorized updates are blocked

### FS-Sec Progress Summary

- [ ] Security/RBAC implementation complete
- [ ] Automated ID workflow complete
- [ ] Transactional forms complete
- [ ] Real-time alerts complete
- [ ] Report views complete

---

## Safety Nets (Recommended)

### 1. Audit Logging (FS-Sec1 Supplement)

- [ ] Create hidden `Logs` table for sensitive action tracking
- [ ] Log every price modification event (FS-Sec5)
- [ ] Log every payroll check issuance event (Rule 8)
- [ ] Capture actor identity, action type, timestamp, and target record
- [ ] Add query/report path for instructor demo verification

### 2. Weekly Trigger Resilience (Rule 6 and Rule 9)

- [ ] Replace strict Monday midnight dependency with "first launch of the week" logic
- [ ] On app startup, check whether current-week timecards already exist
- [ ] Auto-generate missing weekly timecards only when absent
- [ ] Prevent duplicate generation when app restarts in the same week
- [ ] Add test for startup behavior with and without existing weekly records

### 3. Data Integrity for Multi-Supplier Costing (Rule 14)

- [ ] Add unique constraint on `Part_Suppliers(part_id, supplier_id)`
- [ ] Add migration/update script for existing schema
- [ ] Validate duplicate supplier-part entries are blocked
- [ ] Add test coverage for constraint enforcement and error handling

---

## Business Rules & Logic Specification

These are the authoritative business rules to implement in backend controllers, DB constraints, and UI guards. Each item is checkable so you can mark when the behavior is fully implemented and tested.

Inventory & Procurement Logic

- [x] Restock Trigger: Flag part for restocking when `stock_count <= trigger_amount` (FS-Sec6)
- [x] Critical Restock Priority: If `stock_count` in (0,1) AND `on_order = FALSE` AND part appears in an unshipped invoice (status = 'active'), mark as critical priority (QD-Sec5)
- [ ] Prevent Duplicate Orders: Verify `on_order = FALSE` before creating a restock PO
- [ ] Receiving POs: When PO `received = TRUE`, increment `Parts.stock_count` by `quantity_ordered` and set `on_order = FALSE`
- [x] Lowest Cost Sourcing: Recommend supplier with lowest `cost` from `Part_Suppliers` when creating restock reports
- [ ] Dynamic Inventory Valuation:
  - [x] If part not ordered this year → apply price inflation based on `restock_value` (10% if <4, 20% if >=4)
  - [x] Double `restock_value` for the two highest-selling parts of the year (QD-Sec14)

Employee & Payroll Logic

- [x] Hourly Compensation: Gross = `hours_worked * hourly_wage` (timecards required weekly)
- [ ] Timecard Missing Definition: Missing if no `timecards` record for `week_date` and `employee.is_active = TRUE` and employee is hourly; payroll audit runs Monday for prior week
- [x] Sales Rep Commission: 5% commission on each invoice's `total_amount` for rep-written invoices that week
- [ ] YTD Sales Tracking: Maintain `ytdsales` as cumulative year-to-date gross sales; reset to 0.00 at fiscal year start

Sales, Invoicing & Account Balances

- [ ] Invoice Totals: `invoice.total_amount = SUM(invoice_lines.quantity_ordered * parts.selling_price)` (calculated dynamically)
- [ ] Over-selling Prevention: Block creation of `invoice_line` where `quantity_ordered > part.stock_count` unless Manager override
- [ ] Order Fulfillment: When invoice `status` -> 'shipped', decrement `Parts.stock_count` by the respective `quantity_ordered` for each line
- [ ] Invoice Immutability: Once `shipped`, lock invoice and its lines from edits
- [ ] Cancellation: Cancelling sets invoice `status = 'void'` and removes invoice_lines; prohibit cancellation if `status = 'shipped'`
- [ ] Payments & Partial Payments: Track in `customer_payments`; invoice becomes `is_paid` when cumulative payments >= `total_amount`; otherwise adjust customer's `current_balance`
- [ ] Customer Balance Updates: Increase `current_balance` when invoice is shipped; decrease when payments logged
- [x] Customer Deletion Rule: Do not allow deletion if customer has invoices; set `is_active = FALSE` to close account

System, Security & Reporting Rules

- [x] Automated Identifiers: All primary keys use `SERIAL`/`BIGSERIAL` sequences
- [x] RBAC: Internal employees and reps may place/cancel orders; only Managers can view/modify worker files or approve stock overrides
- [ ] Audit Trail: Log user, action, target, and timestamp for sensitive changes (wages, prices, SSNs, payroll issuance)
- [x] Data Integrity Constraints: Quantities >= 0; currency fields use `NUMERIC(10,2)`
- [ ] Legacy Export: Weekly YTD sales report exports read-only to `.DBF` format (QD-Sec9)
- [ ] Secure SALESREP View: Provide a view exposing only `employee_number`, `name`, `ytdsales`, `commission_rate` (exclude SSN, hourly_wage)

---

Mark each item as implemented when you have DB constraints, backend logic, UI changes, and tests in place.
