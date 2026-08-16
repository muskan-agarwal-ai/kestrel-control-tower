import sqlite3

DB_PATH = "data/kestrel_ops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


print("\nNear-Expiry Inventory")
print("-" * 70)

cursor.execute("""
SELECT

    COUNT(*) AS inventory_rows,

    SUM(on_hand_cases) AS on_hand_cases,

    SUM(available_cases) AS available_cases

FROM inventory_snapshots

WHERE
    expiry_date IS NOT NULL

    AND DATE(expiry_date)
        >= DATE(snapshot_date)

    AND DATE(expiry_date)
        <= DATE(snapshot_date, '+30 days');
""")

result = cursor.fetchone()

print(f"Inventory rows:       {result[0]:,}")
print(f"On-hand cases:        {result[1]:,}")
print(f"Available cases:      {result[2]:,}")


print("\nNear-Expiry by Warehouse")
print("-" * 70)

cursor.execute("""
SELECT

    w.warehouse_name,

    COUNT(*) AS inventory_rows,

    SUM(i.on_hand_cases) AS on_hand_cases,

    SUM(i.available_cases) AS available_cases

FROM inventory_snapshots i

JOIN warehouses w
    ON i.warehouse_id = w.warehouse_id

WHERE
    i.expiry_date IS NOT NULL

    AND DATE(i.expiry_date)
        >= DATE(i.snapshot_date)

    AND DATE(i.expiry_date)
        <= DATE(i.snapshot_date, '+30 days')

GROUP BY
    w.warehouse_id,
    w.warehouse_name

ORDER BY
    available_cases DESC;
""")

for row in cursor.fetchall():
    print(row)


print("\nNear-Expiry by Month")
print("-" * 70)

cursor.execute("""
SELECT

    SUBSTR(snapshot_date, 1, 7) AS month,

    SUM(on_hand_cases) AS on_hand_cases,

    SUM(available_cases) AS available_cases

FROM inventory_snapshots

WHERE
    expiry_date IS NOT NULL

    AND DATE(expiry_date)
        >= DATE(snapshot_date)

    AND DATE(expiry_date)
        <= DATE(snapshot_date, '+30 days')

GROUP BY month

ORDER BY month;
""")

for row in cursor.fetchall():
    print(row)


print("\nMost At-Risk Products")
print("-" * 70)

cursor.execute("""
SELECT

    p.sku_code,
    p.product_name,

    SUM(i.available_cases) AS available_cases

FROM inventory_snapshots i

JOIN products p
    ON i.product_id = p.product_id

WHERE
    i.expiry_date IS NOT NULL

    AND DATE(i.expiry_date)
        >= DATE(i.snapshot_date)

    AND DATE(i.expiry_date)
        <= DATE(i.snapshot_date, '+30 days')

GROUP BY
    p.product_id,
    p.sku_code,
    p.product_name

ORDER BY
    available_cases DESC

LIMIT 20;
""")

for row in cursor.fetchall():
    print(row)


connection.close()