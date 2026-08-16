import sqlite3

DB_PATH = "data/kestrel_ops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


query = """
WITH order_quantities AS (

    SELECT
        o.order_id,

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

    GROUP BY o.order_id
),

order_fill AS (

    SELECT
        order_id,
        delivered_eaches * 1.0 / ordered_eaches AS fill_rate

    FROM order_quantities
)

SELECT

    CASE

        WHEN fill_rate >= 0.99
            THEN '99% - 100%'

        WHEN fill_rate >= 0.95
            THEN '95% - 99%'

        WHEN fill_rate >= 0.90
            THEN '90% - 95%'

        WHEN fill_rate >= 0.80
            THEN '80% - 90%'

        ELSE
            '<80%'

    END AS fill_bucket,

    COUNT(*) AS orders

FROM order_fill

GROUP BY fill_bucket

ORDER BY
    CASE fill_bucket
        WHEN '99% - 100%' THEN 1
        WHEN '95% - 99%' THEN 2
        WHEN '90% - 95%' THEN 3
        WHEN '80% - 90%' THEN 4
        ELSE 5
    END;
"""


cursor.execute(query)

print("\nOrder-Level Fill Rate Distribution")
print("-" * 60)

for row in cursor.fetchall():
    print(row)


connection.close()