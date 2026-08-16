import sqlite3

DB_PATH = "data/kestrel_ops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

print("\n" + "=" * 60)
print("1. QUANTITY UNITS")
print("=" * 60)

cursor.execute("""
    SELECT
        qty_uom,
        COUNT(*) AS rows,
        COUNT(case_pack_at_order) AS rows_with_case_pack,
        MIN(case_pack_at_order) AS min_case_pack,
        MAX(case_pack_at_order) AS max_case_pack
    FROM order_lines
    GROUP BY qty_uom;
""")

for row in cursor.fetchall():
    print(row)


print("\n" + "=" * 60)
print("2. ORDER STATUS")
print("=" * 60)

cursor.execute("""
    SELECT
        order_status,
        COUNT(*) AS orders
    FROM orders
    GROUP BY order_status
    ORDER BY orders DESC;
""")

for row in cursor.fetchall():
    print(row)


print("\n" + "=" * 60)
print("3. OUTLET STATUS")
print("=" * 60)

cursor.execute("""
    SELECT
        status,
        is_deleted,
        COUNT(*) AS outlets
    FROM outlets
    GROUP BY status, is_deleted
    ORDER BY status;
""")

for row in cursor.fetchall():
    print(row)


print("\n" + "=" * 60)
print("4. DELIVERY STATUS")
print("=" * 60)

cursor.execute("""
    SELECT
        delivery_status,
        COUNT(*) AS deliveries
    FROM deliveries
    GROUP BY delivery_status;
""")

for row in cursor.fetchall():
    print(row)


print("\n" + "=" * 60)
print("5. SAMPLE ORDER LINES")
print("=" * 60)

cursor.execute("""
    SELECT
        order_line_id,
        order_id,
        product_id,
        ordered_qty,
        qty_uom,
        case_pack_at_order,
        allocated_qty,
        delivered_qty,
        line_value_inr
    FROM order_lines
    LIMIT 15;
""")

for row in cursor.fetchall():
    print(row)

print("\n" + "=" * 60)
print("6. ORDER LINE QUANTITIES BY ORDER STATUS")
print("=" * 60)

cursor.execute("""
    SELECT
        o.order_status,
        COUNT(ol.order_line_id) AS order_lines,
        SUM(ol.ordered_qty) AS ordered_qty,
        SUM(ol.delivered_qty) AS delivered_qty
    FROM orders o
    JOIN order_lines ol
        ON o.order_id = ol.order_id
    GROUP BY o.order_status
    ORDER BY o.order_status;
""")

for row in cursor.fetchall():
    print(row)

print("\n" + "=" * 60)
print("7. INVESTIGATING OPEN ORDERS")
print("=" * 60)

cursor.execute("""
    SELECT
        o.order_status,
        COUNT(DISTINCT o.order_id) AS orders,
        COUNT(DISTINCT d.delivery_id) AS deliveries,
        SUM(ol.ordered_qty) AS ordered_qty,
        SUM(ol.delivered_qty) AS delivered_qty
    FROM orders o
    LEFT JOIN order_lines ol
        ON o.order_id = ol.order_id
    LEFT JOIN deliveries d
        ON o.order_id = d.order_id
    WHERE o.order_status = 'OPEN'
    GROUP BY o.order_status;
""")

for row in cursor.fetchall():
    print(row)


print("\nSample OPEN orders:")

cursor.execute("""
    SELECT
        o.order_id,
        o.order_date,
        o.requested_delivery_date,
        o.order_status,
        d.delivery_status,
        d.planned_arrival,
        d.actual_arrival,
        d.delay_minutes
    FROM orders o
    LEFT JOIN deliveries d
        ON o.order_id = d.order_id
    WHERE o.order_status = 'OPEN'
    LIMIT 10;
""")

for row in cursor.fetchall():
    print(row)


print("\n" + "=" * 60)
print("8. QUANTITY DATA QUALITY")
print("=" * 60)

# Missing or invalid case packs
cursor.execute("""
    SELECT
        COUNT(*) AS case_lines,
        SUM(
            CASE
                WHEN case_pack_at_order IS NULL
                  OR case_pack_at_order <= 0
                THEN 1
                ELSE 0
            END
        ) AS invalid_case_packs
    FROM order_lines
    WHERE qty_uom = 'CASE';
""")

print("CASE lines / invalid case packs:")
print(cursor.fetchone())


# Negative quantities
cursor.execute("""
    SELECT COUNT(*)
    FROM order_lines
    WHERE ordered_qty < 0
       OR delivered_qty < 0;
""")

print("Lines with negative quantities:")
print(cursor.fetchone()[0])


# Delivered greater than ordered
cursor.execute("""
    SELECT COUNT(*)
    FROM order_lines
    WHERE delivered_qty > ordered_qty;
""")

print("Lines where delivered > ordered:")
print(cursor.fetchone()[0])

connection.close()