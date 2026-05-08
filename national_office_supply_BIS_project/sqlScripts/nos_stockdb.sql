-- ============================================================
-- National Office Supplies BIS
-- MODULE: Stock & Inventory (Stock Ordering)
-- Based on: stock_ordering.py requirements | QD-Sec6, 13
-- ============================================================

-- 1. TABLE DEFINITIONS

-- TABLE: Suppliers (Stores vendor contact info)
CREATE TABLE IF NOT EXISTS supplier (
    supplier_id    SERIAL          PRIMARY KEY,
    supplier_name  VARCHAR(100)    NOT NULL,
    phone          VARCHAR(20)
);

-- TABLE: Parts (Inventory items and reorder triggers)
CREATE TABLE IF NOT EXISTS part (
    part_no          VARCHAR(20)     PRIMARY KEY,
    description      VARCHAR(255)    NOT NULL,
    count_in_stock   INTEGER         NOT NULL DEFAULT 0,
    trigger_amount   INTEGER         NOT NULL DEFAULT 10
);

-- TABLE: Supplier_Part (Price linking table - satisfy unit_cost requirement)
CREATE TABLE IF NOT EXISTS supplier_part (
    supplier_id    INTEGER         REFERENCES supplier(supplier_id),
    part_no        VARCHAR(20)     REFERENCES part(part_no),
    unit_cost      NUMERIC(10,2)   NOT NULL,
    PRIMARY KEY (supplier_id, part_no)
);

-- TABLE: Purchase Order Lines (Tracks order status for the report)
CREATE TABLE IF NOT EXISTS purchase_order_line (
    po_line_id     SERIAL          PRIMARY KEY,
    part_no        VARCHAR(20)     REFERENCES part(part_no),
    status         VARCHAR(20)     CHECK (status IN ('pending', 'confirmed', 'delivered'))
);

-- 2. SEED DATA (30 records for the Stock Ordering Report)

-- Insert Suppliers
INSERT INTO supplier (supplier_name, phone) VALUES
  ('Ace Supplies PH',        '02-8234-5678'),
  ('Metro Stationery',       '02-8345-6789'),
  ('Prime Paper Goods',      '02-8567-2233'),
  ('OfficeHub Manila',       '02-8789-4455'),
  ('PaperLine Trading',      '02-8890-5566'),
  ('Rapid Office Solutions', '02-9012-7788'),
  ('CityWide Office Supply', '02-9678-4344'),
  ('NorthStar Stationery',   '02-9901-7677'),
  ('SouthGate Office Mart',  '02-9012-8788');

-- Insert 30 Parts (Includes items from your provided image)
INSERT INTO part (part_no, description, count_in_stock, trigger_amount) VALUES
  ('P-1002', 'Ballpen Blue (box/12)',    3,  10),
  ('P-1003', 'Correction Fluid',         0,   5),
  ('P-1005', 'Scotch Tape 1 inch',       1,   8),
  ('P-1007', 'Paper Clips (100pcs)',     0,   5),
  ('P-1008', 'Folder Long (Plastic)',    7,  15),
  ('P-1010', 'Pencil #2 (box/12)',       2,  10),
  ('P-1015', 'Scissors Office Medium',   4,   8),
  ('P-1016', 'Correction Tape',          1,  10),
  ('P-1019', 'Index Cards (100pcs)',     3,  10),
  ('P-1020', 'Staple Wire No.35',        0,   5),
  ('P-1021', 'Expanding Envelope',       12, 20),
  ('P-1022', 'Whiteboard Marker Black',  5,  12),
  ('P-1023', 'Calculator Basic Model',   2,   5),
  ('P-1024', 'Paper Cutter Small',       3,   5),
  ('P-1025', 'Glue Stick 40g',           0,  10),
  ('P-1026', 'Ink Refill Black',         1,   5),
  ('P-1027', 'Binder Clips 25mm',        15, 25),
  ('P-1028', 'Correction Pen Metal Tip', 0,   5),
  ('P-1029', 'Stamp Pad Ink Blue',       6,  10),
  ('P-1030', 'Clear Book A4',            4,  12),
  ('P-1031', 'Permanent Marker Fine',    9,  15),
  ('P-1032', 'Ruler Plastic 12in',       2,  20),
  ('P-1033', 'Puncher Heavy Duty',       1,   5),
  ('P-1034', 'Stapler Standard',         3,  10),
  ('P-1035', 'Waste Basket Mesh',        0,   5),
  ('P-1036', 'Paper Shredder Oil',       2,   8),
  ('P-1037', 'Carbon Paper Blue',        10, 20),
  ('P-1038', 'Desk Organizer Wood',      1,   5),
  ('P-1039', 'Thermal Paper Rolls',      5,  25),
  ('P-1040', 'Double Sided Tape',        3,  10);

-- Link Suppliers & Costs (Pricing logic)
INSERT INTO supplier_part (supplier_id, part_no, unit_cost) VALUES
  (1, 'P-1002', 1.00), (2, 'P-1003', 1.10), (3, 'P-1005', 0.40),
  (4, 'P-1007', 0.20), (5, 'P-1008', 0.18), (6, 'P-1010', 0.70),
  (7, 'P-1015', 1.90), (7, 'P-1016', 0.95), (8, 'P-1019', 0.90),
  (9, 'P-1020', 0.45), (1, 'P-1021', 15.50), (2, 'P-1022', 12.00),
  (3, 'P-1023', 4.80), (4, 'P-1024', 5.90), (5, 'P-1025', 0.85),
  (6, 'P-1026', 1.80), (7, 'P-1027', 0.65), (8, 'P-1028', 0.70),
  (9, 'P-1029', 1.15), (1, 'P-1030', 2.50), (2, 'P-1031', 1.40),
  (3, 'P-1032', 0.50), (4, 'P-1033', 18.00), (5, 'P-1034', 8.50),
  (6, 'P-1035', 6.00), (7, 'P-1036', 3.20), (8, 'P-1037', 0.95),
  (9, 'P-1038', 25.00), (1, 'P-1039', 1.25), (2, 'P-1040', 0.80);

-- Mock Initial Purchase Orders (Status tracking)
INSERT INTO purchase_order_line (part_no, status) VALUES
  ('P-1002', 'pending'), ('P-1003', 'pending'), ('P-1005', 'pending'),
  ('P-1007', 'pending'), ('P-1008', 'pending'), ('P-1015', 'pending'),
  ('P-1016', 'pending'), ('P-1019', 'pending'), ('P-1020', 'pending'),
  ('P-1028', 'pending');