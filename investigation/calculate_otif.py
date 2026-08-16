import sqlite3

DB_PATH = "data/kestrel_ops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


query = """
WITH order_quantities AS (

    SELECT
        o.order_id,
        o.requested_delivery_date,
        o.order_status,
        d.actual_arrival,

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

    JOIN deliveries d
        ON o.order_id = d.order_id

    JOIN order_lines ol
        ON o.order_id = ol.order_id

    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')

    GROUP BY
        o.order_id,
        o.requested_delivery_date,
        o.order_status,
        d.actual_arrival
),

otif_classification AS (

    SELECT
        order_id,

        CASE
            WHEN DATE(actual_arrival)
                 <= DATE(requested_delivery_date)
            THEN 1
            ELSE 0
        END AS is_on_time,

        CASE
            WHEN delivered_eaches = ordered_eaches
            THEN 1
            ELSE 0
        END AS is_in_full

    FROM order_quantities
)

SELECT

    COUNT(*) AS total_orders,

    SUM(is_on_time) AS on_time_orders,

    SUM(is_in_full) AS in_full_orders,

    SUM(
        CASE
            WHEN is_on_time = 1
             AND is_in_full = 1
            THEN 1
            ELSE 0
        END
    ) AS otif_orders

FROM otif_classification;
"""


cursor.execute(query)

result = cursor.fetchone()

total_orders = result[0]
on_time_orders = result[1]
in_full_orders = result[2]
otif_orders = result[3]


print("\nOTIF Calculation")
print("-" * 60)

print(f"Total eligible orders: {total_orders:,}")
print(f"On-time orders:        {on_time_orders:,}")
print(f"In-full orders:        {in_full_orders:,}")
print(f"OTIF orders:           {otif_orders:,}")

print()

print(
    f"On-time rate:  "
    f"{on_time_orders / total_orders * 100:.2f}%"
)

print(
    f"In-full rate:  "
    f"{in_full_orders / total_orders * 100:.2f}%"
)

print(
    f"OTIF rate:     "
    f"{otif_orders / total_orders * 100:.2f}%"
)


connection.close()