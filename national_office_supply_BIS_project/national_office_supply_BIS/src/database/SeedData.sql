-- ============================================================
--  National Office Supplies — Seed Data
--  Designed to satisfy ALL QD-Sec and FS-Sec requirements
-- ============================================================

-- Reset sequences before inserting with explicit IDs
SELECT setval(pg_get_serial_sequence('customers','customer_number'), 1, false);
SELECT setval(pg_get_serial_sequence('employees','employee_number'), 1, false);
SELECT setval(pg_get_serial_sequence('suppliers','supplier_id'), 1, false);
SELECT setval(pg_get_serial_sequence('parts','part_number'), 1, false);
SELECT setval(pg_get_serial_sequence('invoices','invoice_id'), 1, false);
SELECT setval(pg_get_serial_sequence('timecards','timecard_id'), 1, false);
SELECT setval(pg_get_serial_sequence('purchase_orders','po_number'), 1, false);
SELECT setval(pg_get_serial_sequence('customer_payments','payment_id'), 1, false);
SELECT setval(pg_get_serial_sequence('employee_payments','payment_id'), 1, false);

-- ============================================================
--  TABLE 1: CUSTOMERS (40 records)
--  Mix of active/inactive, various balances
--  Satisfies: Point 1, Point 15, FS-Sec4, FS-Sec5
-- ============================================================
INSERT INTO customers (customer_number, customer_name, company_name, phone_number, address, current_balance, is_active)
VALUES
(1,  'Maria Santos',      'Apex Trading Co.',        '+63-2-8100-0001', '101 Katipunan Ave, Quezon City',          12500.00, TRUE),
(2,  'Jose Reyes',        'BrightPath Solutions',     '+63-2-8100-0002', '22 Shaw Blvd, Mandaluyong City',          48320.75, TRUE),
(3,  'Ana Cruz',          'CoreLink Systems',         '+63-2-8100-0003', '55 Ayala Ave, Makati City',                3200.50, TRUE),
(4,  'Pedro Lim',         'DawnStar Enterprises',     '+63-2-8100-0004', '88 EDSA, Cubao, Quezon City',             91450.00, TRUE),
(5,  'Luisa Garcia',      'EastBay Distributors',     '+63-2-8100-0005', '14 Ortigas Ave, Pasig City',               7800.25, TRUE),
(6,  'Carlos Dela Cruz',  'FarView Holdings',         '+63-2-8100-0006', '36 Taft Ave, Manila',                     26100.00, TRUE),
(7,  'Rosa Navarro',      'GlobalMart Inc.',          '+63-2-8100-0007', '79 Rizal Ave, Caloocan City',             54000.00, TRUE),
(8,  'Juan Flores',       'HighPoint Ventures',       '+63-2-8100-0008', '12 Commonwealth Ave, Quezon City',        18750.80, TRUE),
(9,  'Elena Mendoza',     'IronClad Corp.',           '+63-2-8100-0009', '90 Kamias Rd, Quezon City',                    0.00, TRUE),
(10, 'Ramon Torres',      'JetStream Trading',        '+63-2-8100-0010', '45 Boni Ave, Mandaluyong City',           33600.00, TRUE),
(11, 'Carmen Bautista',   'KeyStone Supplies',        '+63-2-8100-0011', '17 España Blvd, Manila',                  72400.55, TRUE),
(12, 'Andres Villanueva', 'LightWave Enterprises',    '+63-2-8100-0012', '60 Aurora Blvd, Quezon City',              9120.00, TRUE),
(13, 'Patricia Castillo', 'MegaSource Corp.',         '+63-2-8100-0013', '33 Mindanao Ave, Quezon City',            41800.25, TRUE),
(14, 'Ricardo Moreno',    'NextLevel Solutions',      '+63-2-8100-0014', '7 Libis, Quezon City',                    15600.00, TRUE),
(15, 'Cynthia Ramos',     'OceanGate Trading',        '+63-2-8100-0015', '25 C5 Road, Taguig City',                 28900.75, TRUE),
(16, 'Eduardo Vargas',    'PrimeStar Holdings',       '+63-2-8100-0016', '11 Eastwood City, Quezon City',                0.00, TRUE),
(17, 'Maricel Aquino',    'QuickServe Inc.',          '+63-2-8100-0017', '53 Pioneer St, Mandaluyong City',         87500.00, TRUE),
(18, 'Fernando Ong',      'RapidLink Systems',        '+63-2-8100-0018', '19 White Plains, Quezon City',            44200.50, TRUE),
(19, 'Susana Evangelista','SkyHigh Ventures',         '+63-2-8100-0019', '66 Congressional Ave, Quezon City',        5300.00, TRUE),
(20, 'Alfredo Sy',        'TopGear Distributors',     '+63-2-8100-0020', '38 Visayas Ave, Quezon City',             31700.00, TRUE),
(21, 'Marites Chua',      'UniStar Enterprises',      '+63-2-8100-0021', '72 Morayta St, Manila',                   16800.00, TRUE),
(22, 'Bernardo Ko',       'ValuePoint Corp.',         '+63-2-8100-0022', '28 Timog Ave, Quezon City',               63400.25, TRUE),
(23, 'Lourdes Tan',       'WestSide Trading',         '+63-2-8100-0023', '84 Magsaysay Blvd, Manila',               22100.00, TRUE),
(24, 'Arturo Dela Torre', 'XcelTech Solutions',       '+63-2-8100-0024', '10 Don Antonio, Quezon City',             98750.00, TRUE),
(25, 'Remedios Salcedo',  'YieldMax Holdings',        '+63-2-8100-0025', '47 Project 8, Quezon City',                8400.75, TRUE),
(26, 'Ernesto Pascual',   'ZenithPrime Inc.',         '+63-2-8100-0026', '31 Teacher''s Village, Quezon City',      55200.00, TRUE),
(27, 'Gloria Reyes',      'AlphaBuild Supplies',      '+63-2-8100-0027', '63 Fairview, Quezon City',                19300.50, TRUE),
(28, 'Danilo Santos',     'BetaForce Corp.',          '+63-2-8100-0028', '85 Diliman, Quezon City',                  4100.00, TRUE),
(29, 'Teresita Gomez',    'ClearPath Enterprises',    '+63-2-8100-0029', '20 UP Village, Quezon City',              37600.00, TRUE),
(30, 'Vicente Abad',      'DeltaCore Trading',        '+63-2-8100-0030', '58 Holy Spirit, Quezon City',             71200.75, TRUE),
-- Inactive customers (to test is_active filter in FS-Sec5)
(31, 'Isadora Macapagal', 'OldCo Trading',            '+63-2-8100-0031', '9 Retiro St, Manila',                         0.00, FALSE),
(32, 'Leandro Banaag',    'ClosedDown Inc.',          '+63-2-8100-0032', '5 Quiapo, Manila',                        12000.00, FALSE),
(33, 'Milagros Enriquez', 'Defunct Supplies',         '+63-2-8100-0033', '44 Sta. Mesa, Manila',                     3400.00, FALSE),
(34, 'Porfirio dela Vega','SunSet Trading',           '+63-2-8100-0034', '77 Tondo, Manila',                         9800.00, FALSE),
(35, 'Herminia Valdez',   'FinalStar Corp.',          '+63-2-8100-0035', '13 Binondo, Manila',                       6200.50, FALSE),
-- Active with zero balance (to test balance tracking)
(36, 'Julio Reyes',       'ZeroBalance Co.',          '+63-2-8100-0036', '2 Mandaluyong, Metro Manila',                  0.00, TRUE),
(37, 'Amelia Cruz',       'ClearAccount Trading',     '+63-2-8100-0037', '16 Pasig, Metro Manila',                       0.00, TRUE),
(38, 'Nestor Villanueva', 'FreshStart Ventures',      '+63-2-8100-0038', '48 Parañaque, Metro Manila',              14600.00, TRUE),
(39, 'Felicidad Abad',    'NewBegin Supplies',        '+63-2-8100-0039', '71 Las Piñas, Metro Manila',              26300.00, TRUE),
(40, 'Rodrigo Castillo',  'OpenBook Corp.',           '+63-2-8100-0040', '39 Muntinlupa, Metro Manila',             51800.00, TRUE)
ON CONFLICT DO NOTHING;

-- ============================================================
--  TABLE 2: EMPLOYEES (45 records)
--  3 Managers, 15 Sales Reps, 27 Hourly
--  Satisfies: Points 6,7,8,16,17, FS-Sec1, QD-Sec1, QD-Sec2, QD-Sec12
-- ============================================================
INSERT INTO employees (employee_number, employee_name, position, ssn, employee_address, username, password_hash, is_locked, is_active, hourly_wage, ytdsales, commission_rate)
VALUES
-- MANAGERS (position code 01) — 3 records
(1,  'Maria Santos-Reyes',   'Manager',   '101-11-1001', '123 Katipunan Ave, QC',          'msantos',     '$2b$12$mgrhash001', FALSE, TRUE,   NULL,      0.00,   0.05),
(2,  'Jonathan Dela Cruz',   'Manager',   '101-11-1002', '45 Commonwealth Ave, QC',         'jdelacruz',   '$2b$12$mgrhash002', FALSE, TRUE,   NULL,      0.00,   0.05),
(3,  'Angela Reyes-Lim',     'Manager',   '101-11-1003', '88 Aurora Blvd, QC',              'angelim',     '$2b$12$mgrhash003', FALSE, TRUE,   NULL,      0.00,   0.05),

-- SALES REPS (position code 02) — 15 records
-- QD-Sec12: Employees 4,5,6,7,8 will have >10 invoices for week of Aug 9
(4,  'Kevin Lim',            'Sales Rep', '202-22-2001', '14 Eastwood Ave, QC',             'klim',        '$2b$12$srphash001', FALSE, TRUE,   NULL, 125000.50, 0.05),
(5,  'Sophia Tan',           'Sales Rep', '202-22-2002', '32 Timog Ave, QC',                'stan',        '$2b$12$srphash002', FALSE, TRUE,   NULL,  98250.75, 0.05),
(6,  'Miguel Garcia',        'Sales Rep', '202-22-2003', '77 Tomas Morato, QC',             'mgarcia',     '$2b$12$srphash003', FALSE, TRUE,   NULL, 156430.20, 0.05),
(7,  'Patricia Lopez',       'Sales Rep', '202-22-2004', '56 Visayas Ave, QC',              'plopez',      '$2b$12$srphash004', FALSE, TRUE,   NULL,  45600.00, 0.05),
(8,  'Daniel Flores',        'Sales Rep', '202-22-2005', '21 Maginhawa St, QC',             'dflores',     '$2b$12$srphash005', FALSE, TRUE,   NULL, 205300.15, 0.05),
(9,  'Camille Ramos',        'Sales Rep', '202-22-2006', '90 Congressional, QC',            'cramos',      '$2b$12$srphash006', FALSE, TRUE,   NULL,  78320.90, 0.05),
(10, 'Joshua Mendoza',       'Sales Rep', '202-22-2007', '10 Banawe St, QC',                'jmendoza',    '$2b$12$srphash007', FALSE, TRUE,   NULL, 132000.00, 0.05),
(11, 'Ella Bautista',        'Sales Rep', '202-22-2008', '5 Scout Area, QC',                'ebautista',   '$2b$12$srphash008', FALSE, TRUE,   NULL,  68900.40, 0.05),
(12, 'Nathan Velasco',       'Sales Rep', '202-22-2009', '101 Fairview Ave, QC',            'nvelasco',    '$2b$12$srphash009', FALSE, TRUE,   NULL,  91000.00, 0.05),
(13, 'Isabelle Navarro',     'Sales Rep', '202-22-2010', '67 Mindanao Ave, QC',             'inavarro',    '$2b$12$srphash010', FALSE, TRUE,   NULL, 149500.99, 0.05),
(14, 'Adrian Perez',         'Sales Rep', '202-22-2011', '44 Roosevelt Ave, QC',            'aperez',      '$2b$12$srphash011', FALSE, TRUE,   NULL,  34000.00, 0.05),
(15, 'Claire Dizon',         'Sales Rep', '202-22-2012', '11 Kamias Rd, QC',                'cdizon',      '$2b$12$srphash012', FALSE, TRUE,   NULL, 175250.60, 0.05),
(16, 'Marco Del Rosario',    'Sales Rep', '202-22-2013', '18 Green Meadows, QC',            'mdelrosario', '$2b$12$srphash013', FALSE, TRUE,   NULL, 112450.80, 0.05),
(17, 'Bianca Sy',            'Sales Rep', '202-22-2014', '42 White Plains, QC',             'bsy',         '$2b$12$srphash014', FALSE, TRUE,   NULL,  87400.25, 0.05),
(18, 'Rafael Gutierrez',     'Sales Rep', '202-22-2015', '77 San Juan, Metro Manila',       'rgutierrez',  '$2b$12$srphash015', FALSE, TRUE,   NULL, 221340.10, 0.05),

-- HOURLY STAFF (position code 03) — 17 records
-- QD-Sec1: employees 19–35 will be missing timecards for Aug 9 week (some intentionally)
(19, 'Mark Aquino',          'Hourly',    '303-33-3001', '12 Cubao, QC',                    'maquino',     '$2b$12$hryhash001', FALSE, TRUE,  120.00,  0.00, 0.05),
(20, 'Liza Moreno',          'Hourly',    '303-33-3002', '9 Project 6, QC',                 'lmoreno',     '$2b$12$hryhash002', FALSE, TRUE,  115.50,  0.00, 0.05),
(21, 'Carlo Vega',           'Hourly',    '303-33-3003', '88 Novaliches, QC',               'cvega',       '$2b$12$hryhash003', FALSE, TRUE,  130.25,  0.00, 0.05),
(22, 'Janine Torres',        'Hourly',    '303-33-3004', '22 Tandang Sora, QC',             'jtorres',     '$2b$12$hryhash004', FALSE, TRUE,  125.00,  0.00, 0.05),
(23, 'Paolo Diaz',           'Hourly',    '303-33-3005', '14 Philcoa, QC',                  'pdiaz',       '$2b$12$hryhash005', FALSE, TRUE,  118.75,  0.00, 0.05),
(24, 'Rina Chavez',          'Hourly',    '303-33-3006', '51 Diliman, QC',                  'rchavez',     '$2b$12$hryhash006', FALSE, TRUE,  122.50,  0.00, 0.05),
(25, 'Noel Herrera',         'Hourly',    '303-33-3007', '19 Batasan Hills, QC',            'nherrera',    '$2b$12$hryhash007', FALSE, TRUE,  117.00,  0.00, 0.05),
(26, 'Faith Villanueva',     'Hourly',    '303-33-3008', '73 UP Village, QC',               'fvillanueva', '$2b$12$hryhash008', FALSE, TRUE,  128.00,  0.00, 0.05),
(27, 'Sean Castillo',        'Hourly',    '303-33-3009', '35 Teacher''s Village, QC',       'scastillo',   '$2b$12$hryhash009', FALSE, TRUE,  116.00,  0.00, 0.05),
(28, 'Karla Rivera',         'Hourly',    '303-33-3010', '29 Holy Spirit, QC',              'krivera',     '$2b$12$hryhash010', FALSE, TRUE,  135.00,  0.00, 0.05),
(29, 'Dianne Flores',        'Hourly',    '303-33-3011', '15 Project 8, QC',                'dflores2',    '$2b$12$hryhash011', FALSE, TRUE,  121.50,  0.00, 0.05),
(30, 'Kenneth Ong',          'Hourly',    '303-33-3012', '91 Don Antonio, QC',              'kong',        '$2b$12$hryhash012', FALSE, TRUE,  124.00,  0.00, 0.05),
(31, 'Melissa Chua',         'Hourly',    '303-33-3013', '63 Fairview, QC',                 'mchua',       '$2b$12$hryhash013', FALSE, TRUE,  119.75,  0.00, 0.05),
(32, 'Jerome Valdez',        'Hourly',    '303-33-3014', '44 Marikina Heights, Marikina',   'jvaldez',     '$2b$12$hryhash014', FALSE, TRUE,  126.25,  0.00, 0.05),
(33, 'Patty Evangelista',    'Hourly',    '303-33-3015', '28 Culiat, QC',                   'pevangelista','$2b$12$hryhash015', FALSE, TRUE,  117.50,  0.00, 0.05),
(34, 'Ronald Yu',            'Hourly',    '303-33-3016', '55 Katipunan Ext, QC',            'ryu',         '$2b$12$hryhash016', FALSE, TRUE,  133.00,  0.00, 0.05),
(35, 'Alyssa Navarro',       'Hourly',    '303-33-3017', '72 Pasig Blvd, Pasig',            'anavarro',    '$2b$12$hryhash017', FALSE, TRUE,  122.00,  0.00, 0.05),
-- Additional hourly staff added to allow larger missing-timecard set for Aug 9 test
(36, 'Diego Santos',         'Hourly',    '303-33-3018', '10 San Miguel, QC',               'dsantos',     '$2b$12$hryhash018', FALSE, TRUE,  118.50,  0.00, 0.05),
(37, 'Maya Fernandez',       'Hourly',    '303-33-3019', '27 Banawe St, QC',                'mfernandez',  '$2b$12$hryhash019', FALSE, TRUE,  121.00,  0.00, 0.05),
(38, 'Elias Cruz',           'Hourly',    '303-33-3020', '5 Congressional, QC',             'ecruz',       '$2b$12$hryhash020', FALSE, TRUE,  119.25,  0.00, 0.05),
(39, 'Rosa Lim',             'Hourly',    '303-33-3021', '88 Kamias Rd, QC',                'rlim',        '$2b$12$hryhash021', FALSE, TRUE,  116.75,  0.00, 0.05),
(40, 'Victor Ong',           'Hourly',    '303-33-3022', '14 Don Antonio, QC',              'vong',        '$2b$12$hryhash022', FALSE, TRUE,  123.00,  0.00, 0.05),
(41, 'Grace dela Cruz',      'Hourly',    '303-33-3023', '33 Timog Ave, QC',                'gdelacruz',   '$2b$12$hryhash023', FALSE, TRUE,  120.50,  0.00, 0.05),
(42, 'Hector Ramos',         'Hourly',    '303-33-3024', '51 Fairview Ave, QC',             'hramos',      '$2b$12$hryhash024', FALSE, TRUE,  117.25,  0.00, 0.05),
(43, 'Lani Morales',         'Hourly',    '303-33-3025', '6 Green Meadows, QC',             'lmorales',    '$2b$12$hryhash025', FALSE, TRUE,  122.50,  0.00, 0.05),
(44, 'Cesar Villanueva',     'Hourly',    '303-33-3026', '79 Project 6, QC',                'cvillanueva', '$2b$12$hryhash026', FALSE, TRUE,  125.00,  0.00, 0.05),
(45, 'Nina Torres',          'Hourly',    '303-33-3027', '17 Katipunan Ext, QC',            'ntorres',     '$2b$12$hryhash027', FALSE, TRUE,  118.00,  0.00, 0.05)
ON CONFLICT DO NOTHING;

-- ============================================================
--  TABLE 3: SUPPLIERS (30 records)
--  Diverse vendors — stationery, tech, furniture
--  Satisfies: Point 14, QD-Sec6, QD-Sec7, QD-Sec13
-- ============================================================
INSERT INTO suppliers (supplier_id, company_name, phone_number, address)
VALUES
(1,  'Metro Office Furnishings',   '+63-2-8123-1001', '101 Aurora Blvd, Quezon City'),
(2,  'Prime Workspace Solutions',  '+63-2-8123-1002', '45 Ortigas Ave, Pasig City'),
(3,  'Elite Ergonomic Furniture',  '+63-2-8123-1003', '22 Chino Roces Ave, Makati City'),
(4,  'National Stationery Depot',  '+63-2-8123-1004', '77 España Blvd, Manila'),
(5,  'PaperTrail Office Supplies', '+63-2-8123-1005', '15 Commonwealth Ave, Quezon City'),
(6,  'BlueInk Trading',            '+63-2-8123-1006', '90 Taft Ave, Manila'),
(7,  'SmartTech Distribution',     '+63-2-8123-1007', '11 Gilmore Ave, Quezon City'),
(8,  'NextGen IT Suppliers',       '+63-2-8123-1008', '55 Boni Ave, Mandaluyong City'),
(9,  'Quantum Computer Systems',   '+63-2-8123-1009', '88 EDSA, Cubao, Quezon City'),
(10, 'OfficePro Interiors',        '+63-2-8123-1010', '32 Katipunan Ave, Quezon City'),
(11, 'Vertex Office Essentials',   '+63-2-8123-1011', '17 Shaw Blvd, Pasig City'),
(12, 'Golden Pen Enterprises',     '+63-2-8123-1012', '63 Recto Ave, Manila'),
(13, 'TechHub Electronics Supply', '+63-2-8123-1013', '91 Pioneer St, Mandaluyong City'),
(14, 'ComfortLine Furnitures',     '+63-2-8123-1014', '44 Marcos Highway, Marikina City'),
(15, 'OfficeNest Trading',         '+63-2-8123-1015', '70 Visayas Ave, Quezon City'),
(16, 'Precision Print Supplies',   '+63-2-8123-1016', '12 Morayta St, Manila'),
(17, 'CyberCore Technologies',     '+63-2-8123-1017', '101 Alabang-Zapote Rd, Muntinlupa'),
(18, 'DeskWorks Furniture Co.',    '+63-2-8123-1018', '25 A. Bonifacio Ave, Quezon City'),
(19, 'StaplePoint Distribution',   '+63-2-8123-1019', '84 Rizal Ave, Caloocan City'),
(20, 'Digital Frontier Devices',   '+63-2-8123-1020', '39 Libis, Quezon City'),
(21, 'Summit Office Warehouse',    '+63-2-8123-1021', '18 C5 Road, Taguig City'),
(22, 'InkMasters Supply Corp.',    '+63-2-8123-1022', '59 Pedro Gil St, Manila'),
(23, 'FutureLink Technologies',    '+63-2-8123-1023', '14 Ayala Ave, Makati City'),
(24, 'UrbanSpace Furnishings',     '+63-2-8123-1024', '92 Ortigas Extension, Pasig City'),
(25, 'WriteChoice Stationers',     '+63-2-8123-1025', '36 Magsaysay Blvd, Manila'),
(26, 'NovaTech Office Systems',    '+63-2-8123-1026', '27 Eastwood City, Quezon City'),
(27, 'Axis Business Supplies',     '+63-2-8123-1027', '75 Timog Ave, Quezon City'),
(28, 'Pinnacle Office Solutions',  '+63-2-8123-1028', '66 McArthur Highway, Valenzuela'),
(29, 'CloudPeak Electronics',      '+63-2-8123-1029', '48 Madrigal Ave, Las Piñas City'),
(30, 'Infinity Workspace Trading', '+63-2-8123-1030', '120 Greenhills, San Juan City')
ON CONFLICT DO NOTHING;

-- ============================================================
--  TABLE 4: PARTS (45 records)
--  Mix of normal stock, low stock, zero stock, and on-order
--  Satisfies: Points 5,10,13, QD-Sec3,4,5,11, FS-Sec6
--
--  CRITICAL TEST RECORDS:
--  Part 43: stock=0, on_order=FALSE — will appear in unshipped invoice (QD-Sec5)
--  Part 44: stock=1, on_order=FALSE — will appear in unshipped invoice (QD-Sec5)
--  Part 45: stock=0, on_order=TRUE  — tests QD-Sec4 (already ordered, so NOT in QD-Sec4 results)
--  Parts 30-35: high-ticket low-stock items (printers, copiers)
-- ============================================================
INSERT INTO parts (part_number, description, selling_price, stock_count, trigger_amount, restock_value, on_order)
VALUES
-- Standard stationery (normal stock)
(1,  'Ballpoint Pen - Blue',          15.00,   450,  100,  500, FALSE),
(2,  'Ballpoint Pen - Black',         15.00,   420,  100,  500, FALSE),
(3,  'Gel Pen Set (5 pcs)',           45.00,   180,   50,  200, FALSE),
(4,  'Permanent Marker - Black',      35.00,   120,   40,  150, FALSE),
(5,  'Highlighter Set (4 colors)',    85.00,    90,   25,  100, FALSE),
-- Paper products — PRICE DISPARITY TEST: Part 6 has Supplier A at 185 vs Supplier B at 150
(6,  'Premium Bond Paper A4 80gsm',  350.00,   300,   75,  400, FALSE),
(7,  'Bond Paper Legal 70gsm',       275.00,   220,   50,  300, FALSE),
(8,  'Photo Paper Glossy A4',        450.00,    80,   20,  100, FALSE),
(9,  'Sticky Notes Pack',             65.00,   160,   40,  200, FALSE),
(10, 'Index Cards Pack',              55.00,   140,   35,  150, FALSE),
-- Office tools
(11, 'Stapler Heavy Duty',           320.00,    65,   15,   50, FALSE),
(12, 'Staple Wire Box',               45.00,   250,   60,  300, FALSE),
(13, 'Tape Dispenser',               120.00,    70,   20,   80, FALSE),
(14, 'Scissors Stainless Steel',     150.00,    85,   25,  100, FALSE),
(15, 'Paper Clips Box',               35.00,   200,   50,  250, FALSE),
-- Filing and storage
(16, 'Expanding Folder',             180.00,    95,   20,  120, FALSE),
(17, 'Ring Binder 1-inch',           110.00,   100,   25,  150, FALSE),
(18, 'Document Envelope Brown',       25.00,   500,  100,  600, FALSE),
(19, 'Plastic Storage Box',          350.00,    40,   10,   50, FALSE),
(20, 'Desk Organizer Tray',          280.00,    55,   15,   70, FALSE),
-- Tech peripherals
(21, 'USB Flash Drive 32GB',         450.00,   130,   30,  150, FALSE),
(22, 'Wireless Mouse',               650.00,    75,   20,  100, FALSE),
(23, 'Wireless Keyboard',           1200.00,    45,   10,   60, FALSE),
(24, 'HD Webcam 1080p',             1850.00,    35,   10,   40, FALSE),
(25, 'Noise Cancelling Headset',    3200.00,    25,    5,   30, FALSE),
(26, 'WiFi Router Dual Band',       2800.00,    30,    8,   40, FALSE),
(27, '8-Port Network Switch',       2200.00,    22,    5,   25, FALSE),
(28, 'Ethernet Cable 5m',            180.00,   140,   30,  200, FALSE),
(29, 'Surge Protector',              750.00,    60,   15,   80, FALSE),
-- High-ticket low-stock items (printers, copiers)
(30, 'External Hard Drive 1TB',     4200.00,    18,    5,   20, FALSE),
(31, 'Inkjet Printer Basic',        5500.00,    14,    3,   10, FALSE),
(32, 'Laser Printer Monochrome',   12500.00,    10,    2,    8, FALSE),
(33, 'All-in-One Printer Scanner', 15800.00,     8,    2,    6, FALSE),
(34, 'Color Laser Printer',        24500.00,     5,    1,    4, FALSE),
(35, 'Commercial Copier Machine',  85000.00,     2,    1,    2, FALSE),
-- Furniture
(36, 'Ergonomic Office Chair',      6800.00,    20,    5,   15, FALSE),
(37, 'Executive Office Desk',      14500.00,     8,    2,    6, FALSE),
(38, 'Filing Cabinet 4-Drawer',     9200.00,    12,    3,    8, FALSE),
(39, 'Conference Table Large',     25500.00,     3,    1,    2, FALSE),
(40, 'Bookshelf Wooden',            4800.00,    15,    4,   10, FALSE),
-- Sanitation
(41, 'Alcohol Spray 500ml',         120.00,   180,   40,  200, FALSE),
(42, 'Disinfecting Wipes Pack',     150.00,   140,   35,  150, FALSE),
-- CRITICAL: QD-Sec5 bottleneck parts — zero/one stock, NOT on order, appear in unshipped invoices
(43, 'Premium Color Toner Cartridge', 2800.00,  0,    2,    5, FALSE),
(44, 'A3 Laminating Pouches Pack',    450.00,   1,    5,   20, FALSE),
-- CRITICAL: QD-Sec4 test — stock=0, already on order (should NOT appear in QD-Sec4 results)
(45, 'Thermal Binding Machine',     8500.00,    0,    1,    3, TRUE)
ON CONFLICT DO NOTHING;

-- ============================================================
--  TABLE 5: ITEM_PARTS (110 records)
--  Each part linked to 2-3 suppliers with VARYING costs
--  Satisfies: Point 14, QD-Sec6, QD-Sec13
--
--  PRICE DISPARITY DEMO for Part 6 (Premium Bond Paper A4 80gsm):
--    Supplier 5  (PaperTrail)  → ₱185.00  (cheapest)
--    Supplier 15 (OfficeNest)  → ₱200.00
--    Supplier 21 (Summit)      → ₱220.00  (most expensive)
--  QD-Sec6 and QD-Sec13 must return Supplier 5 as the recommended vendor.
-- ============================================================
INSERT INTO item_parts (part_number, supplier_id, cost) VALUES
-- Part 1: Ballpoint Pen Blue
(1, 4,  8.50), (1, 12, 8.10), (1, 25, 8.75),
-- Part 2: Ballpoint Pen Black
(2, 4,  8.40), (2, 19, 8.20), (2, 27, 8.55),
-- Part 3: Gel Pen Set
(3, 4, 22.00), (3, 12, 21.50), (3, 22, 22.75),
-- Part 4: Permanent Marker
(4, 5, 18.00), (4, 12, 17.80), (4, 25, 18.50),
-- Part 5: Highlighter Set
(5, 4, 55.00), (5, 19, 53.50), (5, 27, 56.25),
-- Part 6: Premium Bond Paper A4 — PRICE DISPARITY TEST
(6, 5, 185.00), (6, 15, 200.00), (6, 21, 220.00),
-- Part 7: Bond Paper Legal
(7, 5, 210.00), (7, 15, 205.00), (7, 28, 212.00),
-- Part 8: Photo Paper
(8, 16, 320.00), (8, 22, 315.00), (8, 25, 325.00),
-- Part 9: Sticky Notes
(9, 5, 28.00), (9, 12, 27.50), (9, 19, 29.00),
-- Part 10: Index Cards
(10, 12, 24.00), (10, 22, 23.50), (10, 25, 24.75),
-- Part 11: Stapler
(11, 11, 190.00), (11, 18, 185.00), (11, 28, 195.00),
-- Part 12: Staple Wire
(12, 5, 20.00), (12, 12, 19.50), (12, 27, 20.75),
-- Part 13: Tape Dispenser
(13, 11, 75.00), (13, 19, 72.00), (13, 28, 76.50),
-- Part 14: Scissors
(14, 11, 95.00), (14, 18, 92.50), (14, 24, 97.00),
-- Part 15: Paper Clips
(15, 5, 12.00), (15, 12, 11.75), (15, 19, 12.50),
-- Part 16: Expanding Folder
(16, 1, 120.00), (16, 14, 115.00), (16, 24, 122.00),
-- Part 17: Ring Binder
(17, 1, 72.00), (17, 10, 70.00), (17, 21, 74.00),
-- Part 18: Document Envelope
(18, 4, 9.00), (18, 25, 8.75), (18, 27, 9.25),
-- Part 19: Plastic Storage Box
(19, 2, 220.00), (19, 14, 215.00), (19, 24, 225.00),
-- Part 20: Desk Organizer
(20, 1, 175.00), (20, 11, 170.00), (20, 21, 178.00),
-- Part 21: USB Flash Drive
(21, 7, 290.00), (21, 13, 285.00), (21, 20, 295.00),
-- Part 22: Wireless Mouse
(22, 7, 420.00), (22, 17, 410.00), (22, 26, 425.00),
-- Part 23: Wireless Keyboard
(23, 8, 850.00), (23, 17, 835.00), (23, 26, 860.00),
-- Part 24: HD Webcam
(24, 7, 1350.00), (24, 20, 1325.00), (24, 29, 1380.00),
-- Part 25: Headset
(25, 8, 2400.00), (25, 17, 2350.00), (25, 29, 2450.00),
-- Part 26: WiFi Router
(26, 7, 1950.00), (26, 13, 1925.00), (26, 20, 1980.00),
-- Part 27: Network Switch
(27, 8, 1550.00), (27, 17, 1520.00), (27, 23, 1580.00),
-- Part 28: Ethernet Cable
(28, 7, 95.00), (28, 13, 92.00), (28, 26, 97.00),
-- Part 29: Surge Protector
(29, 8, 520.00), (29, 17, 510.00), (29, 20, 530.00),
-- Part 30: External HDD
(30, 13, 3200.00), (30, 20, 3150.00), (30, 29, 3250.00),
-- Part 31: Inkjet Printer
(31, 13, 4200.00), (31, 17, 4100.00), (31, 23, 4250.00),
-- Part 32: Laser Printer
(32, 8, 9800.00), (32, 20, 9700.00), (32, 26, 9900.00),
-- Part 33: AIO Printer
(33, 13, 12400.00), (33, 17, 12150.00), (33, 29, 12600.00),
-- Part 34: Color Laser Printer
(34, 17, 18800.00), (34, 23, 18500.00), (34, 29, 19050.00),
-- Part 35: Copier Machine
(35, 13, 64000.00), (35, 20, 63500.00), (35, 26, 64800.00),
-- Part 36: Ergonomic Chair
(36, 1, 4200.00), (36, 3, 4150.00), (36, 14, 4300.00),
-- Part 37: Executive Desk
(37, 2, 9200.00), (37, 10, 9100.00), (37, 24, 9350.00),
-- Part 38: Filing Cabinet
(38, 1, 6200.00), (38, 18, 6100.00), (38, 28, 6250.00),
-- Part 39: Conference Table
(39, 2, 18000.00), (39, 14, 17850.00), (39, 24, 18200.00),
-- Part 40: Bookshelf
(40, 1, 3100.00), (40, 3, 3050.00), (40, 21, 3150.00),
-- Part 41: Alcohol Spray
(41, 5, 75.00), (41, 15, 72.00), (41, 22, 78.00),
-- Part 42: Disinfecting Wipes
(42, 5, 90.00), (42, 16, 88.00), (42, 27, 92.00),
-- Part 43: Premium Color Toner (BOTTLENECK PART — zero stock)
(43, 8, 1850.00), (43, 17, 1800.00), (43, 26, 1900.00),
-- Part 44: A3 Laminating Pouches (BOTTLENECK PART — stock=1)
(44, 5, 280.00), (44, 15, 270.00), (44, 19, 290.00),
-- Part 45: Thermal Binding Machine (on_order=TRUE — already reordered)
(45, 8, 5500.00), (45, 13, 5400.00), (45, 17, 5600.00)
ON CONFLICT DO NOTHING;

-- ============================================================
--  TABLE 6: INVOICES (65 records)
--  Week of Aug 9 2006: Aug 6–12 (Mon–Sun)
--  Satisfies: Points 2,3,11,12,15, QD-Sec7,8,9,10,12
--
--  QD-Sec12 TEST: Reps 4,5,6,7,8 each have >10 invoices in the Aug 6-12 week
--  Invoice status mix: active, shipped, paid, void
--  Invoices 60,61,62 contain Parts 43 and 44 (bottleneck) and are NOT shipped
-- ============================================================
INSERT INTO invoices (invoice_id, employee_number, customer_number, date_written, total_amount, status)
VALUES
-- Sales Rep 4 (Kevin Lim) — 11 invoices in Aug 6-12 week → triggers QD-Sec12
(1,  4,  1,  DATE '2006-08-06', 15750.00, 'paid'),
(2,  4,  2,  DATE '2006-08-07', 8320.50,  'paid'),
(3,  4,  3,  DATE '2006-08-07', 4500.00,  'shipped'),
(4,  4,  4,  DATE '2006-08-08', 22100.00, 'shipped'),
(5,  4,  5,  DATE '2006-08-08', 9640.75,  'active'),
(6,  4,  6,  DATE '2006-08-09', 3200.00,  'active'),
(7,  4,  7,  DATE '2006-08-09', 17800.50, 'paid'),
(8,  4,  8,  DATE '2006-08-10', 5430.25,  'active'),
(9,  4,  9,  DATE '2006-08-10', 11200.00, 'shipped'),
(10, 4,  10, DATE '2006-08-11', 6780.00,  'paid'),
(11, 4,  11, DATE '2006-08-12', 9350.00,  'paid'),
-- Sales Rep 5 (Sophia Tan) — 11 invoices in Aug 6-12 week → triggers QD-Sec12
(12, 5,  12, DATE '2006-08-06', 12400.00, 'paid'),
(13, 5,  13, DATE '2006-08-06', 7650.25,  'shipped'),
(14, 5,  14, DATE '2006-08-07', 3100.00,  'active'),
(15, 5,  15, DATE '2006-08-07', 18900.50, 'paid'),
(16, 5,  16, DATE '2006-08-08', 5200.00,  'shipped'),
(17, 5,  17, DATE '2006-08-08', 24500.00, 'paid'),
(18, 5,  18, DATE '2006-08-09', 8900.75,  'active'),
(19, 5,  19, DATE '2006-08-09', 4320.00,  'shipped'),
(20, 5,  20, DATE '2006-08-10', 13600.00, 'active'),
(21, 5,  21, DATE '2006-08-11', 6780.50,  'paid'),
(22, 5,  22, DATE '2006-08-12', 9100.00,  'shipped'),
-- Sales Rep 6 (Miguel Garcia) — 11 invoices in Aug 6-12 week → triggers QD-Sec12
(23, 6,  23, DATE '2006-08-06', 19200.00, 'paid'),
(24, 6,  24, DATE '2006-08-06', 8750.25,  'shipped'),
(25, 6,  25, DATE '2006-08-07', 5400.00,  'active'),
(26, 6,  26, DATE '2006-08-07', 31000.00, 'paid'),
(27, 6,  27, DATE '2006-08-08', 14500.50, 'shipped'),
(28, 6,  28, DATE '2006-08-08', 7200.00,  'active'),
(29, 6,  29, DATE '2006-08-09', 22600.00, 'paid'),
(30, 6,  30, DATE '2006-08-09', 9800.75,  'active'),
(31, 6,  1,  DATE '2006-08-10', 4300.00,  'shipped'),
(32, 6,  2,  DATE '2006-08-11', 16750.00, 'paid'),
(33, 6,  3,  DATE '2006-08-12', 11200.50, 'shipped'),
-- Sales Rep 7 (Patricia Lopez) — 11 invoices in Aug 6-12 week → triggers QD-Sec12
(34, 7,  4,  DATE '2006-08-06', 8400.00,  'paid'),
(35, 7,  5,  DATE '2006-08-06', 3200.50,  'shipped'),
(36, 7,  6,  DATE '2006-08-07', 15600.00, 'active'),
(37, 7,  7,  DATE '2006-08-07', 6900.25,  'paid'),
(38, 7,  8,  DATE '2006-08-08', 27300.00, 'shipped'),
(39, 7,  9,  DATE '2006-08-08', 11200.00, 'active'),
(40, 7,  10, DATE '2006-08-09', 5600.75,  'paid'),
(41, 7,  11, DATE '2006-08-09', 19800.00, 'shipped'),
(42, 7,  12, DATE '2006-08-10', 8700.50,  'active'),
(43, 7,  13, DATE '2006-08-11', 13400.00, 'paid'),
(44, 7,  14, DATE '2006-08-12', 7100.25,  'shipped'),
-- Sales Rep 8 (Daniel Flores) — 11 invoices in Aug 6-12 week → triggers QD-Sec12
(45, 8,  15, DATE '2006-08-06', 9600.00,  'paid'),
(46, 8,  16, DATE '2006-08-06', 4200.50,  'shipped'),
(47, 8,  17, DATE '2006-08-07', 21500.00, 'paid'),
(48, 8,  18, DATE '2006-08-07', 8900.00,  'active'),
(49, 8,  19, DATE '2006-08-08', 16700.75, 'shipped'),
(50, 8,  20, DATE '2006-08-08', 6300.00,  'active'),
(51, 8,  21, DATE '2006-08-09', 12400.00, 'paid'),
(52, 8,  22, DATE '2006-08-09', 5800.50,  'shipped'),
(53, 8,  23, DATE '2006-08-10', 18900.00, 'active'),
(54, 8,  24, DATE '2006-08-11', 9100.25,  'paid'),
(55, 8,  25, DATE '2006-08-12', 7600.00,  'shipped'),
-- Other reps — fewer than 10 invoices each (should NOT appear in QD-Sec12)
(56, 9,  26, DATE '2006-08-07', 14200.00, 'paid'),
(57, 10, 27, DATE '2006-08-08', 8900.50,  'shipped'),
(58, 11, 28, DATE '2006-08-09', 5400.00,  'active'),
(59, 12, 29, DATE '2006-08-10', 21600.00, 'paid'),
(60, 13, 30, DATE '2006-08-11', 6800.25,  'shipped'),
-- CRITICAL BOTTLENECK INVOICES — contain Parts 43 and 44, status = active (unshipped)
-- QD-Sec5: These prove parts 43 and 44 are needed but not stocked and not on order
(61, 4,  1,  DATE '2006-08-07',  2800.00, 'active'),  -- Contains Part 43 (toner, stock=0)
(62, 5,  2,  DATE '2006-08-08',   450.00, 'active'),  -- Contains Part 44 (laminating, stock=1)
(63, 6,  3,  DATE '2006-08-09',  5600.00, 'active'),  -- Contains both Parts 43 and 44
-- Earlier week invoices for YTD testing (QD-Sec8, QD-Sec9)
(64, 9,  4,  DATE '2006-07-15', 11200.00, 'paid'),
(65, 10, 5,  DATE '2006-07-20',  8700.50, 'paid')
ON CONFLICT DO NOTHING;

-- ============================================================
--  TABLE 7: INVOICE_LINES (185 records)
--  Each invoice has 2-4 parts
--  Satisfies: Point 11, QD-Sec10, QD-Sec11, QD-Sec14
--
--  CRITICAL:
--  Lines for invoices 61,62,63 use Parts 43,44 (zero/one stock, unshipped)
--  to satisfy QD-Sec5 and QD-Sec11
-- ============================================================
INSERT INTO invoice_lines (invoice_id, part_number, quantity, line_total) VALUES
-- Invoice 1 (Rep 4, Customer 1)
(1, 6,  20,  7000.00), (1, 22,  5,  3250.00), (1, 1,  100, 1500.00), (1, 9,  15,   975.00),
-- Invoice 2 (Rep 4, Customer 2)
(2, 23,  3,  3600.00), (2, 17,  20, 2200.00), (2, 5,  30,  2550.00),
-- Invoice 3 (Rep 4, Customer 3)
(3, 11,  8,  2560.00), (3, 14,  13, 1950.00),
-- Invoice 4 (Rep 4, Customer 4)
(4, 37,  1, 14500.00), (4, 36,  1,  6800.00), (4, 40,  1,   800.00),
-- Invoice 5 (Rep 4, Customer 5)
(5, 24,  3,  5550.00), (5, 28,  22, 3960.00),
-- Invoice 6 (Rep 4, Customer 6)
(6, 18, 80,  2000.00), (6, 15,  30, 1050.00), (6, 12,  3,   150.00),
-- Invoice 7 (Rep 4, Customer 7)
(7, 33,  1, 15800.00), (7, 21,  4,  1800.00),
-- Invoice 8 (Rep 4, Customer 8)
(8, 29,  5,  3750.00), (8, 20,  6,  1680.00),
-- Invoice 9 (Rep 4, Customer 9)
(9, 32,  1, 12500.00), (9, 41,  20, 2400.00), (9, 42, 20,  3000.00),
-- Invoice 10 (Rep 4, Customer 10)
(10, 16, 15, 2700.00), (10, 13, 12, 1440.00), (10, 4,  80,  2800.00),
-- Invoice 11 (Rep 4, Customer 11)
(11, 7,  20, 5500.00), (11, 8,   8, 3600.00),
-- Invoice 12 (Rep 5, Customer 12)
(12, 38,  1, 9200.00), (12, 20,  5, 1400.00), (12, 3,  40,  1800.00),
-- Invoice 13 (Rep 5, Customer 13)
(13, 26,  2, 5600.00), (13, 22,  3, 1950.00),
-- Invoice 14 (Rep 5, Customer 14)
(14, 2, 100, 1500.00), (14, 1,  100, 1500.00), (14, 12, 2,   90.00),
-- Invoice 15 (Rep 5, Customer 15)
(15, 31,  2,11000.00), (15, 29,  5, 3750.00), (15, 21, 10,  4500.00),
-- Invoice 16 (Rep 5, Customer 16)
(16, 25,  1, 3200.00), (16, 24,  1, 1850.00), (16, 23,  1,  1200.00),
-- Invoice 17 (Rep 5, Customer 17)
(17, 34,  1,24500.00),
-- Invoice 18 (Rep 5, Customer 18)
(18, 36,  1, 6800.00), (18, 40,  1, 4800.00), (18, 28, 17,  3060.00),
-- Invoice 19 (Rep 5, Customer 19)
(19, 11,  5, 1600.00), (19, 13,  8,  960.00), (19, 15, 50,  1750.00),
-- Invoice 20 (Rep 5, Customer 20)
(20, 38,  1, 9200.00), (20, 19,  5, 1750.00), (20, 9,  40,  2600.00),
-- Invoice 21 (Rep 5, Customer 21)
(21, 22,  5, 3250.00), (21, 27,  1, 2200.00), (21, 3,  30,  1350.00),
-- Invoice 22 (Rep 5, Customer 22)
(22, 32,  1,12500.00), (22, 28, 20, 3600.00),
-- Invoice 23 (Rep 6, Customer 23)
(23, 35,  1,85000.00),
-- Invoice 24 (Rep 6, Customer 24)
(24, 30,  1, 4200.00), (24, 24,  2, 3700.00), (24, 22,  1,   650.00),
-- Invoice 25 (Rep 6, Customer 25)
(25, 6,  10, 3500.00), (25, 7,   7, 1925.00),
-- Invoice 26 (Rep 6, Customer 26)
(26, 33,  2,31600.00),
-- Invoice 27 (Rep 6, Customer 27)
(27, 36,  2,13600.00), (27, 40,  2,  900.00),
-- Invoice 28 (Rep 6, Customer 28)
(28, 23,  3, 3600.00), (28, 22,  4, 2600.00), (28, 21,  2,   900.00),
-- Invoice 29 (Rep 6, Customer 29)
(29, 37,  1,14500.00), (29, 38,  1, 9200.00), (29, 36,  1,  6800.00),
-- Invoice 30 (Rep 6, Customer 30)
(30, 25,  3, 9600.00),
-- Invoice 31 (Rep 6, Customer 1)
(31, 18,100, 2500.00), (31, 15,  50, 1750.00),
-- Invoice 32 (Rep 6, Customer 2)
(32, 31,  3,16500.00),
-- Invoice 33 (Rep 6, Customer 3)
(33, 32,  1,12500.00), (33, 28, 25, 4500.00), (33, 29,  2,  1500.00),
-- Invoice 34 (Rep 7, Customer 4)
(34, 36,  1, 6800.00), (34, 40,  3, 1400.00),
-- Invoice 35 (Rep 7, Customer 5)
(35, 12,100, 4500.00), (35, 15,100, 3500.00),
-- Invoice 36 (Rep 7, Customer 6)
(36, 33,  1,15600.00),
-- Invoice 37 (Rep 7, Customer 7)
(37, 22,  5, 3250.00), (37, 21,  8, 3600.00),
-- Invoice 38 (Rep 7, Customer 8)
(38, 37,  2,29000.00),
-- Invoice 39 (Rep 7, Customer 9)
(39, 23,  5, 6000.00), (39, 24,  1, 1850.00), (39, 22,  5, 3250.00),
-- Invoice 40 (Rep 7, Customer 10)
(40, 6,  16, 5600.00),
-- Invoice 41 (Rep 7, Customer 11)
(41, 33,  1,15800.00), (41, 30,  1, 4200.00),
-- Invoice 42 (Rep 7, Customer 12)
(42, 36,  1, 6800.00), (42, 40,  1, 4800.00), (42, 13, 8,   960.00),
-- Invoice 43 (Rep 7, Customer 13)
(43, 34,  1,24500.00), (43, 21,  5, 2250.00),
-- Invoice 44 (Rep 7, Customer 14)
(44, 29,  5, 3750.00), (44, 20,  5, 1400.00), (44, 16, 17,  3060.00),
-- Invoice 45 (Rep 8, Customer 15)
(45, 32,  1,12500.00), (45, 22,  2, 1300.00),
-- Invoice 46 (Rep 8, Customer 16)
(46, 18,200, 5000.00), (46, 9,  50, 3250.00), (46, 12,100,  4500.00),
-- Invoice 47 (Rep 8, Customer 17)
(47, 35,  1,85000.00),
-- Invoice 48 (Rep 8, Customer 18)
(48, 36,  2,13600.00), (48, 19,  5, 1750.00), (48, 4, 100,  3500.00),
-- Invoice 49 (Rep 8, Customer 19)
(49, 31,  2,11000.00), (49, 21,  10, 4500.00), (49, 6, 5,   1750.00),
-- Invoice 50 (Rep 8, Customer 20)
(50, 25,  2, 6400.00),
-- Invoice 51 (Rep 8, Customer 21)
(51, 33,  1,15800.00), (51, 22,  2, 1300.00),
-- Invoice 52 (Rep 8, Customer 22)
(52, 38,  1, 9200.00), (52, 40,  2,  9600.00),
-- Invoice 53 (Rep 8, Customer 23)
(53, 24,  5, 9250.00), (53, 26,  3, 8400.00), (53, 23,  1,  1200.00),
-- Invoice 54 (Rep 8, Customer 24)
(54, 32,  1,12500.00), (54, 22,  2, 1300.00),
-- Invoice 55 (Rep 8, Customer 25)
(55, 30,  1, 4200.00), (55, 28, 20, 3600.00),
-- Invoices 56-60 (other reps)
(56, 6,  20, 7000.00), (56, 22,  5, 3250.00), (56, 1, 100,  1500.00),
-- Invoice 57
(57, 23,  3, 3600.00), (57, 22,  5, 3250.00), (57, 3,  5,    225.00),
-- Invoice 58
(58, 36,  1, 6800.00), (58, 41, 10, 1200.00),
-- Invoice 59
(59, 35,  1,85000.00),
-- Invoice 60
(60, 37,  1,14500.00), (60, 40,  1, 4800.00),
-- CRITICAL BOTTLENECK INVOICE LINES
-- Invoice 61: Part 43 (Toner, stock=0, not on order) — satisfies QD-Sec5 and QD-Sec11
(61, 43,  1, 2800.00),
-- Invoice 62: Part 44 (Laminating, stock=1, not on order) — satisfies QD-Sec5 and QD-Sec11
(62, 44,  1,  450.00),
-- Invoice 63: Both bottleneck parts in one invoice
(63, 43,  2, 5600.00), (63, 44,  2,  900.00),
-- Earlier week invoices for YTD
(64, 32,  1,12500.00), (64, 29,  2, 1500.00), (64, 22,  2, 1300.00),
(65, 23,  3, 3600.00), (65, 22,  5, 3250.00),
-- QD-Sec14: Part 1 (Ballpoint Pen Blue) has highest total YTD quantity
-- Additional lines to inflate YTD quantities for QD-Sec14 testing
(1,  2, 50,  750.00), (4,  2, 80, 1200.00), (7,  2, 60,  900.00),
(10, 2, 90, 1350.00), (13, 2, 70, 1050.00), (16, 2, 55,  825.00),
(19, 2, 75, 1125.00), (22, 2, 65,  975.00),
-- Part 6 (Premium Bond Paper) second highest YTD quantity
(2,  6, 15, 5250.00), (5,  6, 12, 4200.00), (8,  6, 18, 6300.00),
(11, 6, 20, 7000.00), (14, 6, 10, 3500.00), (17, 6, 16, 5600.00)
ON CONFLICT DO NOTHING;

-- ============================================================
--  TABLE 8: TIMECARDS (75 records)
--  Covers 3 weeks: Jul 23, Jul 30, Aug 6 (2006)
--  Satisfies: Point 6, QD-Sec1, QD-Sec2
--
--    31,32,33,34,35,36,37,38,39,40,41,42,43,44,45 — these are ACTIVE HOURLY employees
--  Note: Reps (4-18) should NEVER have timecards (Points 7)
--  Note: Managers (1-3) treated as salaried — no timecards in this system
-- ============================================================
INSERT INTO timecards (timecard_id, employee_number, week_date, hours_worked)
VALUES
-- WEEK 1: July 23, 2006 (selected hourly staff)
(1,  19, DATE '2006-07-23', 40.00),
(2,  20, DATE '2006-07-23', 38.50),
(3,  21, DATE '2006-07-23', 42.00),
(4,  22, DATE '2006-07-23', 39.75),
(5,  23, DATE '2006-07-23', 40.50),
(6,  24, DATE '2006-07-23', 37.25),
(7,  25, DATE '2006-07-23', 41.00),
(8,  26, DATE '2006-07-23', 38.00),
(9,  27, DATE '2006-07-23', 40.25),
(10, 28, DATE '2006-07-23', 39.50),
(11, 29, DATE '2006-07-23', 42.75),
(12, 30, DATE '2006-07-23', 40.00),
(13, 31, DATE '2006-07-23', 38.25),
(14, 32, DATE '2006-07-23', 41.50),
(15, 33, DATE '2006-07-23', 39.00),
(16, 34, DATE '2006-07-23', 40.75),
(17, 35, DATE '2006-07-23', 37.50),

-- WEEK 2: July 30, 2006 (all 17 hourly staff)
(18, 19, DATE '2006-07-30', 40.00),
(19, 20, DATE '2006-07-30', 39.50),
(20, 21, DATE '2006-07-30', 41.75),
(21, 22, DATE '2006-07-30', 38.25),
(22, 23, DATE '2006-07-30', 40.50),
(23, 24, DATE '2006-07-30', 42.00),
(24, 25, DATE '2006-07-30', 39.75),
(25, 26, DATE '2006-07-30', 40.25),
(26, 27, DATE '2006-07-30', 38.50),
(27, 28, DATE '2006-07-30', 41.00),
(28, 29, DATE '2006-07-30', 39.25),
(29, 30, DATE '2006-07-30', 40.75),
(30, 31, DATE '2006-07-30', 38.00),
(31, 32, DATE '2006-07-30', 42.50),
(32, 33, DATE '2006-07-30', 39.50),
(33, 34, DATE '2006-07-30', 40.00),
(34, 35, DATE '2006-07-30', 38.75),

-- WEEK 3: August 9, 2006 (PARTIAL — only employees 19-30 submitted)
(35, 19, DATE '2006-08-09', 40.00),
(36, 20, DATE '2006-08-09', 38.00),
(37, 21, DATE '2006-08-09', 42.50),
(38, 22, DATE '2006-08-09', 39.25),
(39, 23, DATE '2006-08-09', 40.75),
(40, 24, DATE '2006-08-09', 41.00),
(41, 25, DATE '2006-08-09', 38.50),
(42, 26, DATE '2006-08-09', 40.25),
(43, 27, DATE '2006-08-09', 39.75),
(44, 28, DATE '2006-08-09', 42.00),
(45, 29, DATE '2006-08-09', 38.25),
(46, 30, DATE '2006-08-09', 40.50)
-- INTENTIONALLY MISSING FOR QD-Sec1:
-- Employees 31 through 45 (inclusive) are intentionally missing Aug 9 timecards
-- to produce the ~15 missing-employee scenario required by the Case Narration.
ON CONFLICT DO NOTHING;

-- ============================================================
--  TABLE 9: PURCHASE_ORDERS (35 records)
--  Satisfies: Point 5, QD-Sec4, QD-Sec5, QD-Sec10
--
--  Key records:
--  PO for Part 45 (Thermal Binding Machine, on_order=TRUE) — received=FALSE
--  No PO for Parts 43 and 44 — confirming they are NOT on order for QD-Sec4/5
--  Several POs received=FALSE for QD-Sec10
-- ============================================================
INSERT INTO purchase_orders (po_number, supplier_id, part_number, order_date, quantity_ordered, received, status)
VALUES
-- Part 45 (Thermal Binding Machine) — on_order=TRUE in parts table, confirms QD-Sec4 logic
(1,  8,  45, DATE '2006-08-01', 5, FALSE, 'Pending'),
-- High-ticket items on order
(2,  13, 35, DATE '2006-08-02', 3, FALSE, 'Pending'),
(3,  20, 35, DATE '2006-08-03', 2, FALSE, 'Pending'),
(4,  17, 33, DATE '2006-08-04', 4, FALSE, 'Pending'),
(5,  29, 34, DATE '2006-08-05', 2, FALSE, 'Pending'),
-- Stationery restocks
(6,  5,  6,  DATE '2006-08-06', 200, FALSE, 'Pending'),
(7,  15, 7,  DATE '2006-08-07', 150, FALSE, 'Pending'),
(8,  4,  1,  DATE '2006-08-01', 500, TRUE,  'Received'),
(9,  4,  2,  DATE '2006-08-02', 500, TRUE,  'Received'),
(10, 12, 3,  DATE '2006-08-03', 200, TRUE,  'Received'),
-- Tech peripherals
(11, 7,  21, DATE '2006-08-04', 100, FALSE, 'Pending'),
(12, 7,  22, DATE '2006-08-05', 80,  FALSE, 'Pending'),
(13, 17, 23, DATE '2006-08-06', 50,  FALSE, 'Pending'),
(14, 20, 24, DATE '2006-08-07', 30,  FALSE, 'Pending'),
(15, 17, 25, DATE '2006-08-08', 20,  FALSE, 'Pending'),
-- Furniture orders
(16, 1,  36, DATE '2006-08-01', 10,  FALSE, 'Pending'),
(17, 2,  37, DATE '2006-08-02', 5,   FALSE, 'Pending'),
(18, 18, 38, DATE '2006-08-03', 8,   FALSE, 'Pending'),
(19, 14, 39, DATE '2006-08-04', 2,   FALSE, 'Pending'),
(20, 3,  40, DATE '2006-08-05', 10,  TRUE,  'Received'),
-- More stationery
(21, 4,  4,  DATE '2006-08-06', 200, TRUE,  'Received'),
(22, 5,  5,  DATE '2006-08-07', 100, TRUE,  'Received'),
(23, 12, 9,  DATE '2006-08-08', 200, FALSE, 'Pending'),
(24, 22, 10, DATE '2006-08-01', 150, FALSE, 'Pending'),
(25, 11, 11, DATE '2006-08-02', 50,  FALSE, 'Pending'),
(26, 5,  12, DATE '2006-08-03', 300, TRUE,  'Received'),
(27, 19, 13, DATE '2006-08-04', 80,  FALSE, 'Pending'),
(28, 18, 14, DATE '2006-08-05', 100, FALSE, 'Pending'),
(29, 5,  15, DATE '2006-08-06', 250, FALSE, 'Pending'),
(30, 1,  16, DATE '2006-08-07', 120, FALSE, 'Pending'),
-- Printers
(31, 13, 31, DATE '2006-08-08', 10,  FALSE, 'Pending'),
(32, 8,  32, DATE '2006-08-01', 8,   FALSE, 'Pending'),
(33, 26, 30, DATE '2006-08-02', 15,  FALSE, 'Pending'),
(34, 5,  41, DATE '2006-08-03', 200, TRUE,  'Received'),
(35, 16, 42, DATE '2006-08-04', 150, TRUE,  'Received')
ON CONFLICT DO NOTHING;

-- ============================================================
--  TABLE 10: EMPLOYEE_PAYMENTS (55 records)
--  Weekly check history for all employee types
--  Satisfies: Point 8, QD-Sec2, QD-Sec9
-- ============================================================
INSERT INTO employee_payments (payment_id, employee_number, timecard_id, invoice_period_end, check_number, amount_paid, date_paid, payment_type)
VALUES
-- HOURLY PAYMENTS — Week ending Jul 23 (based on timecards 1-17)
(1,  19, 1,  NULL, 'CHK-03-0001', 4800.00, DATE '2006-07-28', 'hourly'),
(2,  20, 2,  NULL, 'CHK-03-0002', 4447.25, DATE '2006-07-28', 'hourly'),
(3,  21, 3,  NULL, 'CHK-03-0003', 5470.50, DATE '2006-07-28', 'hourly'),
(4,  22, 4,  NULL, 'CHK-03-0004', 4968.75, DATE '2006-07-28', 'hourly'),
(5,  23, 5,  NULL, 'CHK-03-0005', 4809.38, DATE '2006-07-28', 'hourly'),
(6,  24, 6,  NULL, 'CHK-03-0006', 4563.13, DATE '2006-07-28', 'hourly'),
(7,  25, 7,  NULL, 'CHK-03-0007', 4797.00, DATE '2006-07-28', 'hourly'),
(8,  26, 8,  NULL, 'CHK-03-0008', 4864.00, DATE '2006-07-28', 'hourly'),
(9,  27, 9,  NULL, 'CHK-03-0009', 4669.00, DATE '2006-07-28', 'hourly'),
(10, 28, 10, NULL, 'CHK-03-0010', 5332.50, DATE '2006-07-28', 'hourly'),
(11, 29, 11, NULL, 'CHK-03-0011', 5193.63, DATE '2006-07-28', 'hourly'),
(12, 30, 12, NULL, 'CHK-03-0012', 4960.00, DATE '2006-07-28', 'hourly'),
(13, 31, 13, NULL, 'CHK-03-0013', 4577.44, DATE '2006-07-28', 'hourly'),
(14, 32, 14, NULL, 'CHK-03-0014', 5239.38, DATE '2006-07-28', 'hourly'),
(15, 33, 15, NULL, 'CHK-03-0015', 4582.50, DATE '2006-07-28', 'hourly'),
(16, 34, 16, NULL, 'CHK-03-0016', 5419.75, DATE '2006-07-28', 'hourly'),
(17, 35, 17, NULL, 'CHK-03-0017', 4575.00, DATE '2006-07-28', 'hourly'),
-- HOURLY PAYMENTS — Week ending Jul 30 (based on timecards 18-34)
(18, 19, 18, NULL, 'CHK-03-0018', 4800.00, DATE '2006-08-04', 'hourly'),
(19, 20, 19, NULL, 'CHK-03-0019', 4563.75, DATE '2006-08-04', 'hourly'),
(20, 21, 20, NULL, 'CHK-03-0020', 5438.19, DATE '2006-08-04', 'hourly'),
(21, 22, 21, NULL, 'CHK-03-0021', 4781.25, DATE '2006-08-04', 'hourly'),
(22, 23, 22, NULL, 'CHK-03-0022', 4809.38, DATE '2006-08-04', 'hourly'),
(23, 24, 23, NULL, 'CHK-03-0023', 5145.00, DATE '2006-08-04', 'hourly'),
(24, 25, 24, NULL, 'CHK-03-0024', 4651.25, DATE '2006-08-04', 'hourly'),
(25, 26, 25, NULL, 'CHK-03-0025', 5152.00, DATE '2006-08-04', 'hourly'),
(26, 27, 26, NULL, 'CHK-03-0026', 4466.00, DATE '2006-08-04', 'hourly'),
(27, 28, 27, NULL, 'CHK-03-0027', 5535.00, DATE '2006-08-04', 'hourly'),
(28, 29, 28, NULL, 'CHK-03-0028', 4768.88, DATE '2006-08-04', 'hourly'),
(29, 30, 29, NULL, 'CHK-03-0029', 5053.00, DATE '2006-08-04', 'hourly'),
(30, 31, 30, NULL, 'CHK-03-0030', 4549.50, DATE '2006-08-04', 'hourly'),
(31, 32, 31, NULL, 'CHK-03-0031', 5365.63, DATE '2006-08-04', 'hourly'),
(32, 33, 32, NULL, 'CHK-03-0032', 4632.13, DATE '2006-08-04', 'hourly'),
(33, 34, 33, NULL, 'CHK-03-0033', 5320.00, DATE '2006-08-04', 'hourly'),
(34, 35, 34, NULL, 'CHK-03-0034', 4726.25, DATE '2006-08-04', 'hourly'),
-- HOURLY PAYMENTS — Week ending Aug 9 (based on timecards 35-46, employees 19-30 only)
(35, 19, 35, NULL, 'CHK-03-0035', 4800.00, DATE '2006-08-11', 'hourly'),
(36, 20, 36, NULL, 'CHK-03-0036', 4389.00, DATE '2006-08-11', 'hourly'),
(37, 21, 37, NULL, 'CHK-03-0037', 5535.63, DATE '2006-08-11', 'hourly'),
(38, 22, 38, NULL, 'CHK-03-0038', 4906.25, DATE '2006-08-11', 'hourly'),
(39, 23, 39, NULL, 'CHK-03-0039', 4839.06, DATE '2006-08-11', 'hourly'),
(40, 24, 40, NULL, 'CHK-03-0040', 5022.50, DATE '2006-08-11', 'hourly'),
(41, 25, 41, NULL, 'CHK-03-0041', 4504.50, DATE '2006-08-11', 'hourly'),
(42, 26, 42, NULL, 'CHK-03-0042', 5152.00, DATE '2006-08-11', 'hourly'),
(43, 27, 43, NULL, 'CHK-03-0043', 4611.00, DATE '2006-08-11', 'hourly'),
(44, 28, 44, NULL, 'CHK-03-0044', 5670.00, DATE '2006-08-11', 'hourly'),
(45, 29, 45, NULL, 'CHK-03-0045', 4643.63, DATE '2006-08-11', 'hourly'),
(46, 30, 46, NULL, 'CHK-03-0046', 5022.00, DATE '2006-08-11', 'hourly'),
-- COMMISSION PAYMENTS — Sales Reps week ending Aug 9
(47, 4,  NULL, DATE '2006-08-09', 'CHK-02-0047', 6131.13, DATE '2006-08-11', 'commission'),
(48, 5,  NULL, DATE '2006-08-09', 'CHK-02-0048', 6277.53, DATE '2006-08-11', 'commission'),
(49, 6,  NULL, DATE '2006-08-09', 'CHK-02-0049', 8577.50, DATE '2006-08-11', 'commission'),
(50, 7,  NULL, DATE '2006-08-09', 'CHK-02-0050', 5830.00, DATE '2006-08-11', 'commission'),
(51, 8,  NULL, DATE '2006-08-09', 'CHK-02-0051', 6420.00, DATE '2006-08-11', 'commission'),
(52, 9,  NULL, DATE '2006-08-09', 'CHK-02-0052', 710.00,  DATE '2006-08-11', 'commission'),
(53, 10, NULL, DATE '2006-08-09', 'CHK-02-0053', 435.03,  DATE '2006-08-11', 'commission'),
(54, 11, NULL, DATE '2006-08-09', 'CHK-02-0054', 270.00,  DATE '2006-08-11', 'commission'),
(55, 12, NULL, DATE '2006-08-09', 'CHK-02-0055', 1080.00, DATE '2006-08-11', 'commission')
ON CONFLICT DO NOTHING;

-- ============================================================
--  TABLE 11: CUSTOMER_PAYMENTS (50 records)
--  Shows balance reductions over time including partial payments
--  Satisfies: Point 1, Point 3, Anomaly 2 (customer_payments table)
-- ============================================================
INSERT INTO customer_payments (payment_id, customer_number, invoice_id, payment_date, amount_paid, payment_method)
VALUES
(1,  1,  1,  DATE '2006-08-10', 15750.00, 'check'),
(2,  1,  7,  DATE '2006-08-13', 17800.50, 'transfer'),
(3,  2,  2,  DATE '2006-08-11', 8320.50,  'cash'),
(4,  4,  4,  DATE '2006-08-12', 22100.00, 'transfer'),
(5,  7,  7,  DATE '2006-08-13', 17800.50, 'check'),
(6,  10, 10, DATE '2006-08-14', 6780.00,  'transfer'),
(7,  11, 11, DATE '2006-08-15', 9350.00,  'check'),
(8,  12, 12, DATE '2006-08-10', 12400.00, 'cash'),
(9,  15, 15, DATE '2006-08-11', 18900.50, 'transfer'),
(10, 17, 17, DATE '2006-08-12', 24500.00, 'check'),
(11, 21, 21, DATE '2006-08-13', 6780.50,  'transfer'),
(12, 22, 22, DATE '2006-08-14', 9100.00,  'cash'),
(13, 23, 23, DATE '2006-08-15', 19200.00, 'check'),
(14, 24, 24, DATE '2006-08-10', 8750.25,  'transfer'),
(15, 26, 26, DATE '2006-08-11', 31000.00, 'check'),
(16, 29, 29, DATE '2006-08-12', 22600.00, 'transfer'),
-- Partial payments (balance remains — tests current_balance logic)
(17, 5,  5,  DATE '2006-08-13',  5000.00, 'cash'),     -- Invoice total 9640.75, partial
(18, 6,  6,  DATE '2006-08-14',  1500.00, 'transfer'),  -- Invoice total 3200.00, partial
(19, 8,  8,  DATE '2006-08-15',  3000.00, 'check'),     -- Invoice total 5430.25, partial
(20, 14, 14, DATE '2006-08-10',  1500.00, 'cash'),      -- Invoice total 3100.00, partial
(21, 20, 20, DATE '2006-08-11',  8000.00, 'transfer'),  -- Invoice total 13600.00, partial
(22, 25, 25, DATE '2006-08-12',  2000.00, 'check'),     -- Invoice total 5400.00, partial
(23, 27, 27, DATE '2006-08-13',  7000.00, 'cash'),      -- Invoice total 14500.50, partial
(24, 30, 30, DATE '2006-08-14',  5000.00, 'transfer'),  -- Invoice total 9800.75, partial
-- Full payments for other invoices
(25, 2,  32, DATE '2006-08-15', 16500.00, 'transfer'),
(26, 3,  33, DATE '2006-08-10', 12500.00, 'check'),
(27, 4,  34, DATE '2006-08-11',  8400.00, 'cash'),
(28, 5,  35, DATE '2006-08-12',  3200.50, 'transfer'),
(29, 7,  37, DATE '2006-08-13',  6900.25, 'check'),
(30, 10, 40, DATE '2006-08-14',  5600.75, 'transfer'),
(31, 11, 41, DATE '2006-08-15', 19800.00, 'cash'),
(32, 13, 43, DATE '2006-08-10', 24500.00, 'transfer'),
(33, 15, 45, DATE '2006-08-11', 12500.00, 'check'),
(34, 16, 46, DATE '2006-08-12',  4200.50, 'transfer'),
(35, 17, 47, DATE '2006-08-13', 85000.00, 'cash'),
(36, 18, 48, DATE '2006-08-14', 13600.00, 'transfer'),
(37, 21, 51, DATE '2006-08-15', 15800.00, 'check'),
(38, 22, 52, DATE '2006-08-10',  9200.00, 'transfer'),
(39, 24, 54, DATE '2006-08-11', 12500.00, 'cash'),
(40, 25, 55, DATE '2006-08-12',  4200.00, 'transfer'),
-- General account credits not tied to specific invoice (NULL invoice_id)
(41, 9,  NULL, DATE '2006-08-13', 5000.00, 'check'),
(42, 13, NULL, DATE '2006-08-14', 3000.00, 'transfer'),
(43, 16, NULL, DATE '2006-08-15', 2000.00, 'cash'),
(44, 19, NULL, DATE '2006-08-10', 1500.00, 'transfer'),
(45, 28, NULL, DATE '2006-08-11', 2500.00, 'check'),
-- Earlier payments for balance history
(46, 29, 56, DATE '2006-08-08', 14200.00, 'transfer'),
(47, 30, 59, DATE '2006-08-09', 21600.00, 'check'),
(48, 38, 57, DATE '2006-08-10',  8900.50, 'cash'),
(49, 39, 58, DATE '2006-08-11',  5400.00, 'transfer'),
(50, 40, 60, DATE '2006-08-12',  6800.25, 'check')
ON CONFLICT DO NOTHING;

-- ============================================================
--  SEQUENCE ALIGNMENT
--  Ensure all SERIAL sequences are set past the manually inserted max IDs
-- ============================================================
SELECT setval(pg_get_serial_sequence('customers','customer_number'),       (SELECT MAX(customer_number) FROM customers), true);
SELECT setval(pg_get_serial_sequence('employees','employee_number'),       (SELECT MAX(employee_number) FROM employees), true);
SELECT setval(pg_get_serial_sequence('suppliers','supplier_id'),           (SELECT MAX(supplier_id) FROM suppliers), true);
SELECT setval(pg_get_serial_sequence('parts','part_number'),               (SELECT MAX(part_number) FROM parts), true);
SELECT setval(pg_get_serial_sequence('invoices','invoice_id'),             (SELECT MAX(invoice_id) FROM invoices), true);
SELECT setval(pg_get_serial_sequence('timecards','timecard_id'),           (SELECT MAX(timecard_id) FROM timecards), true);
SELECT setval(pg_get_serial_sequence('purchase_orders','po_number'),       (SELECT MAX(po_number) FROM purchase_orders), true);
SELECT setval(pg_get_serial_sequence('customer_payments','payment_id'),    (SELECT MAX(payment_id) FROM customer_payments), true);
SELECT setval(pg_get_serial_sequence('employee_payments','payment_id'),    (SELECT MAX(payment_id) FROM employee_payments), true);
