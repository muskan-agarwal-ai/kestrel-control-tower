import sqlite3

DB_PATH = "data/kestrel_ops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


# ---------------------------------------------------------
# 1. Check delivery dates outside the stated data range
# ---------------------------------------------------------

print("\nDeliveries after 30 June 2026")
print("-" * 70)

cursor.execute("""
SELECT
    COUNT(*) AS deliveries_after_range,
    MIN(dispatch_datetime),
    MAX(dispatch_datetime)

FROM deliveries

WHERE DATE(dispatch_datetime) > DATE('2026-06-30');
""")

print(cursor.fetchone())


print("\nJuly 2026 deliveries")
print("-" * 70)

cursor.execute("""
SELECT
    d.delivery_id,
    d.order_id,
    d.dispatch_datetime,
    d.delivery_status,
    r.is_reefer,
    d.temperature_excursion_flag

FROM deliveries d

JOIN routes r
    ON d.route_id = r.route_id

WHERE DATE(d.dispatch_datetime) >= DATE('2026-07-01')

ORDER BY d.dispatch_datetime

LIMIT 10;
""")

for row in cursor.fetchall():
    print(row)


# ---------------------------------------------------------
# 2. Check return reason codes
# ---------------------------------------------------------

print("\nReturn Reason Codes")
print("-" * 70)

cursor.execute("""
SELECT
    return_reason_code,
    COUNT(*) AS return_lines,
    SUM(ABS(return_qty)) AS returned_quantity,
    SUM(ABS(credit_note_value_inr)) AS credit_value

FROM returns_credit_notes

GROUP BY return_reason_code

ORDER BY return_lines DESC;
""")

for row in cursor.fetchall():
    print(row)


# ---------------------------------------------------------
# 3. Check whether RT06 exists at all
# ---------------------------------------------------------

print("\nRT06 Cold Chain Returns")
print("-" * 70)

cursor.execute("""
SELECT *
FROM returns_credit_notes
WHERE return_reason_code = 'RT06'
LIMIT 10;
""")

rows = cursor.fetchall()

if rows:
    for row in rows:
        print(row)
else:
    print("No RT06 records found.")


# ---------------------------------------------------------
# 4. Compare temperature excursions with returns
# ---------------------------------------------------------

print("\nTemperature Excursions vs Cold Chain Returns")
print("-" * 70)

cursor.execute("""
SELECT

    SUM(
        CASE
            WHEN temperature_excursion_flag = 1
            THEN 1
            ELSE 0
        END
    ) AS temperature_excursions,

    COUNT(*) AS total_deliveries

FROM deliveries;
""")

print(cursor.fetchone())


connection.close()