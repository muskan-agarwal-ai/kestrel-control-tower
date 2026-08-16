import sqlite3

DB_PATH = "data/kestrel_ops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


print("\nOrders WITHOUT deliveries by status")
print("-" * 60)

cursor.execute("""
    SELECT
        o.order_status,
        COUNT(*) AS orders_without_delivery
    FROM orders o
    LEFT JOIN deliveries d
        ON o.order_id = d.order_id
    WHERE d.order_id IS NULL
    GROUP BY o.order_status
    ORDER BY o.order_status;
""")

for row in cursor.fetchall():
    print(row)


print("\nOrders WITH deliveries by status")
print("-" * 60)

cursor.execute("""
    SELECT
        o.order_status,
        COUNT(*) AS orders_with_delivery
    FROM orders o
    JOIN deliveries d
        ON o.order_id = d.order_id
    GROUP BY o.order_status
    ORDER BY o.order_status;
""")

for row in cursor.fetchall():
    print(row)


print("\nOn-time vs late based on requested delivery date")
print("-" * 60)

cursor.execute("""
    SELECT
        CASE
            WHEN DATE(d.actual_arrival) <= DATE(o.requested_delivery_date)
                THEN 'ON_TIME'
            ELSE 'LATE'
        END AS timing_status,

        COUNT(*) AS orders

    FROM orders o

    JOIN deliveries d
        ON o.order_id = d.order_id

    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')

    GROUP BY timing_status;
""")

for row in cursor.fetchall():
    print(row)


connection.close()