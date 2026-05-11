import psycopg2
import psycopg2.extras

conn = psycopg2.connect(
    dbname="nos_db",
    user="postgres",
    password="02j16e88d",
    host="localhost"
)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# Show current timecards for hourly employees
print("Current timecards:")
cur.execute("""
    SELECT t.timecard_id, e.employee_name, t.week_date, t.hours_worked
    FROM   timecards t
    JOIN   employees e ON e.employee_number = t.employee_number
    WHERE  t.week_date >= '2026-01-01'
    ORDER  BY t.week_date DESC, e.employee_name
""")
rows = cur.fetchall()
for r in rows:
    print(f"  ID:{r['timecard_id']} | {r['employee_name']} | {r['week_date']} | {r['hours_worked']} hrs")

if not rows:
    print("  No 2026 timecards found.")
else:
    print()
    confirm = input("Delete ALL 2026 timecards? (yes/no): ").strip().lower()
    if confirm == "yes":
        cur.execute("DELETE FROM timecards WHERE week_date >= '2026-01-01'")
        print(f"Deleted {cur.rowcount} timecard(s).")
        conn.commit()
    else:
        print("Cancelled.")

cur.close()
conn.close()