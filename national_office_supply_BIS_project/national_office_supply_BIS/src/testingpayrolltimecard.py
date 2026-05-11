"""
Adds a unique constraint to timecards(employee_number, week_date)
so ON CONFLICT works correctly for upserts.
"""
import psycopg2

conn = psycopg2.connect(
    dbname="nos_db",
    user="postgres",
    password="02j16e88d",
    host="localhost"
)
cur = conn.cursor()

# Remove duplicate timecards first (keep the one with most hours)
cur.execute("""
    DELETE FROM timecards
    WHERE timecard_id NOT IN (
        SELECT DISTINCT ON (employee_number, week_date)
               timecard_id
        FROM   timecards
        ORDER  BY employee_number, week_date, hours_worked DESC
    )
""")
deleted = cur.rowcount
print(f"Removed {deleted} duplicate timecard rows.")

# Add unique constraint
try:
    cur.execute("""
        ALTER TABLE timecards
        ADD CONSTRAINT uq_timecards_emp_week
        UNIQUE (employee_number, week_date)
    """)
    print("Unique constraint added: (employee_number, week_date)")
except Exception as e:
    print(f"Constraint may already exist: {e}")

conn.commit()
cur.close()
conn.close()
print("Done! Timecard upserts will now work correctly.")