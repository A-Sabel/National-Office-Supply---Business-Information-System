# National Office Supply BIS - Progress Tracker

Use this file as your live implementation checklist.

## Overall Progress

- [ ] Milestone 1: Database schema updates complete
- [ ] Milestone 2: Backend logic complete
- [ ] Milestone 3: Frontend tab integration complete
- [ ] Milestone 4: Testing and validation complete

Completed Requirements: `0 / 17`  
Last Updated: `YYYY-MM-DD`

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

- [ ] Filter inventory where `stock_count <= 1`
- [ ] Add condition `on_order = False`
- [ ] Surface results as critical alerts
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

- [ ] Filter `Invoices` where `is_shipped = False`
- [ ] Expose as backend backlog dataset
- [ ] Display backlog list in Orders tab
- [ ] Generate part-level list of ordered parts not yet shipped (QD-Sec10)
- [ ] Validate order counts match database

### 11. Shipment Blockers

- [ ] Add `OrdersView` rule: compare `Part.stock_count` vs `Invoice_Line.quantity`
- [ ] Flag parts where stock is insufficient
- [ ] Show blocker reason in order details UI
- [ ] Validate blockers clear after restock

### 12. High-Performance Reps

- [ ] Group invoices by rep for target week
- [ ] Add `HAVING COUNT(invoice_id) > 10`
- [ ] Return list of high-performance reps
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

- [ ] Add `status` enum (`Pending`, `Shipped`) or `shipped_date` to `Invoices`
- [ ] Update backend when shipment is processed
- [ ] Display status badge in Orders tab
- [ ] Add test for status transitions

### 3. Payment Status

- [ ] Add `is_paid` boolean to `Invoices`
- [ ] Update payment workflow to set `is_paid`
- [ ] Filter dashboard Total Revenue to paid invoices only
- [ ] Add test for paid-only revenue metric

### 4. Rep Sales Tracking

- [ ] Implement SQL `GROUP BY` sales query per sales rep
- [ ] Expose query in backend reports service
- [ ] Show Rep Performance section in Reports tab
- [ ] Add test for rep totals

### 5. Stock vs. On Order

- [ ] Ensure inventory table stores `stock_count` and `on_order_count`
- [ ] Add low-stock threshold check in alert/notice logic
- [ ] Show critical alerts in top bar/alerts UI
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
- [ ] Build dynamic multi-part line item UI in order/invoice flow
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
- [ ] Populate invoice header fields when customer is selected
- [x] Validate customer lookup/autocomplete flow in invoice UI
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
- [ ] Restrict worker file access (timecards, payroll) to managers only (FS-Sec1)
- [ ] Enforce RBAC checks before opening restricted tabs (Manager-only views)
- [ ] Show Access Denied alert when non-manager requests restricted actions
- [ ] Re-validate active session permissions before every sensitive `INSERT`/`UPDATE`
- [ ] Add tests for manager and non-manager access paths

### FS-Sec2: Automated Identifiers

- [ ] Ensure primary keys use auto-increment strategy (`SERIAL`/`BIGSERIAL`)
- [ ] Remove manual ID entry from create forms
- [ ] Validate generated IDs are unique and sequential
- [ ] Keep `part_number` as a flexible business SKU field

### FS-Sec3-FS-Sec5: Transactional Interface and Form Engine

- [ ] Build New Order form flow in Orders tab (placement and cancellation)
- [ ] Use entry components for editable text fields (address, descriptions)
- [ ] Use dropdown/combobox components for existing customer/supplier selection
- [ ] Add modification workflow for transactional records
- [ ] Restrict price-edit controls in Inventory tab to Manager role only
- [ ] Restrict price-edit controls in Inventory tab to Manager role only
- [x] Enable customer profile modification (FS-Sec5): company name, address, contact info
- [ ] Add UI and backend tests for form validation and submission

### FS-Sec6: Real-time Critical Alerts

- [ ] Run stock check function whenever an order is placed/updated
- [ ] Trigger critical notice when `current_stock <= critical_level`
- [ ] Ensure bell icon/banner updates from alert state
- [ ] Add test for critical alert trigger and display timing

### FS-Sec7: Report Generation Views

- [ ] Create Inventory Report view (parts, stock counts, costs)
- [ ] Create Weekly Sales report (last 7 days invoice total)
- [ ] Create Sales Rep Payroll report (commission calculation: `Sales * 0.05`)
- [ ] Create Stock Ordering report (`stock <= trigger`)
- [ ] Create searchable Customer List report (profiles and balances)
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

1. Inventory & Procurement Logic

- [ ] Restock Trigger: Flag part for restocking when `stock_count <= trigger_amount` (FS-Sec6)
- [ ] Critical Restock Priority: If `stock_count` in (0,1) AND `on_order = FALSE` AND part appears in an unshipped invoice (status = 'active'), mark as critical priority (QD-Sec5)
- [ ] Prevent Duplicate Orders: Verify `on_order = FALSE` before creating a restock PO
- [ ] Receiving POs: When PO `received = TRUE`, increment `Parts.stock_count` by `quantity_ordered` and set `on_order = FALSE`
- [ ] Lowest Cost Sourcing: Recommend supplier with lowest `cost` from `Part_Suppliers` when creating restock reports
- [ ] Dynamic Inventory Valuation:
  - [ ] If part not ordered this year → apply price inflation based on `restock_value` (10% if <4, 20% if >=4)
  - [ ] Double `restock_value` for the two highest-selling parts of the year (QD-Sec14)

2. Employee & Payroll Logic

- [ ] Hourly Compensation: Gross = `hours_worked * hourly_wage` (timecards required weekly)
- [ ] Timecard Missing Definition: Missing if no `timecards` record for `week_date` and `employee.is_active = TRUE` and employee is hourly; payroll audit runs Monday for prior week
- [ ] Sales Rep Commission: 5% commission on each invoice's `total_amount` for rep-written invoices that week
- [ ] YTD Sales Tracking: Maintain `ytdsales` as cumulative year-to-date gross sales; reset to 0.00 at fiscal year start

3. Sales, Invoicing & Account Balances

- [ ] Invoice Totals: `invoice.total_amount = SUM(invoice_lines.quantity_ordered * parts.selling_price)` (calculated dynamically)
- [ ] Over-selling Prevention: Block creation of `invoice_line` where `quantity_ordered > part.stock_count` unless Manager override
- [ ] Order Fulfillment: When invoice `status` -> 'shipped', decrement `Parts.stock_count` by the respective `quantity_ordered` for each line
- [ ] Invoice Immutability: Once `shipped`, lock invoice and its lines from edits
- [ ] Cancellation: Cancelling sets invoice `status = 'void'` and removes invoice_lines; prohibit cancellation if `status = 'shipped'`
- [ ] Payments & Partial Payments: Track in `customer_payments`; invoice becomes `is_paid` when cumulative payments >= `total_amount`; otherwise adjust customer's `current_balance`
- [ ] Customer Balance Updates: Increase `current_balance` when invoice is shipped; decrease when payments logged
- [ ] Customer Deletion Rule: Do not allow deletion if customer has invoices; set `is_active = FALSE` to close account

4. System, Security & Reporting Rules

- [ ] Automated Identifiers: All primary keys use `SERIAL`/`BIGSERIAL` sequences
- [ ] RBAC: Internal employees and reps may place/cancel orders; only Managers can view/modify worker files or approve stock overrides
- [ ] Audit Trail: Log user, action, target, and timestamp for sensitive changes (wages, prices, SSNs, payroll issuance)
- [ ] Data Integrity Constraints: Quantities >= 0; currency fields use `NUMERIC(10,2)`
- [ ] Legacy Export: Weekly YTD sales report exports read-only to `.DBF` format (QD-Sec9)
- [ ] Secure SALESREP View: Provide a view exposing only `employee_number`, `name`, `ytdsales`, `commission_rate` (exclude SSN, hourly_wage)

---

Mark each item as implemented when you have DB constraints, backend logic, UI changes, and tests in place.
