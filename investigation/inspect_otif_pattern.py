import sqlite3


DB_PATH = "data/kestrel_ops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


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
    order_status,
    COUNT(*) AS order_count,
    SUM(ordered_eaches) AS ordered_eaches,
    SUM(delivered_eaches) AS delivered_eaches,

    SUM(
        CASE
            WHEN delivered_eaches >= ordered_eaches
                THEN 1
            ELSE 0
        END
    ) AS in_full_orders

FROM order_quantities

GROUP BY order_status

ORDER BY order_status;
"""


cursor.execute(query)

results = cursor.fetchall()


print("Corrected OTIF Pattern")
print("=" * 90)

for row in results:

    status = row[0]
    order_count = row[1]
    ordered = row[2]
    delivered = row[3]
    in_full = row[4]

    fill_rate = delivered / ordered * 100

    print(
        f"{status:<12} "
        f"Orders: {order_count:>8,}  "
        f"Ordered: {ordered:>12,.0f}  "
        f"Delivered: {delivered:>12,.0f}  "
        f"In-full: {in_full:>6,}  "
        f"Fill: {fill_rate:>6.2f}%"
    )


# Overall OTIF

query2 = """
WITH order_quantities AS (

    SELECT
        o.order_id,
        o.requested_delivery_date,

        MAX(d.actual_arrival) AS actual_arrival,

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

    JOIN deliveries d
        ON o.order_id = d.order_id

    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')

    GROUP BY
        o.order_id,
        o.requested_delivery_date
)

SELECT
    COUNT(*) AS eligible_orders,

    SUM(
        CASE
            WHEN DATE(actual_arrival) <= DATE(requested_delivery_date)
            THEN 1
            ELSE 0
        END
    ) AS on_time_orders,

    SUM(
        CASE
            WHEN delivered_eaches >= ordered_eaches
            THEN 1
            ELSE 0
        END
    ) AS in_full_orders,

    SUM(
        CASE
            WHEN DATE(actual_arrival) <= DATE(requested_delivery_date)
             AND delivered_eaches >= ordered_eaches
            THEN 1
            ELSE 0
        END
    ) AS otif_orders

FROM order_quantities;
"""


cursor.execute(query2)

result = cursor.fetchone()


eligible = result[0]
on_time = result[1]
in_full = result[2]
otif = result[3]


print()
print("Overall OTIF")
print("=" * 90)

print(f"Eligible orders: {eligible:,}")
print(f"On-time orders:  {on_time:,}")
print(f"In-full orders:  {in_full:,}")
print(f"OTIF orders:     {otif:,}")

print()

print(f"On-time rate: {on_time / eligible * 100:.2f}%")
print(f"In-full rate: {in_full / eligible * 100:.2f}%")
print(f"OTIF rate:    {otif / eligible * 100:.2f}%")


connection.close()