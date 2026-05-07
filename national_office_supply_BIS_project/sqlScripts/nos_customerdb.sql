-- ============================================================
-- National Office Supplies BIS
-- MODULE: Customers
-- Based on: Case Narration Points 1, 15 | QD-Sec9 | FS-Sec1,2,4,5,6
-- ============================================================

-- TABLE DEFINITION
-- Satisfies: FS-Sec2 (auto-generated customer_number via SERIAL)
CREATE TABLE IF NOT EXISTS customers (
    customer_number  SERIAL          PRIMARY KEY,          -- FS-Sec2: system-generated
    company_name     VARCHAR(100)    NOT NULL,             -- Point 15
    contact_name     VARCHAR(100),                         -- Point 15: individual contact
    phone_number     VARCHAR(20),
    address          TEXT            NOT NULL,             -- Point 15
    current_balance  NUMERIC(10,2)   NOT NULL DEFAULT 0.00,-- Point 1: track current balance
    is_active        BOOLEAN         NOT NULL DEFAULT TRUE  -- allows "soft delete" without
                                                           -- losing invoice history
);

-- INTEGRITY CONSTRAINTS
-- Domain Integrity: balance cannot go below -99999.99 (credit limit floor)
ALTER TABLE customers
    ADD CONSTRAINT chk_balance CHECK (current_balance >= -99999.99);

-- ============================================================
-- SEED DATA — 30 records minimum (required by spec)
-- ============================================================
INSERT INTO customers (company_name, contact_name, phone_number, address, current_balance, is_active)
VALUES
  ('Acme Office Corp',         'James Reyes',       '(02) 8100-0001', '12 Ayala Ave, Makati City',              1250.00,  TRUE),
  ('Beta Solutions Inc',       'Maria Santos',      '(02) 8100-0002', '55 Ortigas Center, Pasig City',           895.50,  TRUE),
  ('Gamma Enterprises',        'Ricardo Tan',       '(02) 8100-0003', '3 Bonifacio High St, BGC, Taguig',        320.00,  TRUE),
  ('Delta Trading Co',         'Lorna Cruz',        '(02) 8100-0004', '78 Shaw Blvd, Mandaluyong',              2100.75,  TRUE),
  ('Epsilon Supplies',         'Fernando Aquino',   '(02) 8100-0005', '9 Quezon Ave, Quezon City',                 0.00,  TRUE),
  ('Zeta Distributors',        'Ana Villanueva',    '(02) 8100-0006', '101 España Blvd, Manila',                 540.00,  TRUE),
  ('Eta Business Solutions',   'Paolo Soriano',     '(02) 8100-0007', '22 Aurora Blvd, Cubao',                   125.00,  TRUE),
  ('Theta Global Inc',         'Cynthia Lim',       '(02) 8100-0008', '88 Katipunan Ave, Quezon City',          3200.00,  TRUE),
  ('Iota Marketing',           'Rodrigo Dela Cruz', '(02) 8100-0009', '14 Mabini St, Ermita, Manila',             75.50,  TRUE),
  ('Kappa Ventures',           'Sophia Garcia',     '(02) 8100-0010', '33 Jupiter St, Makati City',             1800.00,  TRUE),
  ('Lambda Tech Corp',         'David Ocampo',      '(02) 8100-0011', '5 Techno Hub, UP Campus, QC',             990.00,  TRUE),
  ('Mu Creative Agency',       'Elena Ramos',       '(02) 8100-0012', '47 Sgt. Esguerra, South Triangle, QC',   445.25,  TRUE),
  ('Nu Logistics Ltd',         'Carlos Bautista',   '(02) 8100-0013', '200 EDSA, Balintawak, QC',              1100.00,  TRUE),
  ('Xi Office Hub',            'Patricia Mendoza',  '(02) 8100-0014', '18 Pasay Rd, Dasmarinas Vill, Makati',   670.00,  TRUE),
  ('Omicron Traders',          'Renato Aguilar',    '(02) 8100-0015', '6 Libertad St, Mandaluyong',              220.00,  TRUE),
  ('Pi Paper & Ink',           'Gloria Torres',     '(02) 8100-0016', '90 T. Alonzo St, Sta. Cruz, Manila',     3500.50,  TRUE),
  ('Rho Consulting Group',     'Andres Flores',     '(02) 8100-0017', '12 V. Luna Rd, Diliman, QC',              800.00,  TRUE),
  ('Sigma Supply Chain',       'Natividad Reyes',   '(02) 8100-0018', '55 South Ave, Novaliches, QC',            150.00,  TRUE),
  ('Tau Print Solutions',      'Maximino Castillo', '(02) 8100-0019', '3 Zobel Roxas, Alabang, Muntinlupa',       60.00,  TRUE),
  ('Upsilon Furniture',        'Carmelita Santos',  '(02) 8100-0020', '101 Mt. Apo St, Project 8, QC',          2250.00,  TRUE),
  ('Phi Digital Works',        'Benjamin Cruz',     '(02) 8100-0021', '78 E. Rodriguez Sr, Cubao, QC',           385.75,  TRUE),
  ('Chi Paper Depot',          'Rowena Pascual',    '(02) 8100-0022', '9 Welcome Rotonda, QC',                   905.00,  TRUE),
  ('Psi Office Systems',       'Ramon Gutierrez',   '(02) 8100-0023', '22 Congressional Ave, QC',                  0.00,  TRUE),
  ('Omega Enterprise',         'Felicitas Navarro', '(02) 8100-0024', '14 McArthur Hi-way, Angeles City',       4100.00,  TRUE),
  ('Alpha Ink & Toner',        'Leonardo Domingo',  '(02) 8100-0025', '33 Rizal Ave, Caloocan City',             725.00,  TRUE),
  ('BrightStar Supplies',      'Milagros Rivera',   '(02) 8100-0026', '5 Gen. Luna St, Malolos, Bulacan',        310.50,  TRUE),
  ('ClearVision Corp',         'Vicente Hernandez', '(02) 8100-0027', '200 MacArthur Fwy, Valenzuela',          1650.00,  TRUE),
  ('DeskPro Trading',          'Josefina Morales',  '(02) 8100-0028', '18 National Rd, Cainta, Rizal',           480.00,  TRUE),
  ('EcoWrite Solutions',       'Arnoldo Jimenez',   '(02) 8100-0029', '6 Magsaysay Blvd, Sta. Mesa, Manila',     95.00,  TRUE),
  ('FilPaper Industries',      'Consolacion Perez', '(02) 8100-0030', '90 Governors Dr, Imus, Cavite',         1980.00,  FALSE); -- closed account example

-- ============================================================
-- VIEW: Customer List for Reports Tab (FS-Sec1, QD-Sec9 pattern)
-- Excludes nothing sensitive here, but follows the RBAC view pattern
-- ============================================================
CREATE OR REPLACE VIEW customer_list_view AS
SELECT
    customer_number,
    company_name,
    contact_name,
    phone_number,
    address,
    current_balance,
    is_active,
    CASE
        WHEN current_balance = 0     THEN 'Clear'
        WHEN current_balance < 500   THEN 'Low'
        WHEN current_balance < 2000  THEN 'Medium'
        ELSE 'High'
    END AS balance_tier
FROM customers
ORDER BY company_name;

-- ============================================================
-- USEFUL QUERIES (matching the QD-Sec and FS-Sec specs)
-- ============================================================

-- QD pattern: Get all active customers with outstanding balances
-- Used by: Tab 2 Customers list, Tab 6 Customer List Report
SELECT customer_number, company_name, contact_name, phone_number, current_balance
FROM customers
WHERE is_active = TRUE
ORDER BY current_balance DESC;

-- FS-Sec5: Modify customer profile (UPDATE example)
-- UPDATE customers SET contact_name = 'New Name', phone_number = '(02) 8100-9999'
-- WHERE customer_number = 1;

-- FS-Sec6 pattern: Flag customers with balance above threshold (warning pop-up logic)
-- SELECT company_name, current_balance FROM customers
-- WHERE current_balance > 3000 AND is_active = TRUE;

-- Point 1: Track payments — after logging a payment, reduce balance
-- UPDATE customers SET current_balance = current_balance - [amount_paid]
-- WHERE customer_number = [id];

-- Customer data retention rule: NEVER DELETE, only deactivate
-- UPDATE customers SET is_active = FALSE WHERE customer_number = [id];