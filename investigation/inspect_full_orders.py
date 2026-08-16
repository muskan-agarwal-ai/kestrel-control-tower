import sqlite3

DB_PATH = "data/kestrel_ops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


print("\nOrder-level quantity comparison")
print("-" * 70)

query = """
WITH order_quantities AS (

    SELECT
        o.order_id,
        o.order_status,

        SUM(
            CASE
                WHEN ol.qty_uom = 'CASE'
                    THEN ol.ordered_qty * ol.case_pack_at_order
                ELSE ol.ordered_qty
            END
        ) AS ordered_eaches,

        SUM(
            CASE
                WHEN ol.qty_uom = 'CASE'
                    THEN ol.delivered_qty * ol.case_pack_at_order
                ELSE ol.delivered_qty
            END
        ) AS delivered_eaches

    FROM orders o

    JOIN order_lines ol
        ON o.order_id = ol.order_id

    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')

    GROUP BY
        o.order_id,
        o.order_status
)

SELECT

    COUNT(*) AS total_orders,

    SUM(
        CASE
            WHEN delivered_eaches = ordered_eaches
            THEN 1
            ELSE 0
        END
    ) AS completely_full_orders,

    SUM(
        CASE
            WHEN delivered_eaches < ordered_eaches
            THEN 1
            ELSE 0
        END
    ) AS partially_fulfilled_orders,

    MIN(
        ordered_eaches - delivered_eaches
    ) AS smallest_shortfall,

    MAX(
        ordered_eaches - delivered_eaches
    ) AS largest_shortfall

FROM order_quantities;
"""

cursor.execute(query)

result = cursor.fetchone()

print(f"Total orders:             {result[0]:,}")
print(f"Completely full orders:   {result[1]:,}")
print(f"Partially fulfilled:      {result[2]:,}")
print(f"Smallest shortfall:       {result[3]:,.0f}")
print(f"Largest shortfall:        {result[4]:,.0f}")


print("\nSample orders closest to being full")
print("-" * 70)

cursor.execute("""
WITH order_quantities AS (

    SELECT
        o.order_id,
        o.order_status,

        SUM(
            CASE
                WHEN ol.qty_uom = 'CASE'
                    THEN ol.ordered_qty * ol.case_pack_at_order
                ELSE ol.ordered_qty
            END
        ) AS ordered_eaches,

        SUM(
            CASE
                WHEN ol.qty_uom = 'CASE'
                    THEN ol.delivered_qty * ol.case_pack_at_order
                ELSE ol.delivered_qty
            END
        ) AS delivered_eaches

    FROM orders o

    JOIN order_lines ol
        ON o.order_id = ol.order_id

    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')

    GROUP BY
        o.order_id,
        o.order_status
)

SELECT
    order_id,
    order_status,
    ordered_eaches,
    delivered_eaches,
    ordered_eaches - delivered_eaches AS shortfall

FROM order_quantities

ORDER BY shortfall ASC

LIMIT 10;
""")

for row in cursor.fetchall():
    print(row)


connection.close()