import sqlite3

DB_PATH = "data/kestrel_ops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


print("\nOrders with deliveries")
print("-" * 60)

cursor.execute("""
    SELECT
        COUNT(DISTINCT o.order_id),
        COUNT(DISTINCT d.order_id)
    FROM orders o
    LEFT JOIN deliveries d
        ON o.order_id = d.order_id;
""")

print(cursor.fetchone())


print("\nOrders with multiple deliveries")
print("-" * 60)

cursor.execute("""
    SELECT
        order_id,
        COUNT(*) AS delivery_count
    FROM deliveries
    GROUP BY order_id
    HAVING COUNT(*) > 1
    ORDER BY delivery_count DESC
    LIMIT 20;
""")

for row in cursor.fetchall():
    print(row)


print("\nSample order + delivery data")
print("-" * 60)

cursor.execute("""
    SELECT
        o.order_id,
        o.order_date,
        o.requested_delivery_date,
        o.order_status,

        d.delivery_id,
        d.delivery_status,
        d.planned_arrival,
        d.actual_arrival,
        d.delay_minutes

    FROM orders o

    JOIN deliveries d
        ON o.order_id = d.order_id

    ORDER BY o.order_id

    LIMIT 20;
""")

for row in cursor.fetchall():
    print(row)


connection.close()