import sqlite3

DB_PATH = "data/kestrel_ops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


print("\nTemperature Excursions by Reefer Flag")
print("-" * 70)

cursor.execute("""
SELECT
    r.is_reefer,
    COUNT(*) AS deliveries,
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

WHERE DATE(d.dispatch_datetime)
      BETWEEN DATE('2025-01-01')
      AND DATE('2026-06-30')

GROUP BY r.is_reefer
ORDER BY r.is_reefer;
""")

for row in cursor.fetchall():
    print(row)


print("\nNon-Reefer Deliveries With Temperature Excursions")
print("-" * 70)

cursor.execute("""
SELECT
    d.delivery_id,
    d.order_id,
    d.route_id,
    r.route_name,
    r.is_reefer,
    d.temperature_excursion_flag,
    d.max_temp_celsius

FROM deliveries d

JOIN routes r
    ON d.route_id = r.route_id

WHERE r.is_reefer = 0
  AND d.temperature_excursion_flag = 1
  AND DATE(d.dispatch_datetime)
      BETWEEN DATE('2025-01-01')
      AND DATE('2026-06-30')

LIMIT 20;
""")

for row in cursor.fetchall():
    print(row)


print("\nTemperature Excursions by Route Type")
print("-" * 70)

cursor.execute("""
SELECT
    r.vehicle_type,
    r.is_reefer,
    COUNT(*) AS deliveries,
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

WHERE DATE(d.dispatch_datetime)
      BETWEEN DATE('2025-01-01')
      AND DATE('2026-06-30')

GROUP BY
    r.vehicle_type,
    r.is_reefer

ORDER BY excursions DESC;
""")

for row in cursor.fetchall():
    print(row)


connection.close()