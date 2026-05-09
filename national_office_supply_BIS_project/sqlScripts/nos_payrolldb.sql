-- 1. CLEANUP (Optional: Runs only if tables exist to ensure a fresh start)
DROP TABLE IF EXISTS payroll_audit;
DROP TABLE IF EXISTS timecards;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS employees;

-- 2. PURPLE SECTION: EMPLOYEES (The Central Hub)
CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    employee_fullname VARCHAR(100) NOT NULL,
    employee_role VARCHAR(50) NOT NULL, -- 'Manager', 'Hourly', or 'Sales Rep'
    ssn VARCHAR(11) NOT NULL,           -- You will mask this in Python
    hourly_rate DECIMAL(10, 2) DEFAULT 0.00
);

-- 3. PINK SECTION: TIMECARDS (Hourly Work)
CREATE TABLE timecards (
    timecard_id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(employee_id) ON DELETE CASCADE,
    hours_worked DECIMAL(5, 2) NOT NULL,
    work_date DATE DEFAULT CURRENT_DATE
);

-- 4. YELLOW SECTION: INVOICES (Sales Rep Activity)
CREATE TABLE invoices (
    invoice_id SERIAL PRIMARY KEY,
    sales_rep_id INTEGER REFERENCES employees(employee_id) ON DELETE CASCADE,
    total_amount DECIMAL(10, 2) NOT NULL,
    sale_date DATE DEFAULT CURRENT_DATE
);

-- 5. GREEN SECTION: PAYROLL AUDIT (Final Results)
CREATE TABLE payroll_audit (
    audit_id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(employee_id) ON DELETE CASCADE,
    gross_pay DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending', -- 'Pending' or 'Processed'
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
	
INSERT INTO employees (name, username, password_hash, ssn, address, position, hourly_wage, ytdsales, commission_rate)
VALUES
    -- Managers (Full Access) [cite: 295, 298]
    ('Antonio Porsild',             'NOS-266-0001', '$2b$12$tUaIjSdObndsrt1jLlCR6iy/HNd/Zs.2lUdHSHxH8zzW97q6NzqcP', '127-27-8808', 'Mandaluyong',   'Manager', 550.0, NULL, NULL),
    ('Jacqueline Tonio-Laxamana',   'NOS-266-0002', '$2b$12$QQ253RWZ.uW40sNzs4thmDCwVGC21pYwIkQaLugFZl2m7Mga6TIy1', '895-12-7942', 'Makati',        'Manager', 550.0, NULL, NULL),
    ('Martha Castillo',             'NOS-266-0003', '$2b$12$aFbBbCEWHISCYW3f9.VuEwzt442IYdneKqyi6nRjNXBMWYuktcy7C', '890-53-2909', 'Bacoor',        'Manager', 550.0, NULL, NULL),
    ('Leo Alba',                    'NOS-266-0004', '$2b$12$/ihjmxWeKtn7P1xpmkq4czTrRSQ7RyNIpJUlXl9OGaIHziu/JTndj', '379-31-4816', 'San Pedro',     'Manager', 550.0, NULL, NULL),
    ('Edilberto Manalangin',        'NOS-266-0005', '$2b$12$tmKvw67UDZtjAaSC2DTHfa4qZJ6J2XexOfuAQFYA6CIpwUEu14Syb', '159-27-4639', 'Valenzuel',     'Manager', 550.0, NULL, NULL),
    ('Olive Castro',                'NOS-266-0006', '$2b$12$k33ExXbGaRIjNoWGLu8IKMOf0Ck2dikyGzSd9XiguRfDPUAQqakO5', '505-90-3571', 'Marikina',      'Manager', 550.0, NULL, NULL),
    ('Marissa Payumo',              'NOS-266-0007', '$2b$12$bj5wJxwb1ea7LLnbPzsqd7hiss8.q5YSbVqydC9Xu6KHTBPQCe4J/', '756-28-6498', 'Las Piñas',     'Manager', 550.0, NULL, NULL),

    -- Hourly (Paid by QD-Sec1/2) [cite: 296, 298]
    ('Alexandra Colmenares', 'NOS-267-0001', '$2b$12$UETTiy.Y6M1YpDGn6eiqR73WDabp5HAqUbHCVXTLM9CyBkqEVSpnC', '700-59-8319', 'Cavite', 'Hourly', 250.0, NULL, NULL),
    ('Patricia Arellano', 'NOS-267-0002', '$2b$12$XIetObzVdBXrlNn0sMQfNFGjKzvZuMsZ5opWUiE.Ua2IUxIhSH44z', '777-43-6120', 'Quezon City', 'Hourly', 150.0, NULL, NULL),
    ('Randy De Guzman', 'NOS-267-0003', '$2b$12$pZyosmeSVctQQwXCpjmXcf1o4k/Kz8IL4Fm5lWjPwb.o.MuJGm03t', '568-65-7617', 'Makati', 'Hourly', 160.0, NULL, NULL),
    ('Vanessa Cruz', 'NOS-267-0004', '$2b$12$DRurkslRJROHODsGETHZCXIwm3g84KkKT9B2D/iFrUfwbIimVfTzq', '272-89-3807', 'Cebu', 'Hourly', 175.5, NULL, NULL),
    ('Jared Santos', 'NOS-267-0005', '$2b$12$iwT20HJyvzJsigToaGUCQ4U3yMdDBrZLodFAk1ttFHaNluFthIJeX', '550-97-5259', 'Makati', 'Hourly', 225.0, NULL, NULL),
    ('Emilia Reyes', 'NOS-267-0006', '$2b$12$sINPZRpDZIfjiqIZUQQ7zAHYGpoaM8z6FxCcSjKB263IpXuwRSlIC', '741-87-8865', 'Pampanga', 'Hourly', 250.0, NULL, NULL),
    ('Christopher Galvez', 'NOS-267-0007', '$2b$12$UKuEaTzMZ1hzB6n8n5/K6jngfPDKCVAZGbVrhgg.VFTHJfuu4vLlm', '505-59-9675', 'Quezon City', 'Hourly', 180.0, NULL, NULL),
    ('Eliseo Juan', 'NOS-267-0008', '$2b$12$aG6CJZdb/ZYHcqKeWppI6rnKOWQf9WlcOkhQrORSHHM2bq1w18IjF', '405-15-6859', 'Batangas', 'Hourly', 180.0, NULL, NULL),
    ('', 'NOS-267-0009', '$2b$12$Uvcb.qFmqlo0V0huKHnI0IrO209W/ZzLT9pbl67xMSNXULEfUgz3F', '163-55-4129', 'Laguna', 'Hourly', 225.0, NULL, NULL),
    ('', 'NOS-267-0010', '$2b$12$ZrPyayUZc2CZ7mBL4LAdyoGUEHIyHeZFzvkcqat8GDaWDXzuiwtd1', '581-13-3945', 'Laguna', 'Hourly', 250.0, NULL, NULL),
    ('', 'NOS-267-0011', '$2b$12$4XnT3qOI0yEA.QgyCO76tCWpjald5KoMFxAk1oxUmzVVBZg7L4n9B', '208-89-2207', 'Pampanga', 'Hourly', 225.0, NULL, NULL),
    ('', 'NOS-267-0012', '$2b$12$mUVChH7tE79Qy.nC7fGwb6pY5tyg2avoP22Gb/r8ANVjZYrxq7tFw', '674-74-1323', 'Bacoor', 'Hourly', 200.0, NULL, NULL),
    ('', 'NOS-267-0013', '$2b$12$V5.gx5MB6ZAOFc7psg/LV8d8NNa6ciWw6OED0zVhlZiXC31ak9ql.', '754-32-4362', 'Pampanga', 'Hourly', 175.5, NULL, NULL),
    ('', 'NOS-267-0014', '$2b$12$p0OmYcrfdBmSzNFgOmDRLc0tj90HyQ53BDRRKPogiuPayMInPfIa5', '313-41-7199', 'Mandaluyong', 'Hourly', 160.0, NULL, NULL),
    ('', 'NOS-267-0015', '$2b$12$lQrD03Kh32lm/no1n6N18G2hTmygFHO9DiDkw0oosUFyoS5rwjv/c', '343-58-3914', 'Davao', 'Hourly', 175.5, NULL, NULL),
    ('', 'NOS-267-0016', '$2b$12$M8syOQGbU1rId/Z7oOuMeYy3ptZGGdRkQj8kFkOvwAEZTWGVvjKD7', '113-33-2585', 'Cebu', 'Hourly', 180.0, NULL, NULL),
    ('', 'NOS-267-0017', '$2b$12$Cb8HufNinDI1MdGG2Xexu8xzHZSvi/0TPtLMlL9meo1/a4opS6C/y', '559-61-9874', 'Bulacan', 'Hourly', 150.0, NULL, NULL),
    ('', 'NOS-267-0018', '$2b$12$zoAGVegVpktgqNgeUs.y4r/Iu3Augowoa4ze46yG6gBCIFszMURFF', '580-49-7672', 'Davao', 'Hourly', 250.0, NULL, NULL),
    ('', 'NOS-267-0019', '$2b$12$R9IAoLsm77j4/IehGKPqozfwqcvpWRVk.O.gZn5xtBMBTwi5jSeMw', '140-36-2994', 'Quezon City', 'Hourly', 175.5, NULL, NULL),
    ('', 'NOS-267-0020', '$2b$12$gp35JVHf22SdSnpe9SeMDgp3GdZ7e816Bf1nk/sJ7bymAw6DUBT3W', '547-89-1146', 'Makati', 'Hourly', 180.0, NULL, NULL),
    ('', 'NOS-267-0021', '$2b$12$..wCNLs7f/qkHrDyBwY9kUc3QOrqKSLHiduKcx0KFyGLABIDfaaK5', '539-87-8769', 'Laguna', 'Hourly', 225.0, NULL, NULL),
    ('', 'NOS-267-0022', '$2b$12$UhhenTb8ULipo/F4ZjeEqD9qx9Kvh9zayZCbGgyb8MxCnlbbUnt5y', '147-98-3598', 'Pasig', 'Hourly', 150.0, NULL, NULL),
    ('', 'NOS-267-0023', '$2b$12$b6pwPMbC3fEE4l7TBet2P3VkEv8D.3uR55v5pcB98JGe5AzPsDieM', '307-17-8109', 'Cavite', 'Hourly', 180.0, NULL, NULL),
    ('', 'NOS-267-0024', '$2b$12$4cw2eoLNhjs98IGcxpzmO6WiUGhztxLb.QcJzAU92/05d3fyhU9rj', '152-81-1870', 'Laguna', 'Hourly', 150.0, NULL, NULL),
    ('', 'NOS-267-0025', '$2b$12$jAwioi/5cZWEl/CuBwjufZszVgbPXbT9PwvTalUR3t5xuhPAPO6i2', '330-52-2539', 'Bulacan', 'Hourly', 250.0, NULL, NULL),
    ('', 'NOS-267-0026', '$2b$12$vNg6oLm8IUCPCLWx5dX5TuXmDbFlstXtK4rIOR.mClguHcwH3WAyx', '239-58-7303', 'Pampanga', 'Hourly', 150.0, NULL, NULL),
    ('', 'NOS-267-0027', '$2b$12$mAZGF7Spjyl9iK/.yPXvdc./87LGIn7P2RBVfHXtslcwprw1/XnqW', '518-55-6291', 'Cebu', 'Hourly', 250.0, NULL, NULL),
    ('', 'NOS-267-0028', '$2b$12$w7GCX4fkIujWooZ4bGoRxFHsDRstPJe4K/Uk6.tf4EE1yuJnlDWsD', '190-38-8657', 'Cebu', 'Hourly', 180.0, NULL, NULL),
    ('', 'NOS-267-0029', '$2b$12$KYUMhwaZZrvJIC.l15pg5Yg892eoRd35rVoDTIqgT4jXZKu9Ewzcp', '797-94-8206', 'Davao', 'Hourly', 250.0, NULL, NULL),
    ('', 'NOS-267-0030', '$2b$12$vVLTrUXiZ16H7BF9Gu3D/JFv5Rj4q7Q7NXfftImabHLJji33q3LnS', '396-73-2006', 'Batangas', 'Hourly', 250.0, NULL, NULL),

	-- Sales Reps (Paid by 5% Commission) [cite: 296, 298]
    ('Daniel Hernandez', 'NOS-268-0001', '$2b$12$V5NbLx39MTPEQv8ZuWyayzN4TPuM5v85EvNVKyTHwyXw2PFswLItF', '361-23-6620', 'Batangas', 'Sales Rep', NULL, 0.0, 0.05),
    ('John Reyes', 'NOS-268-0002', '$2b$12$cimWvIX4b4BccZeDSvgDpkLAnh81a2BjmBdY7Bzf7R7VjVxHSzIjp', '771-72-7053', 'Quezon City', 'Sales Rep', NULL, 0.0, 0.05),
    ('Elizabeth Reyes', 'NOS-268-0003', '$2b$12$wMkabDk4voLpQrywTVsZBMI//hIk0etVRqoqMal6/i/Ejuy2sA893', '511-51-5434', 'Cebu', 'Sales Rep', NULL, 0.0, 0.05),
    ('James Andamon', 'NOS-268-0004', '$2b$12$12wpzt/QEqChPmbbOr69SuKp.gDPlvphEtWvz8rPDbppQc9INSyZc', '105-83-4770', 'Quezon City', 'Sales Rep', NULL, 0.0, 0.05),
    ('David Santos', 'NOS-268-0005', '$2b$12$A2uVFwpI4HhWOzOFFBeFBfLhPYqj78aCP6MV6/6EEvo1MNtsx8nR2', '648-95-1789', 'Davao', 'Sales Rep', NULL, 0.0, 0.05),
    ('Elizabeth Jugado', 'NOS-268-0006', '$2b$12$v1Eff6MJlYmmv5yX4FiCBUd7ao6Ohfl530uu5ZXcFNXYlJBYvtGd6', '673-98-5402', 'Cebu', 'Sales Rep', NULL, 0.0, 0.05),
    ('Richard Joson', 'NOS-268-0007', '$2b$12$tn/qiaqowGmQJnMAHcbeGPxGdSiuon9qLg.6svANDxGL6OLGMjcv0', '773-61-6640', 'Bulacan', 'Sales Rep', NULL, 0.0, 0.05),
    ('Susan Salamanca', 'NOS-268-0008', '$2b$12$JNAfFTmdCF6sKQyweP9hs0UQMCw2KbyVhudbbrHQ70ft5iQvk5j5s', '829-80-7413', 'Pasig', 'Sales Rep', NULL, 0.0, 0.05),
    ('Sarah Elago', 'NOS-268-0009', '$2b$12$2WFbQCp4Nu4gVy6hAq4bWbp7dqVWalq/eNaSjNQdpJ91vziZunl/E', '317-86-1332', 'Bulacan', 'Sales Rep', NULL, 0.0, 0.05),
    ('Robert Punzalan', 'NOS-268-0010', '$2b$12$.B8fcz8bhHa5muoeiXg7taUHT7laBgt95AqPl3I7b1T.4xr4/7KBv', '477-32-8567', 'Quezon City', 'Sales Rep', NULL, 0.0, 0.05),
    ('Barbara Hernandez', 'NOS-268-0011', '$2b$12$.itx3WeIMZso7mhCbf2HbE902i6q4JZ/NFX1VmVbpunigy3OOurYv', '363-51-5330', 'Makati', 'Sales Rep', NULL, 0.0, 0.05),
    ('James Reyes', 'NOS-268-0012', '$2b$12$hTLuXCn2chf5k2/sLt0DU7htmXh.TlEUyL196/CoHH1athhcnSWPj', '795-14-4358', 'Pampanga', 'Sales Rep', NULL, 0.0, 0.05),
    ('John Garcia', 'NOS-268-0013', '$2b$12$OFLC2vgO9mEAMh2Gjsxaa4hL5.9lKtdKHOCN4endOI/DMvQubhF5f', '625-93-1944', 'Batangas', 'Sales Rep', NULL, 0.0, 0.05),
    ('Ana Katigbak', 'NOS-268-0014', '$2b$12$d./t59HOuok25.4ZZAKhUjyNjFwkq3168.y9Fk/JuDehz2sHqvKgg', '330-14-1622', 'Bulacan', 'Sales Rep', NULL, 0.0, 0.05),
    ('David Go', 'NOS-268-0015', '$2b$12$UaFjBlDt0eFJ9bah1pNdTb.GVXp/wFn9fNTvZN1S1SWBKJnfdtV7d', '515-44-9885', 'Pampanga', 'Sales Rep', NULL, 0.0, 0.05),
    ('Michael Santos', 'NOS-268-0016', '$2b$12$RsoLprb64IiFuPkf7yRXD.ZOkvX7Ahw0DUq1iW8APrkUY4tn0BwNU', '591-47-4850', 'Pasig', 'Sales Rep', NULL, 0.0, 0.05),
    ('James Lopez', 'NOS-268-0017', '$2b$12$tgq6.1AcX9jEd5XWodv8ny/u/E4AZkQH8gP.rAcFSUh9j6TCYYl9n', '257-76-4359', 'Bulacan', 'Sales Rep', NULL, 0.0, 0.05),
    ('Jennifer Hernandez', 'NOS-268-0018', '$2b$12$qi.592qtVVD37BuS2RJVWe7oW6i5oFSxt/M9wWHIARihUeWcaGLGs', '119-64-9578', 'Laguna', 'Sales Rep', NULL, 0.0, 0.05),
    ('Jessica Bustria', 'NOS-268-0019', '$2b$12$U/eQbSuQgdoxY.yCE1VhLmE9PgD/BZPBHGZNKGO6f8.BtjYLb9/sP', '232-63-7674', 'Batangas', 'Sales Rep', NULL, 0.0, 0.05),
    ('Joseph Tarun', 'NOS-268-0020', '$2b$12$VxP/LajXK4gCE0wukSkmLy4kP2QqJw2adccGpH4PqkaCI5Udlly7Q', '430-22-7220', 'Davao', 'Sales Rep', NULL, 0.0, 0.05),
    ('Jennifer Tuldac', 'NOS-268-0021', '$2b$12$p2rGLZNUSvdKeYwMQikkY3bQRW3ys84kDYY94sfvtB6GzXreJIwHY', '208-23-9431', 'Cavite', 'Sales Rep', NULL, 0.0, 0.05),
    ('Joseph Manahan', 'NOS-268-0022', '$2b$12$76TJIqX1H.GKtwmBzWqbDvUitihURztBBcChwShTeA6rIZEE2rOyF', '153-40-5680', 'Pasig', 'Sales Rep', NULL, 0.0, 0.05),
    ('James Gonzalez', 'NOS-268-0023', '$2b$12$ydQB/E1Lt42u8a4NL/4FBgOrPGfWiz9SAayzuzkdNubAeRiu5.WcZ', '810-88-2583', 'Batangas', 'Sales Rep', NULL, 0.0, 0.05),
    ('David Oliveros', 'NOS-268-0024', '$2b$12$XAJ28j6NGSVKisr2ZhvTHBJQWJeCicCEvQKWpVw4zYnnEt7iuzZvC', '746-88-5739', 'Cavite', 'Sales Rep', NULL, 0.0, 0.05),
    ('Jennifer Garcia', 'NOS-268-0025', '$2b$12$Ko3HAFyE.fCHsB9VMUeNaL9n//kugSWLhMcC92HYUnpNtAjuNVfrb', '541-30-9465', 'Laguna', 'Sales Rep', NULL, 0.0, 0.05),
    ('Linda Cruz', 'NOS-268-0026', '$2b$12$erCDF0DEYmtWHdT0AO5GLirAXGRwqzFzqizb.F4HlKRysA0yoDkMV', '787-99-1703', 'Makati', 'Sales Rep', NULL, 0.0, 0.05),
    ('Lorenz Lopez', 'NOS-268-0027', '$2b$12$yRoViyuvDcOIV21EHSIGwPkEWnlDJHu/4/NiMW2Antae7BQdhfRAO', '785-76-1035', 'Bacoor', 'Sales Rep', NULL, 0.0, 0.05),
    ('Jessica Cruz', 'NOS-268-0028', '$2b$12$gCIhFAT7tXmZ4F6U9EarcEeSdVQK5IcZGN0mdCU5xcJTMIq2KR.tb', '678-32-7853', 'Bulacan', 'Sales Rep', NULL, 0.0, 0.05),
    ('Joseph Reyes', 'NOS-268-0029', '$2b$12$Ft9xVVU2mtR96ZE9Yyt9HE1FercxRhG.S0.WYAMvOD5ya1PHyWGqc', '486-42-6237', 'Manila', 'Sales Rep', NULL, 0.0, 0.05),
    ('Robert Garcia', 'NOS-268-0030', '$2b$12$s5wMb8MkTAs9Q8.Tl53jf16zgZmyS07d4ybytIWhN7ko4RWZ9i3Wa', '303-79-1618', 'Batangas', 'Sales Rep', NULL, 0.0, 0.05),
    ('Barbara Santos', 'NOS-268-0031', '$2b$12$l1hBjidZ2j.pmks4uyNb7H.VbOjogrdM6Q4Z6YUXNIkNWcqpHve9I', '579-56-2515', 'Makati', 'Sales Rep', NULL, 0.0, 0.05),
    ('James Lopez', 'NOS-268-0032', '$2b$12$WcZTI6ZFqNEwVAIQ/4XK607CeeKBDYrGzRHBFp5Zci/FJJMrVfQ6K', '504-98-7354', 'Makati', 'Sales Rep', NULL, 0.0, 0.05),
    ('Daniel Martinez', 'NOS-268-0033', '$2b$12$LZFd2HzazHi7Yu3aM1E0ipRSiG0KTt1cy7miO2KyamiQAYq4KEVpM', '891-17-8537', 'Manila', 'Sales Rep', NULL, 0.0, 0.05),
    ('Joseph Reyes', 'NOS-268-0034', '$2b$12$rE2gd1ZPrFYXTWPjBack7leJBo21xwKFF8lILJh8ULXbATeeRHhFM', '526-66-3174', 'Davao', 'Sales Rep', NULL, 0.0, 0.05),
    ('Thomas Martinez', 'NOS-268-0035', '$2b$12$wMvZ1AoQCboU3i907mLs909sHuZZuklfWH63IeWOj9XSoQT.dCTow', '431-74-8179', 'Batangas', 'Sales Rep', NULL, 0.0, 0.05),
    ('Jessica Wilson', 'NOS-268-0036', '$2b$12$F/pLogeV2ZTINgoIAzyMpZ.JwMTyL8lUcAgBdQedEh3N0kyItw2uV', '338-63-8825', 'Davao', 'Sales Rep', NULL, 0.0, 0.05),
    ('Daniel Smith', 'NOS-268-0037', '$2b$12$wwyjz5Wt88LXjiKri4KIztulWKzEm.GVMS9ew98qT0ujjccnoLmnX', '304-69-6824', 'Batangas', 'Sales Rep', NULL, 0.0, 0.05),
    ('Elizabeth Hernandez', 'NOS-268-0038', '$2b$12$xRCzkdjhCUJXSyDnTWc3IJrlrU4HdoHrnis9t3cvBubFNni/A69bw', '207-14-6767', 'Laguna', 'Sales Rep', NULL, 0.0, 0.05),
    ('Richard Cruz', 'NOS-268-0039', '$2b$12$D.Cpd41o2jyFDj5S8BwikonsHcIZSBHoZh7mitRnuoxCkDrScDobX', '495-97-8644', 'Pampanga', 'Sales Rep', NULL, 0.0, 0.05),
    ('Jennifer Garcia', 'NOS-268-0040', '$2b$12$IXJWjYBRNqGRFMVRoA99ll99pZyZAqJhm3g5p0mjt7.G3TSbLrU6z', '270-94-9150', 'Quezon City', 'Sales Rep', NULL, 0.0, 0.05);