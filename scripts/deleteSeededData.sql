-- Safely remove seeded data. Uses IF EXISTS to avoid errors
-- and resets serial PKs. Run as: psql -f deleteSeededData.sql
-- Use a DO block to truncate only tables that actually exist in the current schema.
-- This avoids using `TRUNCATE ... IF EXISTS` which isn't available on some PG versions.

DO $$
DECLARE
    tbls text[] := ARRAY[
        'customers',
        'employees',
        'timecards',
        'payroll',
        'invoices',
        'invoice_lines',
        'customer_payments',
        'suppliers',
        'parts',
        'item_parts',
        'purchase_orders'
    ];
    existing text;
BEGIN
    SELECT string_agg(quote_ident(schemaname) || '.' || quote_ident(tablename), ',')
    INTO existing
    FROM pg_tables
    WHERE schemaname = current_schema()
      AND tablename = ANY(tbls);

    IF existing IS NOT NULL THEN
        EXECUTE 'TRUNCATE TABLE ' || existing || ' RESTART IDENTITY CASCADE';
    END IF;
END$$;