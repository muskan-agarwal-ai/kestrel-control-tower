import sqlite3

DB_PATH = "data/kestrel_ops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

print("\nTop 20 SKUs by Sales Value")
print("=" * 100)

cursor.execute("""
SELECT
    p.sku_code,
    p.product_name,
    p.category,
    SUM(ol.delivered_qty) AS delivered_qty,
    SUM(ol.line_value_inr) AS sales_value,
    p.list_price_inr,
    p.mrp_inr
FROM order_lines ol

JOIN products p
    ON ol.product_id = p.product_id

JOIN orders o
    ON ol.order_id = o.order_id

WHERE
    o.order_status IN ('DELIVERED', 'PARTIAL')
    AND o.order_date >= '2026-04-01'
    AND o.order_date <= '2026-06-30'

GROUP BY
    p.product_id,
    p.sku_code,
    p.product_name,
    p.category,
    p.list_price_inr,
    p.mrp_inr

ORDER BY
    sales_value DESC

LIMIT 20;
""")

rows = cursor.fetchall()

for i, row in enumerate(rows, 1):

    sku, name, category, qty, value, list_price, mrp = row

    print(
        f"{i:2}. {sku:10} "
        f"{name:40} "
        f"Value: ₹{value:,.2f} "
        f"List: ₹{list_price:,.2f} "
        f"MRP: ₹{mrp:,.2f}"
    )

connection.close()