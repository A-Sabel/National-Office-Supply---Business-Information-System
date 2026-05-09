-- ============================================================
--  National Office Supplies — PostgreSQL DDL
--  Run this in order.
-- ============================================================

-- ── Drop existing tables (safe re-run) ──────────────────────
DROP TABLE IF EXISTS employee_payments  CASCADE;
DROP TABLE IF EXISTS customer_payments  CASCADE;
DROP TABLE IF EXISTS purchase_orders    CASCADE;
DROP TABLE IF EXISTS timecards          CASCADE;
DROP TABLE IF EXISTS invoice_lines      CASCADE;
DROP TABLE IF EXISTS invoices           CASCADE;
DROP TABLE IF EXISTS item_parts         CASCADE;
DROP TABLE IF EXISTS parts              CASCADE;
DROP TABLE IF EXISTS suppliers          CASCADE;
DROP TABLE IF EXISTS employees          CASCADE;
DROP TABLE IF EXISTS customers          CASCADE;


-- ============================================================
--  1. ENTITIES
-- ============================================================

-- TABLE 1: customers
CREATE TABLE customers (
    customer_number  SERIAL         PRIMARY KEY,
    customer_name    VARCHAR(100)    NOT NULL,
    company_name     VARCHAR(100)    NOT NULL,
    phone_number     VARCHAR(20),
    address          TEXT            NOT NULL,
    current_balance  NUMERIC(10,2)   NOT NULL DEFAULT 0.00,
    is_active        BOOLEAN         NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE  customers                  IS 'Tracks customer accounts, balances, and contact info.';
COMMENT ON COLUMN customers.is_active        IS 'Set FALSE instead of deleting accounts that have invoice history.';
COMMENT ON COLUMN customers.current_balance  IS 'Running account balance; updated by customer_payments triggers.';


-- TABLE 2: employees
--   Stores all employee types: Hourly, Sales Rep, Manager.
--   hourly_wage is NULL for non-hourly staff.
--   ytdsales and commission_rate are meaningful only for Sales Reps.
CREATE TABLE employees (
    employee_number  SERIAL          PRIMARY KEY,
    employee_name    VARCHAR(100)    NOT NULL,
    position         VARCHAR(50)     NOT NULL
                        CHECK (position IN ('Manager', 'Hourly', 'Sales Rep')),
    ssn              VARCHAR(11)     UNIQUE NOT NULL,
    employee_address TEXT            NOT NULL,
    username         VARCHAR(50)     UNIQUE NOT NULL,
    password_hash    VARCHAR(255)    NOT NULL,
    is_locked        BOOLEAN         NOT NULL DEFAULT FALSE,
    is_active        BOOLEAN         NOT NULL DEFAULT TRUE,
    hourly_wage      NUMERIC(10,2),
    ytdsales         NUMERIC(12,2)   NOT NULL DEFAULT 0.00,
    commission_rate  NUMERIC(3,2)    NOT NULL DEFAULT 0.05
);

COMMENT ON TABLE  employees               IS 'All employee types: Hourly, Sales Rep, Manager.';
COMMENT ON COLUMN employees.password_hash IS 'Store a bcrypt/argon2 hash — never plain text.';
COMMENT ON COLUMN employees.is_locked     IS 'Flipped to TRUE after 3 consecutive failed login attempts.';
COMMENT ON COLUMN employees.hourly_wage   IS 'NULL for salaried / Sales Rep employees.';
COMMENT ON COLUMN employees.ytdsales      IS 'Year-to-date sales total; updated when invoices are marked paid.';


-- TABLE 3: suppliers
CREATE TABLE suppliers (
    supplier_id   SERIAL        PRIMARY KEY,
    company_name  VARCHAR(100)  NOT NULL,
    phone_number  VARCHAR(20)   NOT NULL,
    address       TEXT
);

COMMENT ON TABLE suppliers IS 'Vendors that supply parts to NOS.';


-- TABLE 4: parts
CREATE TABLE parts (
    part_number    SERIAL          PRIMARY KEY,
    description    VARCHAR(255)    NOT NULL,
    selling_price  NUMERIC(10,2)   NOT NULL CHECK (selling_price >= 0),
    stock_count    INTEGER         NOT NULL DEFAULT 0 CHECK (stock_count >= 0),
    trigger_amount INTEGER         NOT NULL CHECK (trigger_amount >= 0),
    restock_value  INTEGER         NOT NULL CHECK (restock_value > 0),
    on_order       BOOLEAN         NOT NULL DEFAULT FALSE
);

COMMENT ON TABLE  parts                IS 'Inventory of all parts sold by NOS.';
COMMENT ON COLUMN parts.trigger_amount IS 'Restock warning fires when stock_count <= trigger_amount.';
COMMENT ON COLUMN parts.restock_value  IS 'Default quantity to order when restocking.';
COMMENT ON COLUMN parts.on_order       IS 'TRUE when an open purchase order exists for this part.';


-- ============================================================
--  2. JUNCTION & TRANSACTION TABLES
-- ============================================================

-- TABLE 5: item_parts
--   Resolves the many-to-many between parts and suppliers.
--   cost = what NOS pays the supplier (not the selling price).
CREATE TABLE item_parts (
    part_number INTEGER       NOT NULL REFERENCES parts(part_number)
                                   ON DELETE RESTRICT ON UPDATE CASCADE,
    supplier_id INTEGER       NOT NULL REFERENCES suppliers(supplier_id)
                                   ON DELETE RESTRICT ON UPDATE CASCADE,
    cost        NUMERIC(10,2) NOT NULL CHECK (cost >= 0),
    PRIMARY KEY (part_number, supplier_id)
);

COMMENT ON TABLE  item_parts       IS 'Maps which supplier sells which part, and at what cost to NOS.';
COMMENT ON COLUMN item_parts.cost  IS 'Purchase cost NOS pays — distinct from parts.selling_price.';



-- TABLE 6: invoices
CREATE TABLE invoices (
    invoice_id      SERIAL         PRIMARY KEY,
    employee_number INTEGER       NOT NULL REFERENCES employees(employee_number)
                                      ON DELETE RESTRICT ON UPDATE CASCADE,
    customer_number INTEGER       NOT NULL REFERENCES customers(customer_number)
                                      ON DELETE RESTRICT ON UPDATE CASCADE,
    date_written    DATE           NOT NULL DEFAULT CURRENT_DATE,
    total_amount    NUMERIC(10,2)  NOT NULL DEFAULT 0.00 CHECK (total_amount >= 0),
    status          VARCHAR(20)    NOT NULL DEFAULT 'active'
                       CHECK (status IN ('active', 'shipped', 'paid', 'void'))
);

COMMENT ON TABLE  invoices        IS 'Sales orders written by a sales rep for a customer.';
COMMENT ON COLUMN invoices.status IS 'Lifecycle: active → shipped → paid (or void).';



-- TABLE 7: invoice_lines
CREATE TABLE invoice_lines (
    invoice_id   INTEGER        NOT NULL REFERENCES invoices(invoice_id)
                                    ON DELETE CASCADE ON UPDATE CASCADE,
    part_number  INTEGER        NOT NULL REFERENCES parts(part_number)
                                    ON DELETE RESTRICT ON UPDATE CASCADE,
    quantity     INTEGER        NOT NULL CHECK (quantity > 0),
    line_total   NUMERIC(10,2)  NOT NULL CHECK (line_total >= 0),
    PRIMARY KEY (invoice_id, part_number)
);

COMMENT ON TABLE  invoice_lines IS 'Line items (parts + quantities) for each invoice.';
COMMENT ON COLUMN invoice_lines.line_total IS 'quantity × parts.selling_price at time of sale.';


-- TABLE 8: timecards
CREATE TABLE timecards (
    timecard_id      SERIAL PRIMARY KEY,
    employee_number INTEGER NOT NULL REFERENCES employees(employee_number)
                           ON DELETE RESTRICT ON UPDATE CASCADE,
    week_date       DATE NOT NULL,
    hours_worked    NUMERIC(5,2) NOT NULL CHECK (hours_worked >= 0 AND hours_worked <= 168)
);

COMMENT ON TABLE  timecards IS 'Weekly time records for hourly employees only.';
COMMENT ON COLUMN timecards.week_date  IS 'The week-ending (Saturday) date for this timecard.';


-- TABLE 9: purchase_orders
CREATE TABLE purchase_orders (
    po_number         SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(supplier_id)
                           ON DELETE RESTRICT ON UPDATE CASCADE,
    part_number INTEGER NOT NULL REFERENCES parts(part_number)
                           ON DELETE RESTRICT ON UPDATE CASCADE,
    order_date        DATE NOT NULL DEFAULT CURRENT_DATE,
    quantity_ordered INTEGER NOT NULL CHECK (quantity_ordered > 0),
    received          BOOLEAN NOT NULL DEFAULT FALSE
);

COMMENT ON TABLE  purchase_orders IS 'Restocking orders placed with suppliers.';
COMMENT ON COLUMN purchase_orders.received IS 'Set TRUE when stock arrives; triggers stock_count update.';


-- TABLE 10: customer_payments
CREATE TABLE customer_payments (
    payment_id       SERIAL PRIMARY KEY,
    customer_number INTEGER NOT NULL REFERENCES customers(customer_number)
                           ON DELETE RESTRICT ON UPDATE CASCADE,
    invoice_id       INTEGER REFERENCES invoices(invoice_id)
                           ON DELETE RESTRICT ON UPDATE CASCADE,
    payment_date     DATE NOT NULL DEFAULT CURRENT_DATE,
    amount_paid      NUMERIC(10,2) NOT NULL CHECK (amount_paid > 0),
    payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('check', 'cash', 'transfer'))
);

COMMENT ON TABLE  customer_payments IS 'Incoming payments; supports partial and general account credits.';
COMMENT ON COLUMN customer_payments.invoice_id IS 'NULL for general account credits not tied to a specific invoice.';


-- TABLE 11: employee_payments
CREATE TABLE employee_payments (
    payment_id           SERIAL PRIMARY KEY,
    employee_number      INTEGER NOT NULL REFERENCES employees(employee_number)
                               ON DELETE RESTRICT ON UPDATE CASCADE,
    timecard_id          INTEGER REFERENCES timecards(timecard_id)
                               ON DELETE SET NULL ON UPDATE CASCADE,
    invoice_period_end   DATE,
    check_number         VARCHAR(20) NOT NULL,
    amount_paid          NUMERIC(10,2) NOT NULL CHECK (amount_paid > 0),
    date_paid            DATE NOT NULL DEFAULT CURRENT_DATE,
    payment_type         VARCHAR(20) NOT NULL CHECK (payment_type IN ('hourly', 'commission'))
);

COMMENT ON TABLE  employee_payments              IS 'Payment records for all employees (hourly/commission).';
COMMENT ON COLUMN employee_payments.timecard_id  IS 'NULL for sales reps; references timecard for hourly employees.';
COMMENT ON COLUMN employee_payments.invoice_period_end IS 'Week-ending date for commission period; NULL for hourly timecards.';
COMMENT ON COLUMN employee_payments.payment_type IS 'Either "hourly" (from timecard) or "commission" (from ytdsales).';



-- ============================================================
--  INDEXES (common query patterns)
-- ============================================================

-- Speed up invoice lookups by customer and status
CREATE INDEX idx_invoices_customer  ON invoices(customer_number);
CREATE INDEX idx_invoices_status    ON invoices(status);
CREATE INDEX idx_invoices_employee  ON invoices(employee_number);

-- Speed up timecard queries by week (QD-Sec1, QD-Sec2)
CREATE INDEX idx_timecards_week     ON timecards(week_date);
CREATE INDEX idx_timecards_emp      ON timecards(employee_number);

-- Speed up low-stock part queries (QD-Sec3, QD-Sec4)
CREATE INDEX idx_parts_stock        ON parts(stock_count);

-- Speed up payment lookups
CREATE INDEX idx_payments_customer  ON customer_payments(customer_number);
CREATE INDEX idx_payments_invoice   ON customer_payments(invoice_id);

-- Speed up employee payment lookups
CREATE INDEX idx_employee_payments_emp   ON employee_payments(employee_number);
CREATE INDEX idx_employee_payments_date  ON employee_payments(date_paid);

-- Speed up PO lookups by part/supplier
CREATE INDEX idx_po_part            ON purchase_orders(part_number);
CREATE INDEX idx_po_supplier        ON purchase_orders(supplier_id);


-- Run this in your PostgreSQL database
CREATE OR REPLACE VIEW secure_employee_directory AS 
SELECT 
    employee_number, 
    employee_name, 
    position, 
    ytdsales, 
    commission_rate,
    is_active
FROM employees;