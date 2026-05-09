-- ============================================================
-- National Office Supplies BIS
-- QD query library using the live PostgreSQL schema
-- Each block is named so Python can load and execute it directly.
-- ============================================================

-- QD-Sec1: Active hourly employees missing a timecard for a target week
SELECT
	e.employee_number,
	e.employee_name,
	e.employee_address,
	e.hourly_wage,
	%(week_date)s::date AS week_date
FROM employees e
LEFT JOIN timecards t
	ON t.employee_number = e.employee_number
	AND t.week_date = %(week_date)s::date
WHERE e.is_active = TRUE
	AND e.position = 'Hourly'
	AND t.timecard_id IS NULL
ORDER BY e.employee_name, e.employee_number;

-- QD-Sec2: Weekly payroll base for hourly employees with a completed timecard
SELECT
	e.employee_number,
	e.employee_name,
	t.week_date,
	t.hours_worked,
	e.hourly_wage,
	ROUND((t.hours_worked * COALESCE(e.hourly_wage, 0))::numeric, 2) AS gross_pay
FROM timecards t
JOIN employees e
	ON e.employee_number = t.employee_number
WHERE e.is_active = TRUE
	AND e.position = 'Hourly'
	AND t.week_date = %(week_date)s::date
ORDER BY e.employee_name, e.employee_number;

-- QD-Sec3: Low-stock parts at or below the restock trigger
SELECT
	p.part_number,
	p.description,
	p.stock_count,
	p.trigger_amount,
	p.restock_value,
	p.on_order
FROM parts p
WHERE p.stock_count <= p.trigger_amount
ORDER BY p.stock_count ASC, p.part_number;

-- QD-Sec4: Low-stock parts that do not already have an open purchase order
SELECT
	p.part_number,
	p.description,
	p.stock_count,
	p.trigger_amount,
	NOT EXISTS (
		SELECT 1
		FROM purchase_orders po
		WHERE po.part_number = p.part_number
			AND po.received = FALSE
	) AS on_order
FROM parts p
WHERE p.stock_count <= p.trigger_amount
	AND NOT EXISTS (
		SELECT 1
		FROM purchase_orders po
		WHERE po.part_number = p.part_number
			AND po.received = FALSE
	)
ORDER BY p.stock_count ASC, p.part_number;

-- QD-Sec5: Critical stock items that are also needed by active invoices
SELECT
	p.part_number,
	p.description,
	p.stock_count,
	p.trigger_amount,
	p.on_order,
	COUNT(DISTINCT i.invoice_id) AS active_invoice_count,
	COUNT(DISTINCT il.invoice_id) AS linked_invoice_count
FROM parts p
LEFT JOIN invoice_lines il
	ON il.part_number = p.part_number
LEFT JOIN invoices i
	ON i.invoice_id = il.invoice_id
	AND i.status = 'active'
WHERE p.stock_count <= 1
	AND p.on_order = FALSE
GROUP BY p.part_number, p.description, p.stock_count, p.trigger_amount, p.on_order
HAVING COUNT(DISTINCT i.invoice_id) > 0
ORDER BY p.stock_count ASC, p.part_number;

-- QD-Sec6: Stock ordering report with best supplier and order state
WITH best_supplier AS (
	SELECT DISTINCT ON (ip.part_number)
		ip.part_number,
		s.supplier_id,
		s.company_name AS supplier_name,
		s.phone_number,
		ip.cost AS unit_cost
	FROM item_parts ip
	JOIN suppliers s
		ON s.supplier_id = ip.supplier_id
	ORDER BY ip.part_number, ip.cost ASC, s.supplier_id
)
SELECT
	p.part_number,
	p.description,
	p.stock_count,
	p.trigger_amount,
	GREATEST(p.trigger_amount - p.stock_count, 0) AS shortage,
	bs.supplier_name,
	bs.phone_number,
	bs.unit_cost,
	CASE
		WHEN EXISTS (
			SELECT 1
			FROM purchase_orders po
			WHERE po.part_number = p.part_number
				AND po.received = FALSE
		) THEN 'Pending Order'
		ELSE 'Not Ordered'
	END AS order_status
FROM parts p
JOIN best_supplier bs
	ON bs.part_number = p.part_number
WHERE p.stock_count <= p.trigger_amount
ORDER BY p.stock_count ASC, p.part_number;

-- QD-Sec7: Low-stock parts ordered by supplier then part
SELECT
	s.supplier_id,
	s.company_name AS supplier_name,
	s.phone_number,
	p.part_number,
	p.description,
	p.stock_count,
	p.trigger_amount,
	ip.cost AS unit_cost
FROM parts p
JOIN item_parts ip
	ON ip.part_number = p.part_number
JOIN suppliers s
	ON s.supplier_id = ip.supplier_id
WHERE p.stock_count <= p.trigger_amount
ORDER BY s.company_name, p.part_number;

-- QD-Sec7b: Weekly sales summary per sales rep
SELECT
	e.employee_number,
	e.employee_name,
	COUNT(i.invoice_id) AS invoice_count,
	COALESCE(SUM(i.total_amount), 0) AS total_sales,
	COALESCE(MAX(i.total_amount), 0) AS largest_sale,
	COALESCE(AVG(i.total_amount), 0) AS average_sale,
	COUNT(DISTINCT i.customer_number) AS customer_count,
	COALESCE(SUM(i.total_amount), 0) * 0.05 AS commission,
	%(week_end)s::date AS week_end
FROM employees e
LEFT JOIN invoices i
	ON i.employee_number = e.employee_number
	AND i.date_written BETWEEN %(week_start)s::date AND %(week_end)s::date
WHERE e.is_active = TRUE
	AND e.position = 'Sales Rep'
GROUP BY e.employee_number, e.employee_name
ORDER BY total_sales DESC, e.employee_name, e.employee_number;

-- QD-Sec8: Update year-to-date sales for sales reps
UPDATE employees e
SET ytdsales = COALESCE(sub.total_sales, 0)
FROM (
	SELECT
		e.employee_number,
		SUM(i.total_amount) AS total_sales
	FROM employees e
	LEFT JOIN invoices i
		ON i.employee_number = e.employee_number
		AND i.date_written >= DATE_TRUNC('year', CURRENT_DATE)::date
		AND i.date_written < (DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year')::date
		AND i.status <> 'void'
	WHERE e.position = 'Sales Rep'
	GROUP BY e.employee_number
) sub
WHERE e.employee_number = sub.employee_number
	AND e.position = 'Sales Rep';

-- QD-Sec8-customer: Customer balance snapshot with account status
SELECT
	c.customer_number,
	c.customer_name,
	c.company_name,
	c.phone_number,
	c.address,
	c.current_balance,
	CASE WHEN c.is_active THEN 'Active' ELSE 'Closed' END AS account_status
FROM customers c
ORDER BY c.company_name, c.customer_name, c.customer_number;

-- QD-Sec9: Year-to-date sales analytics for sales reps
SELECT
	e.employee_number,
	e.employee_name,
	COALESCE(SUM(i.total_amount), 0) AS total_sales,
	COUNT(i.invoice_id) AS invoice_count,
	COALESCE(MAX(i.total_amount), 0) AS largest_sale,
	COALESCE(AVG(i.total_amount), 0) AS average_sale,
	COUNT(DISTINCT i.customer_number) AS customer_count,
	COALESCE(SUM(i.total_amount), 0) * 0.05 AS commission,
	COALESCE(SUM(i.total_amount), 0) AS ytd_sales
FROM employees e
LEFT JOIN invoices i
	ON i.employee_number = e.employee_number
	AND i.date_written >= DATE_TRUNC('year', CURRENT_DATE)::date
	AND i.date_written < (DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year')::date
WHERE e.is_active = TRUE
	AND e.position = 'Sales Rep'
GROUP BY e.employee_number, e.employee_name
ORDER BY total_sales DESC, e.employee_name, e.employee_number;

-- QD-Sec10: Ordered parts that have not shipped yet
SELECT DISTINCT
	i.invoice_id,
	i.date_written,
	c.customer_number,
	c.company_name,
	p.part_number,
	p.description,
	il.quantity,
	i.status
FROM invoices i
JOIN customers c
	ON c.customer_number = i.customer_number
JOIN invoice_lines il
	ON il.invoice_id = i.invoice_id
JOIN parts p
	ON p.part_number = il.part_number
WHERE i.status = 'active'
ORDER BY i.invoice_id, p.part_number;

-- QD-Sec11: Invoice bottlenecks where stock is already critical
SELECT
	i.invoice_id,
	i.date_written,
	c.company_name,
	p.part_number,
	p.description,
	p.stock_count,
	il.quantity,
	GREATEST(il.quantity - p.stock_count, 0) AS shortage
FROM invoice_lines il
JOIN invoices i
	ON i.invoice_id = il.invoice_id
JOIN customers c
	ON c.customer_number = i.customer_number
JOIN parts p
	ON p.part_number = il.part_number
WHERE i.status = 'active'
	AND p.stock_count <= 1
ORDER BY i.invoice_id, p.part_number;

-- QD-Sec12: High-performance sales reps with more than 10 invoices in a week
SELECT
	e.employee_number,
	e.employee_name,
	COUNT(i.invoice_id) AS invoice_count,
	COALESCE(SUM(i.total_amount), 0) AS total_sales,
	COALESCE(AVG(i.total_amount), 0) AS average_invoice_value
FROM employees e
JOIN invoices i
	ON i.employee_number = e.employee_number
WHERE e.is_active = TRUE
	AND e.position = 'Sales Rep'
	AND i.date_written BETWEEN %(week_start)s::date AND %(week_end)s::date
GROUP BY e.employee_number, e.employee_name
HAVING COUNT(i.invoice_id) > 10
ORDER BY total_sales DESC, e.employee_name, e.employee_number;

-- QD-Sec13: Best price procurement list per part
SELECT DISTINCT ON (ip.part_number)
	ip.part_number,
	p.description,
	s.supplier_id,
	s.company_name AS supplier_name,
	s.phone_number,
	ip.cost AS unit_cost
FROM item_parts ip
JOIN parts p
	ON p.part_number = ip.part_number
JOIN suppliers s
	ON s.supplier_id = ip.supplier_id
ORDER BY ip.part_number, ip.cost ASC, s.supplier_id;

-- QD-Sec14: Double restock value for the top two year-to-date parts by sales volume
WITH ranked_parts AS (
	SELECT
		p.part_number,
		p.description,
		SUM(il.quantity) AS ytd_units_sold,
		p.restock_value
	FROM invoice_lines il
	JOIN invoices i
		ON i.invoice_id = il.invoice_id
	JOIN parts p
		ON p.part_number = il.part_number
	WHERE i.date_written >= DATE_TRUNC('year', CURRENT_DATE)::date
		AND i.date_written < (DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year')::date
	GROUP BY p.part_number, p.description, p.restock_value
	ORDER BY ytd_units_sold DESC, p.part_number
),
selected_parts AS (
	SELECT part_number
	FROM ranked_parts
	ORDER BY ytd_units_sold DESC, part_number
	LIMIT 2
)
UPDATE parts p
SET restock_value = p.restock_value * 2
FROM selected_parts sp
WHERE p.part_number = sp.part_number;

-- QD-Sec14-preview: Confirm the two parts selected for the restock change
SELECT
	part_number,
	description,
	ytd_units_sold,
	restock_value,
	restock_value * 2 AS proposed_restock_value
FROM ranked_parts
ORDER BY ytd_units_sold DESC, part_number
LIMIT 2;

-- QD-Sec15: Apply price inflation to parts with zero year-to-date sales
UPDATE parts p
SET selling_price = CASE
	WHEN p.restock_value < 4 THEN ROUND((p.selling_price * 1.10)::numeric, 2)
	ELSE ROUND((p.selling_price * 1.20)::numeric, 2)
END
WHERE NOT EXISTS (
	SELECT 1
	FROM invoice_lines il
	JOIN invoices i
		ON i.invoice_id = il.invoice_id
	WHERE il.part_number = p.part_number
		AND i.date_written >= DATE_TRUNC('year', CURRENT_DATE)::date
		AND i.date_written < (DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year')::date
);

-- QD-Sec15-preview: Show parts that qualify for the inflation rule
SELECT
	p.part_number,
	p.description,
	p.selling_price,
	p.restock_value,
	CASE
		WHEN p.restock_value < 4 THEN ROUND((p.selling_price * 1.10)::numeric, 2)
		ELSE ROUND((p.selling_price * 1.20)::numeric, 2)
	END AS proposed_price
FROM parts p
WHERE NOT EXISTS (
	SELECT 1
	FROM invoice_lines il
	JOIN invoices i
		ON i.invoice_id = il.invoice_id
	WHERE il.part_number = p.part_number
		AND i.date_written >= DATE_TRUNC('year', CURRENT_DATE)::date
		AND i.date_written < (DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year')::date
)
ORDER BY p.part_number;
