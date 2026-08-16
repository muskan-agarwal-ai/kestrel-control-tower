import sqlite3


DB_PATH = "data/kestrel_ops.db"


def fill_rate_by_region():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    query = """
        SELECT
            r.region_name,

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

        FROM order_lines ol

        JOIN orders o
            ON ol.order_id = o.order_id

        JOIN regions r
            ON o.region_id = r.region_id

        WHERE o.order_status IN ('DELIVERED', 'PARTIAL')

        GROUP BY r.region_name

        ORDER BY
            delivered_eaches * 1.0 / ordered_eaches;
    """

    cursor.execute(query)

    results = cursor.fetchall()

    connection.close()

    return results
def fill_rate_by_month():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    query = """
        SELECT
            SUBSTR(o.order_date, 1, 7) AS month,

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

        FROM order_lines ol

        JOIN orders o
            ON ol.order_id = o.order_id

        WHERE o.order_status IN ('DELIVERED', 'PARTIAL')

        GROUP BY SUBSTR(o.order_date, 1, 7)

        ORDER BY month;
    """

    cursor.execute(query)

    results = cursor.fetchall()

    connection.close()

    return results
def fill_rate_by_region_month(region_name):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    query = """
        SELECT
            SUBSTR(o.order_date, 1, 7) AS month,

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

        FROM order_lines ol

        JOIN orders o
            ON ol.order_id = o.order_id

        JOIN regions r
            ON o.region_id = r.region_id

        WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
          AND r.region_name = ?

        GROUP BY SUBSTR(o.order_date, 1, 7)

        ORDER BY month;
    """

    cursor.execute(query, (region_name,))

    results = cursor.fetchall()

    connection.close()

    return results


def fill_rate_by_warehouse():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    query = """
        SELECT
            w.warehouse_name,

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

        FROM order_lines ol

        JOIN orders o
            ON ol.order_id = o.order_id

        JOIN warehouses w
            ON o.warehouse_id = w.warehouse_id

        WHERE o.order_status IN ('DELIVERED', 'PARTIAL')

        GROUP BY w.warehouse_name

        ORDER BY
            delivered_eaches * 1.0 / ordered_eaches;
    """

    cursor.execute(query)

    results = cursor.fetchall()

    connection.close()

    return results

results = fill_rate_by_region()

print("\nFill Rate by Region")
print("-" * 60)

for region, ordered, delivered in results:

    fill_rate = delivered / ordered * 100

    print(
        f"{region:<15}"
        f"Ordered: {ordered:>15,.0f}  "
        f"Delivered: {delivered:>15,.0f}  "
        f"Fill Rate: {fill_rate:>6.2f}%"
    )

print("\n\nFill Rate by Month")
print("-" * 60)

monthly_results = fill_rate_by_month()

for month, ordered, delivered in monthly_results:

    fill_rate = delivered / ordered * 100

    print(
        f"{month}   "
        f"Ordered: {ordered:>15,.0f}  "
        f"Delivered: {delivered:>15,.0f}  "
        f"Fill Rate: {fill_rate:>6.2f}%"
    )

print("\n\nWest Fill Rate by Month")
print("-" * 60)

west_results = fill_rate_by_region_month("West")

for month, ordered, delivered in west_results:

    fill_rate = delivered / ordered * 100

    print(
        f"{month}   "
        f"Ordered: {ordered:>15,.0f}  "
        f"Delivered: {delivered:>15,.0f}  "
        f"Fill Rate: {fill_rate:>6.2f}%"
    )

print("\n\nData Date Range")
print("-" * 60)

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute("""
    SELECT
        MIN(order_date),
        MAX(order_date)
    FROM orders;
""")

min_date, max_date = cursor.fetchone()

print(f"First order date: {min_date}")
print(f"Last order date:  {max_date}")

print("\n\nWest Fill Rate - Recent Weeks")
print("-" * 70)

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

query = """
    SELECT
        date(
            o.order_date,
            '-' || (
                (CAST(strftime('%w', o.order_date) AS INTEGER) + 6) % 7
            ) || ' days'
        ) AS week_start,

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

    FROM order_lines ol

    JOIN orders o
        ON ol.order_id = o.order_id

    JOIN regions r
        ON o.region_id = r.region_id

    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
      AND r.region_name = 'West'
      AND o.order_date >= date(
            (SELECT MAX(order_date) FROM orders),
            '-41 days'
      )

    GROUP BY week_start

    ORDER BY week_start;
"""

cursor.execute(query)

weekly_results = cursor.fetchall()

for week_start, ordered, delivered in weekly_results:

    fill_rate = delivered / ordered * 100

    print(
        f"Week starting {week_start}   "
        f"Ordered: {ordered:>12,.0f}   "
        f"Delivered: {delivered:>12,.0f}   "
        f"Fill Rate: {fill_rate:>6.2f}%"
    )



print("\n\nFill Rate by Warehouse")
print("-" * 70)

warehouse_results = fill_rate_by_warehouse()

for warehouse, ordered, delivered in warehouse_results:

    fill_rate = delivered / ordered * 100

    print(
        f"{warehouse:<25}"
        f"Ordered: {ordered:>14,.0f}   "
        f"Delivered: {delivered:>14,.0f}   "
        f"Fill Rate: {fill_rate:>6.2f}%"
    )

print("\n\nShort Reasons for Unfulfilled Quantity")
print("-" * 70)

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

query = """
    SELECT
        COALESCE(ol.short_reason_code, 'NO_REASON') AS reason,

        COUNT(*) AS lines,

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

    FROM order_lines ol

    JOIN orders o
        ON ol.order_id = o.order_id

    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')

    GROUP BY COALESCE(ol.short_reason_code, 'NO_REASON')

    ORDER BY
        (ordered_eaches - delivered_eaches) DESC;
"""

cursor.execute(query)

results = cursor.fetchall()

for reason, lines, ordered, delivered in results:

    short_eaches = ordered - delivered

    print(
        f"{reason:<25}"
        f"Lines: {lines:>8,}   "
        f"Ordered: {ordered:>14,.0f}   "
        f"Delivered: {delivered:>14,.0f}   "
        f"Short: {short_eaches:>14,.0f}"
    )

print("\n\nShort Reasons by Region")
print("-" * 80)

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

query = """
    SELECT
        r.region_name,
        ol.short_reason_code,

        SUM(
            CASE
                WHEN ol.qty_uom = 'CASE'
                    THEN (ol.ordered_qty - ol.delivered_qty)
                         * ol.case_pack_at_order
                ELSE
                    (ol.ordered_qty - ol.delivered_qty)
            END
        ) AS short_eaches

    FROM order_lines ol

    JOIN orders o
        ON ol.order_id = o.order_id

    JOIN regions r
        ON o.region_id = r.region_id

    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
      AND ol.short_reason_code IS NOT NULL

    GROUP BY
        r.region_name,
        ol.short_reason_code

    ORDER BY
        r.region_name,
        short_eaches DESC;
"""

cursor.execute(query)

results = cursor.fetchall()

current_region = None

for region, reason, short_eaches in results:

    if region != current_region:
        print(f"\n{region}")
        print("-" * 40)
        current_region = region

    print(
        f"{reason:<25}"
        f"{short_eaches:>14,.0f} eaches"
    )

print("\n\nShort Reason Mix by Region")
print("-" * 80)

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

query = """
    SELECT
        r.region_name,
        ol.short_reason_code,

        SUM(
            CASE
                WHEN ol.qty_uom = 'CASE'
                    THEN (ol.ordered_qty - ol.delivered_qty)
                         * ol.case_pack_at_order
                ELSE
                    (ol.ordered_qty - ol.delivered_qty)
            END
        ) AS short_eaches

    FROM order_lines ol

    JOIN orders o
        ON ol.order_id = o.order_id

    JOIN regions r
        ON o.region_id = r.region_id

    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
      AND ol.short_reason_code IS NOT NULL

    GROUP BY
        r.region_name,
        ol.short_reason_code

    ORDER BY
        r.region_name,
        short_eaches DESC;
"""

cursor.execute(query)

results = cursor.fetchall()

# Calculate total short quantity for each region
region_totals = {}

for region, reason, short_eaches in results:
    region_totals[region] = (
        region_totals.get(region, 0) + short_eaches
    )

current_region = None

for region, reason, short_eaches in results:

    if region != current_region:
        print(f"\n{region}")
        print("-" * 40)
        current_region = region

    percentage = (
        short_eaches / region_totals[region] * 100
    )

    print(
        f"{reason:<25}"
        f"{short_eaches:>12,.0f} eaches   "
        f"{percentage:>6.2f}%"
    )

print("\n\nTop Products by Unfulfilled Quantity")
print("-" * 100)

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

query = """
    SELECT
        p.product_id,
        p.sku_code,
        p.product_name,
        p.brand,

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

    FROM order_lines ol

    JOIN orders o
        ON ol.order_id = o.order_id

    JOIN products p
        ON ol.product_id = p.product_id

    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')

    GROUP BY
        p.product_id,
        p.sku_code,
        p.product_name,
        p.brand

    ORDER BY
        (ordered_eaches - delivered_eaches) DESC

    LIMIT 20;
"""

cursor.execute(query)

results = cursor.fetchall()

for (
    product_id,
    sku_code,
    product_name,
    brand,
    ordered,
    delivered
) in results:

    short = ordered - delivered

    fill_rate = delivered / ordered * 100

    print(
        f"{sku_code:<12}"
        f"{product_name[:30]:<32}"
        f"Ordered: {ordered:>12,.0f}   "
        f"Delivered: {delivered:>12,.0f}   "
        f"Short: {short:>12,.0f}   "
        f"Fill: {fill_rate:>6.2f}%"
    )

print("\n\nLowest Fill Rate Products")
print("-" * 100)

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

query = """
    SELECT
        p.sku_code,
        p.product_name,

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

    FROM order_lines ol

    JOIN orders o
        ON ol.order_id = o.order_id

    JOIN products p
        ON ol.product_id = p.product_id

    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')

    GROUP BY
        p.product_id,
        p.sku_code,
        p.product_name

    HAVING ordered_eaches >= 100000

    ORDER BY
        delivered_eaches * 1.0 / ordered_eaches

    LIMIT 20;
"""

cursor.execute(query)

results = cursor.fetchall()

for sku, product_name, ordered, delivered in results:

    fill_rate = delivered / ordered * 100
    short = ordered - delivered

    print(
        f"{sku:<12}"
        f"{product_name[:35]:<37}"
        f"Ordered: {ordered:>12,.0f}   "
        f"Delivered: {delivered:>12,.0f}   "
        f"Short: {short:>12,.0f}   "
        f"Fill: {fill_rate:>6.2f}%"
    )

print("\n\nShort Reasons for Top 20 Lowest-Fill Products")
print("-" * 100)

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

query = """
    WITH product_metrics AS (

        SELECT
            p.product_id,
            p.sku_code,
            p.product_name,

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

        FROM order_lines ol

        JOIN orders o
            ON ol.order_id = o.order_id

        JOIN products p
            ON ol.product_id = p.product_id

        WHERE o.order_status IN ('DELIVERED', 'PARTIAL')

        GROUP BY
            p.product_id,
            p.sku_code,
            p.product_name

        HAVING ordered_eaches >= 100000
    ),

    worst_products AS (

        SELECT
            product_id,
            sku_code,
            product_name
        FROM product_metrics
        ORDER BY
            delivered_eaches * 1.0 / ordered_eaches
        LIMIT 20
    )

    SELECT
        wp.sku_code,
        wp.product_name,
        ol.short_reason_code,

        SUM(
            CASE
                WHEN ol.qty_uom = 'CASE'
                    THEN (ol.ordered_qty - ol.delivered_qty)
                         * ol.case_pack_at_order
                ELSE
                    (ol.ordered_qty - ol.delivered_qty)
            END
        ) AS short_eaches

    FROM order_lines ol

    JOIN orders o
        ON ol.order_id = o.order_id

    JOIN worst_products wp
        ON ol.product_id = wp.product_id

    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
      AND ol.short_reason_code IS NOT NULL

    GROUP BY
        wp.sku_code,
        wp.product_name,
        ol.short_reason_code

    ORDER BY
        wp.sku_code,
        short_eaches DESC;
"""

cursor.execute(query)

results = cursor.fetchall()

current_sku = None
product_total = 0
product_rows = []


def print_product_rows(rows, total):

    if not rows:
        return

    for sku, product_name, reason, short_eaches in rows:

        percentage = short_eaches / total * 100

        print(
            f"{sku:<12}"
            f"{product_name[:30]:<32}"
            f"{reason:<25}"
            f"{short_eaches:>12,.0f} eaches   "
            f"{percentage:>6.2f}%"
        )


for sku, product_name, reason, short_eaches in results:

    if sku != current_sku:

        print_product_rows(
            product_rows,
            product_total
        )

        if current_sku is not None:
            print()

        current_sku = sku
        product_total = 0
        product_rows = []

    product_total += short_eaches

    product_rows.append(
        (sku, product_name, reason, short_eaches)
    )


print_product_rows(
    product_rows,
    product_total
)




connection.close()