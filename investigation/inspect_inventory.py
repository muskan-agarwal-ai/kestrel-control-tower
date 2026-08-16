import sqlite3

DB_PATH = "data/kestrel_ops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


print("\nInventory Snapshot Date Range")
print("-" * 70)

cursor.execute("""
SELECT
    MIN(snapshot_date),
    MAX(snapshot_date),
    COUNT(DISTINCT snapshot_date)

FROM inventory_snapshots;
""")

print(cursor.fetchone())


print("\nAgeing Buckets")
print("-" * 70)

cursor.execute("""
SELECT
    ageing_bucket,
    COUNT(*) AS rows,
    SUM(on_hand_cases) AS on_hand_cases,
    SUM(available_cases) AS available_cases

FROM inventory_snapshots

GROUP BY ageing_bucket

ORDER BY ageing_bucket;
""")

for row in cursor.fetchall():
    print(row)


print("\nExpiry Date Range")
print("-" * 70)

cursor.execute("""
SELECT
    MIN(expiry_date),
    MAX(expiry_date)

FROM inventory_snapshots
WHERE expiry_date IS NOT NULL;
""")

print(cursor.fetchone())


print("\nSample Inventory Records")
print("-" * 70)

cursor.execute("""
SELECT
    snapshot_date,
    warehouse_id,
    product_id,
    batch_id,
    on_hand_cases,
    available_cases,
    days_of_cover,
    expiry_date,
    ageing_bucket

FROM inventory_snapshots

ORDER BY expiry_date

LIMIT 20;
""")

for row in cursor.fetchall():
    print(row)


connection.close()