import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent)
)

import sqlite3

from integrations.freight_api import fetch_all_invoices


DB_PATH = "data/kestrel_ops.db"


def get_q1_delivered_cases():

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            w.warehouse_code,
            w.warehouse_name,

            SUM(
                CASE
                    WHEN ol.qty_uom = 'CASE'
                        THEN ol.delivered_qty
                    ELSE
                        ol.delivered_qty * 1.0
                        / ol.case_pack_at_order
                END
            ) AS delivered_cases

        FROM order_lines ol

        JOIN orders o
            ON ol.order_id = o.order_id

        JOIN warehouses w
            ON o.warehouse_id = w.warehouse_id

        WHERE
            o.order_status IN ('DELIVERED', 'PARTIAL')
            AND o.order_date >= '2026-04-01'
            AND o.order_date <= '2026-06-30'

        GROUP BY
            w.warehouse_code,
            w.warehouse_name

        ORDER BY
            delivered_cases DESC;
    """)

    rows = cursor.fetchall()

    connection.close()

    return rows


def main():

    print("Fetching freight invoices...")

    invoices = fetch_all_invoices(
        date_from="2026-04-01",
        date_to="2026-06-30"
    )

    print(
        f"Total Q1 freight invoices: "
        f"{len(invoices):,}"
    )

    delivered_cases = get_q1_delivered_cases()

    freight_by_warehouse = {}

    for invoice in invoices:

        warehouse_code = invoice["warehouse_code"]

        amount_inr = invoice["amount_inr"]

        freight_by_warehouse.setdefault(
            warehouse_code,
            0
        )

        freight_by_warehouse[warehouse_code] += amount_inr

    print("\nQ1 FY2027 Freight Metrics")
    print("=" * 90)

    for warehouse_code, warehouse_name, cases in delivered_cases:

        freight = freight_by_warehouse.get(
            warehouse_code,
            0
        )

        cost_per_case = (
            freight / cases
            if cases
            else 0
        )

        print(
            f"{warehouse_name:25}"
            f" Freight: ₹{freight:,.2f}"
            f" Delivered cases: {cases:,.0f}"
            f" Cost/case: ₹{cost_per_case:.2f}"
        )


if __name__ == "__main__":
    main()