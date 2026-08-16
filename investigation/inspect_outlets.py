import sqlite3


DB_PATH = "data/kestrel_ops.db"


connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


print("Outlet Status")
print("-------------")

cursor.execute("""
    SELECT
        status,
        is_deleted,
        COUNT(*) AS outlet_count
    FROM outlets
    GROUP BY status, is_deleted
    ORDER BY status, is_deleted;
""")

for row in cursor.fetchall():
    print(row)


print()
print("Potential Test / Migration Outlets")
print("-----------------------------------")

cursor.execute("""
    SELECT
        outlet_id,
        outlet_code,
        outlet_name,
        status,
        is_deleted,
        city
    FROM outlets
    WHERE
        UPPER(outlet_name) LIKE '%TEST%'
        OR UPPER(outlet_name) LIKE '%MIGRAT%'
        OR UPPER(outlet_code) LIKE '%TEST%'
    ORDER BY outlet_id;
""")

rows = cursor.fetchall()

print(f"Found: {len(rows)}")

for row in rows:
    print(row)


connection.close()