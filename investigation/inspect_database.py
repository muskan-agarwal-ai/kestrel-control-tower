import sqlite3

DB_PATH = "data/kestrel_ops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# Get all table names
cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name;
""")

tables = cursor.fetchall()

for table in tables:
    table_name = table[0]

    print("\n" + "=" * 60)
    print(f"TABLE: {table_name}")
    print("=" * 60)

    # Count rows
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]

    print(f"Rows: {row_count:,}")

    # Get column information
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    print("\nColumns:")

    for column in columns:
        column_id = column[0]
        column_name = column[1]
        data_type = column[2]

        print(f"  - {column_name} ({data_type})")

connection.close()