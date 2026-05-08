-- Parts / Inventory table
CREATE TABLE IF NOT EXISTS part (
    part_no          VARCHAR(20)     PRIMARY KEY,
    description      VARCHAR(200)    NOT NULL,
    sell_price       NUMERIC(10,2)   NOT NULL DEFAULT 0.00,
    count_in_stock   INTEGER         NOT NULL DEFAULT 0,
    trigger_amount   INTEGER         NOT NULL DEFAULT 5
);

-- Supplier table
CREATE TABLE IF NOT EXISTS supplier (
    supplier_id      SERIAL          PRIMARY KEY,
    supplier_name    VARCHAR(100)    NOT NULL,
    phone            VARCHAR(30)
);

-- Supplier-Part cost table (which supplier sells which part at what cost)
CREATE TABLE IF NOT EXISTS supplier_part (
    supplier_id      INTEGER         REFERENCES supplier(supplier_id),
    part_no          VARCHAR(20)     REFERENCES part(part_no),
    unit_cost        NUMERIC(10,2)   NOT NULL,
    PRIMARY KEY (supplier_id, part_no)
);

-- Purchase order line (used for "on order" count in inventory view)
CREATE TABLE IF NOT EXISTS purchase_order_line (
    pol_id           SERIAL          PRIMARY KEY,
    part_no          VARCHAR(20)     REFERENCES part(part_no),
    quantity         INTEGER         NOT NULL DEFAULT 1,
    status           VARCHAR(20)     NOT NULL DEFAULT 'pending'
);

-- Invoice table
CREATE TABLE IF NOT EXISTS invoice (
    invoice_no     SERIAL PRIMARY KEY,
    is_shipped     BOOLEAN NOT NULL DEFAULT FALSE
);

-- Invoice line items
CREATE TABLE IF NOT EXISTS invoice_line (
    invoice_line_id SERIAL PRIMARY KEY,
    invoice_no      INTEGER REFERENCES invoice(invoice_no),
    part_no         VARCHAR(20) REFERENCES part(part_no),
    quantity        INTEGER NOT NULL DEFAULT 1
);

CREATE OR REPLACE VIEW qd3_low_stock AS
SELECT *
FROM part
WHERE count_in_stock <= trigger_amount;

CREATE OR REPLACE VIEW qd6_low_stock_suppliers AS
SELECT
    p.part_no,
    s.supplier_name,
    sp.unit_cost,
    s.phone
FROM part p
JOIN supplier_part sp ON sp.part_no = p.part_no
JOIN supplier s ON s.supplier_id = sp.supplier_id
WHERE p.count_in_stock <= p.trigger_amount;

-- Seed parts (matches your sample data)
INSERT INTO part (part_no, description, sell_price, count_in_stock, trigger_amount) VALUES
('P-1001', 'Bond Paper (500 sheets)',        3.50, 120, 50),
('P-1002', 'Ballpen Blue (box/12)',          1.20,   3, 10),
('P-1003', 'Correction Fluid',               0.95,   0,  5),
('P-1004', 'Stapler Heavy Duty',             8.75,  18, 10),
('P-1005', 'Scotch Tape 1 inch',             0.60,   1,  8),
('P-1006', 'Pad Paper Intermediate',         2.10,  45, 20),
('P-1007', 'Paper Clips (100pcs)',           0.45,   0,  5),
('P-1008', 'Folder Long (Plastic)',          0.30,   7, 15),
('P-1009', 'Whiteboard Marker Set (4)',      3.20,  22, 10),
('P-1010', 'Pencil #2 (box/12)',             1.05,   2, 10),

('P-1011', 'Envelope Brown Long',            0.25,  80, 30),
('P-1012', 'Envelope White A4',              0.28,  10, 20),
('P-1013', 'Glue Stick Large',               1.10,   6, 12),
('P-1014', 'Ruler 12 inch',                  0.50,  25, 10),
('P-1015', 'Scissors Office Medium',         2.75,   4,  8),
('P-1016', 'Correction Tape',                1.30,   1, 10),
('P-1017', 'Marker Permanent Black',         1.80,  15, 10),
('P-1018', 'Notebook Spiral 80 pages',       2.40,   9, 15),
('P-1019', 'Index Cards (100pcs)',           1.60,   3, 10),
('P-1020', 'Staple Wire No.35',              0.90,   0,  5),

('P-1021', 'Push Pins Color (50pcs)',        0.70,  18, 10),
('P-1022', 'Desk Organizer Tray',            5.50,   6,  5),
('P-1023', 'Calculator Basic Model',         6.20,   2,  5),
('P-1024', 'Paper Cutter Small',             7.80,   3,  5),
('P-1025', 'Clipboard A4 Plastic',           1.25,  12, 10),
('P-1026', 'Ink Refill Black',               2.90,   1,  5),
('P-1027', 'Eraser Soft White',              0.20,  60, 20),
('P-1028', 'Correction Pen Metal Tip',       1.15,   0,  5),
('P-1029', 'Sticky Notes (3x3)',            1.75,   8, 15),
('P-1030', 'Paper Fastener Metal',          0.35,  40, 20)
ON CONFLICT (part_no) DO NOTHING;

-- Seed suppliers
INSERT INTO supplier (supplier_name, phone) VALUES
('Lim Office Depot',        '02-8123-4567'),
('Ace Supplies PH',         '02-8234-5678'),
('Metro Stationery',        '02-8345-6789'),

('Sunrise Office Mart',     '02-8456-1122'),
('Prime Paper Goods',       '02-8567-2233'),
('StationPro Supplies',     '02-8678-3344'),
('OfficeHub Manila',        '02-8789-4455'),
('PaperLine Trading',       '02-8890-5566'),
('Golden Pen Enterprises',  '02-8901-6677'),
('Rapid Office Solutions',  '02-9012-7788'),

('BlueWave Stationers',     '02-9123-8899'),
('Evergreen Supplies Co',   '02-9234-9900'),
('SmartOffice Depot',       '02-9345-1011'),
('ValueStation PH',         '02-9456-2122'),
('MetroPaper Trading',      '02-9567-3233'),

('CityWide Office Supply',  '02-9678-4344'),
('Ink & Paper Hub',         '02-9789-5455'),
('PrimePoint Supplies',     '02-9890-6566'),
('NorthStar Stationery',    '02-9901-7677'),
('SouthGate Office Mart',   '02-9012-8788'),

('EasyOffice PH',           '02-9123-9898'),
('PaperCraft Supplies',     '02-9234-0909'),
('SupplyMax Trading',       '02-9345-1112'),
('OfficeLand Depot',        '02-9456-1213'),
('MegaStation Manila',      '02-9567-1314'),

('BrightOffice Supplies',   '02-9678-1415'),
('FastTrack Stationery',    '02-9789-1516'),
('ProPaper Solutions',      '02-9890-1617'),
('UrbanOffice Mart',        '02-9901-1718'),
('Elite Supplies Center',   '02-9012-1819')
ON CONFLICT DO NOTHING;

-- Seed supplier-part costs
-- =========================================================
-- Populate supplier_part for ALL 30 parts
-- =========================================================

INSERT INTO supplier_part (supplier_id, part_no, unit_cost)
SELECT s.supplier_id, v.part_no, v.unit_cost
FROM (
    VALUES
    ('Lim Office Depot',        'P-1001', 0.90),
    ('Ace Supplies PH',         'P-1002', 1.00),
    ('Metro Stationery',        'P-1003', 1.10),
    ('Sunrise Office Mart',     'P-1004', 6.50),
    ('Prime Paper Goods',       'P-1005', 0.40),
    ('StationPro Supplies',     'P-1006', 1.60),
    ('OfficeHub Manila',        'P-1007', 0.20),
    ('PaperLine Trading',       'P-1008', 0.18),
    ('Golden Pen Enterprises',  'P-1009', 2.10),
    ('Rapid Office Solutions',  'P-1010', 0.70),

    ('BlueWave Stationers',     'P-1011', 0.12),
    ('Evergreen Supplies Co',   'P-1012', 0.15),
    ('SmartOffice Depot',       'P-1013', 0.75),
    ('ValueStation PH',         'P-1014', 0.25),
    ('MetroPaper Trading',      'P-1015', 1.90),
    ('CityWide Office Supply',  'P-1016', 0.95),
    ('Ink & Paper Hub',         'P-1017', 1.10),
    ('PrimePoint Supplies',     'P-1018', 1.75),
    ('NorthStar Stationery',    'P-1019', 0.90),
    ('SouthGate Office Mart',   'P-1020', 0.45),

    ('EasyOffice PH',           'P-1021', 0.35),
    ('PaperCraft Supplies',     'P-1022', 3.90),
    ('SupplyMax Trading',       'P-1023', 4.80),
    ('OfficeLand Depot',        'P-1024', 5.90),
    ('MegaStation Manila',      'P-1025', 0.70),
    ('BrightOffice Supplies',   'P-1026', 1.80),
    ('FastTrack Stationery',    'P-1027', 0.08),
    ('ProPaper Solutions',      'P-1028', 0.70),
    ('UrbanOffice Mart',        'P-1029', 1.00),
    ('Elite Supplies Center',   'P-1030', 0.15)
) AS v(supplier_name, part_no, unit_cost)
JOIN supplier s ON s.supplier_name = v.supplier_name
JOIN part p     ON p.part_no = v.part_no
ON CONFLICT (supplier_id, part_no) DO NOTHING;


INSERT INTO purchase_order_line (part_no, quantity, status)
VALUES
('P-1001', 50, 'received'),
('P-1002', 100, 'pending'),
('P-1003', 75, 'pending'),
('P-1004', 20, 'received'),
('P-1005', 60, 'pending'),
('P-1006', 40, 'received'),
('P-1007', 120, 'pending'),
('P-1008', 90, 'pending'),
('P-1009', 30, 'received'),
('P-1010', 80, 'pending'),

('P-1011', 150, 'received'),
('P-1012', 110, 'pending'),
('P-1013', 45, 'pending'),
('P-1014', 35, 'received'),
('P-1015', 25, 'pending'),
('P-1016', 70, 'pending'),
('P-1017', 40, 'received'),
('P-1018', 95, 'pending'),
('P-1019', 85, 'pending'),
('P-1020', 130, 'pending'),

('P-1021', 50, 'received'),
('P-1022', 15, 'pending'),
('P-1023', 10, 'pending'),
('P-1024', 12, 'pending'),
('P-1025', 40, 'received'),
('P-1026', 30, 'pending'),
('P-1027', 200, 'received'),
('P-1028', 65, 'pending'),
('P-1029', 55, 'pending'),
('P-1030', 100, 'received');

INSERT INTO invoice (is_shipped)
VALUES
(FALSE),
(TRUE),
(FALSE),
(TRUE),
(FALSE),
(TRUE),
(FALSE),
(TRUE),
(FALSE),
(TRUE),

(FALSE),
(TRUE),
(FALSE),
(TRUE),
(FALSE),
(TRUE),
(FALSE),
(TRUE),
(FALSE),
(TRUE),

(FALSE),
(TRUE),
(FALSE),
(TRUE),
(FALSE),
(TRUE),
(FALSE),
(TRUE),
(FALSE),
(TRUE);

INSERT INTO invoice_line (invoice_no, part_no, quantity)
VALUES
(1,  'P-1001', 5),
(2,  'P-1002', 3),
(3,  'P-1003', 7),
(4,  'P-1004', 2),
(5,  'P-1005', 4),
(6,  'P-1006', 6),
(7,  'P-1007', 8),
(8,  'P-1008', 3),
(9,  'P-1009', 2),
(10, 'P-1010', 5),

(11, 'P-1011', 9),
(12, 'P-1012', 4),
(13, 'P-1013', 6),
(14, 'P-1014', 3),
(15, 'P-1015', 2),
(16, 'P-1016', 7),
(17, 'P-1017', 5),
(18, 'P-1018', 8),
(19, 'P-1019', 4),
(20, 'P-1020', 10),

(21, 'P-1021', 3),
(22, 'P-1022', 1),
(23, 'P-1023', 2),
(24, 'P-1024', 1),
(25, 'P-1025', 4),
(26, 'P-1026', 5),
(27, 'P-1027', 6),
(28, 'P-1028', 3),
(29, 'P-1029', 7),
(30, 'P-1030', 8);
SELECT * FROM part;
SELECT * FROM supplier;

