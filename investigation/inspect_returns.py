import sqlite3

DB_PATH = "data/kestrel_ops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


print("\nReturns Overview")
print("-" * 70)

cursor.execute("""
SELECT
    COUNT(*) AS return_lines,
    SUM(ABS(return_qty)) AS returned_quantity,
    SUM(ABS(credit_note_value_inr)) AS credit_note_value

FROM returns_credit_notes;
""")

print(cursor.fetchone())


print("\nReturns by Reason")
print("-" * 70)

cursor.execute("""
SELECT

    return_reason_code,

    COUNT(*) AS return_lines,

    SUM(ABS(return_qty)) AS returned_quantity,

    SUM(ABS(credit_note_value_inr)) AS credit_note_value

FROM returns_credit_notes

GROUP BY return_reason_code

ORDER BY credit_note_value DESC;
""")

for row in cursor.fetchall():
    print(row)


print("\nReturns by Product Category")
print("-" * 70)

cursor.execute("""
SELECT

    p.category,

    COUNT(*) AS return_lines,

    SUM(ABS(r.return_qty)) AS returned_quantity,

    SUM(ABS(r.credit_note_value_inr)) AS credit_note_value

FROM returns_credit_notes r

JOIN products p
    ON r.product_id = p.product_id

GROUP BY p.category

ORDER BY credit_note_value DESC;
""")


for row in cursor.fetchall():
    print(row)


print("\nReturns by Category and Reason")
print("-" * 70)

cursor.execute("""
SELECT

    p.category,

    r.return_reason_code,

    SUM(ABS(r.credit_note_value_inr)) AS credit_note_value

FROM returns_credit_notes r

JOIN products p
    ON r.product_id = p.product_id

GROUP BY
    p.category,
    r.return_reason_code

ORDER BY
    p.category,
    credit_note_value DESC;
""")

for row in cursor.fetchall():
    print(row)


connection.close()