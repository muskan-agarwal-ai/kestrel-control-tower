import sqlite3

DB_PATH = "data/kestrel_ops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


print("\nCold Chain Delivery Overview")
print("-" * 70)

cursor.execute("""
SELECT
    COUNT(*) AS total_deliveries,
    SUM(
        CASE
            WHEN r.is_reefer = 1
            THEN 1
            ELSE 0
        END
    ) AS reefer_deliveries,
    SUM(
        CASE
            WHEN r.is_reefer = 1
             AND d.temperature_excursion_flag = 1
            THEN 1
            ELSE 0
        END
    ) AS reefer_excursions

FROM deliveries d

JOIN routes r
    ON d.route_id = r.route_id;
""")

print(cursor.fetchone())


print("\nTemperature Excursions by Month")
print("-" * 70)

cursor.execute("""
SELECT
    SUBSTR(d.dispatch_datetime, 1, 7) AS month,

    COUNT(*) AS reefer_deliveries,

    SUM(
        CASE
            WHEN d.temperature_excursion_flag = 1
            THEN 1
            ELSE 0
        END
    ) AS excursions

FROM deliveries d

JOIN routes r
    ON d.route_id = r.route_id

WHERE r.is_reefer = 1

GROUP BY month

ORDER BY month;
""")

for row in cursor.fetchall():
    print(row)


print("\nCold Chain Returns")
print("-" * 70)

cursor.execute("""
SELECT
    COUNT(*) AS return_lines,
    SUM(ABS(return_qty)) AS returned_quantity,
    SUM(ABS(credit_note_value_inr)) AS credit_note_value

FROM returns_credit_notes

WHERE return_reason_code = 'RT06';
""")

print(cursor.fetchone())


connection.close()