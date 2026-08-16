import sqlite3


DB_PATH = "data/kestrel_ops.db"


def calculate_fill_rate():
    """
    Calculate overall fill rate using individual units (eaches).

    CASE quantities are converted to eaches using
    case_pack_at_order.
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    query = """
        SELECT
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

        JOIN outlets ot
            ON o.outlet_id = ot.outlet_id

        WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
          AND ot.status = 'ACTIVE'
          AND ot.is_deleted = 0
          AND ot.outlet_id NOT IN (721, 722, 723);
    """

    cursor.execute(query)

    result = cursor.fetchone()

    ordered_eaches = result[0]
    delivered_eaches = result[1]

    connection.close()

    fill_rate = delivered_eaches / ordered_eaches * 100

    return ordered_eaches, delivered_eaches, fill_rate


def calculate_fill_rate_by_region():
    """
    Calculate fill rate by region using individual units (eaches).
    """

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

        JOIN outlets ot
            ON o.outlet_id = ot.outlet_id

        WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
          AND ot.status = 'ACTIVE'
          AND ot.is_deleted = 0
          AND ot.outlet_id NOT IN (721, 722, 723)

        GROUP BY r.region_id, r.region_name

        ORDER BY r.region_name;
    """

    cursor.execute(query)

    results = cursor.fetchall()

    connection.close()

    region_metrics = []

    for row in results:
        region_name = row[0]
        ordered_eaches = row[1]
        delivered_eaches = row[2]

        fill_rate = delivered_eaches / ordered_eaches * 100

        region_metrics.append(
            {
                "region": region_name,
                "ordered_eaches": ordered_eaches,
                "delivered_eaches": delivered_eaches,
                "fill_rate": fill_rate,
            }
        )

    return region_metrics


def calculate_fill_rate_by_warehouse():
    """
    Calculate fill rate by warehouse using individual units (eaches).
    """

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

        JOIN outlets ot
            ON o.outlet_id = ot.outlet_id

        WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
          AND ot.status = 'ACTIVE'
          AND ot.is_deleted = 0
          AND ot.outlet_id NOT IN (721, 722, 723)

        GROUP BY w.warehouse_id, w.warehouse_name

        ORDER BY w.warehouse_name;
    """

    cursor.execute(query)

    results = cursor.fetchall()

    connection.close()

    warehouse_metrics = []

    for row in results:
        warehouse_name = row[0]
        ordered_eaches = row[1]
        delivered_eaches = row[2]

        fill_rate = delivered_eaches / ordered_eaches * 100

        warehouse_metrics.append(
            {
                "warehouse": warehouse_name,
                "ordered_eaches": ordered_eaches,
                "delivered_eaches": delivered_eaches,
                "fill_rate": fill_rate,
            }
        )

    return warehouse_metrics



def calculate_fill_rate_by_route():
    """
    Calculate fill rate by route using individual units (eaches).
    Results are sorted from worst to best fill rate.
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    query = """
        SELECT
            r.route_name,

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

        JOIN routes r
            ON o.route_id = r.route_id

        JOIN outlets ot
            ON o.outlet_id = ot.outlet_id

        WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
          AND ot.status = 'ACTIVE'
          AND ot.is_deleted = 0
          AND ot.outlet_id NOT IN (721, 722, 723)

        GROUP BY r.route_id, r.route_name

        ORDER BY
            delivered_eaches * 1.0 / ordered_eaches ASC;
    """

    cursor.execute(query)

    results = cursor.fetchall()

    connection.close()

    route_metrics = []

    for row in results:
        route_name = row[0]
        ordered_eaches = row[1]
        delivered_eaches = row[2]

        fill_rate = delivered_eaches / ordered_eaches * 100

        route_metrics.append(
            {
                "route": route_name,
                "ordered_eaches": ordered_eaches,
                "delivered_eaches": delivered_eaches,
                "fill_rate": fill_rate,
            }
        )

    return route_metrics



def calculate_fill_rate_by_outlet(start_date=None, end_date=None):
    """
    Calculate fill rate by operational outlet using individual units (eaches).

    Optional date filters:
        start_date = inclusive start date, e.g. "2026-06-01"
        end_date   = inclusive end date, e.g. "2026-06-30"

    Excludes:
        - CLOSED outlets
        - DELETED outlets
        - Known test/migration outlets
        - CANCELLED and OPEN orders
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    query = """
        SELECT
            ot.outlet_id,
            ot.outlet_code,
            ot.outlet_name,

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

        JOIN outlets ot
            ON o.outlet_id = ot.outlet_id

        WHERE o.order_status IN ('DELIVERED', 'PARTIAL')

          AND ot.status = 'ACTIVE'

          AND ot.is_deleted = 0

          AND ot.outlet_id NOT IN (721, 722, 723)
    """

    parameters = []

    if start_date:
        query += """
            AND o.order_date >= ?
        """
        parameters.append(start_date)

    if end_date:
        query += """
            AND o.order_date <= ?
        """
        parameters.append(end_date)

    query += """
        GROUP BY
            ot.outlet_id,
            ot.outlet_code,
            ot.outlet_name

        ORDER BY
            delivered_eaches * 1.0 / ordered_eaches ASC;
    """

    cursor.execute(query, parameters)

    results = cursor.fetchall()

    connection.close()

    outlet_metrics = []

    for row in results:
        outlet_id = row[0]
        outlet_code = row[1]
        outlet_name = row[2]
        ordered_eaches = row[3]
        delivered_eaches = row[4]

        fill_rate = delivered_eaches / ordered_eaches * 100

        outlet_metrics.append(
            {
                "outlet_id": outlet_id,
                "outlet_code": outlet_code,
                "outlet_name": outlet_name,
                "ordered_eaches": ordered_eaches,
                "delivered_eaches": delivered_eaches,
                "fill_rate": fill_rate,
            }
        )

    return outlet_metrics


def calculate_cold_chain_metrics():
    """
    Calculate cold-chain delivery metrics.

    Primary cold-chain KPI is based on reefer deliveries.

    Non-reefer deliveries with temperature excursion flags
    are treated as data-quality exceptions and reported separately.
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    query = """
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
                    WHEN d.temperature_excursion_flag = 1
                    THEN 1
                    ELSE 0
                END
            ) AS total_temperature_excursions,

            SUM(
                CASE
                    WHEN r.is_reefer = 1
                     AND d.temperature_excursion_flag = 1
                    THEN 1
                    ELSE 0
                END
            ) AS reefer_excursions,

            SUM(
                CASE
                    WHEN r.is_reefer = 0
                     AND d.temperature_excursion_flag = 1
                    THEN 1
                    ELSE 0
                END
            ) AS non_reefer_excursions

        FROM deliveries d

        JOIN routes r
            ON d.route_id = r.route_id;
    """

    cursor.execute(query)

    result = cursor.fetchone()

    connection.close()

    total_deliveries = result[0]
    reefer_deliveries = result[1]
    total_temperature_excursions = result[2]
    reefer_excursions = result[3]
    non_reefer_excursions = result[4]

    reefer_excursion_rate = (
        reefer_excursions / reefer_deliveries * 100
        if reefer_deliveries
        else 0
    )

    return {
        "total_deliveries": total_deliveries,
        "reefer_deliveries": reefer_deliveries,
        "total_temperature_excursions": total_temperature_excursions,
        "reefer_excursions": reefer_excursions,
        "non_reefer_excursions": non_reefer_excursions,
        "reefer_excursion_rate": reefer_excursion_rate,
    }


def calculate_near_expiry():
    """
    Near-expiry stock, as of the LATEST inventory snapshot only.

    Bug found and fixed: inventory_snapshots has 78 distinct snapshot_date
    values (roughly weekly snapshots over 18 months). The original query summed
    on_hand/available cases across ALL 78 snapshots with no date filter, adding
    the same physical inventory up to 78 times. Verified: unfiltered sum =
    6,819,874 available cases; latest-snapshot-only = 87,158. ~78x overstated.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    query = """
        SELECT
            COUNT(*) AS inventory_rows,
            SUM(on_hand_cases) AS on_hand_cases,
            SUM(available_cases) AS available_cases
        FROM inventory_snapshots
        WHERE
            expiry_date IS NOT NULL
            AND DATE(expiry_date) >= DATE(snapshot_date)
            AND DATE(expiry_date) <= DATE(snapshot_date, '+30 days')
            AND snapshot_date = (SELECT MAX(snapshot_date) FROM inventory_snapshots);
    """

    cursor.execute(query)
    result = cursor.fetchone()

    connection.close()

    return result[0], result[1], result[2]


def calculate_returns_metrics():
    """
    Calculate overall returns and credit-note value.
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) AS return_lines,
            COALESCE(SUM(return_qty), 0) AS return_qty,
            COALESCE(SUM(credit_note_value_inr), 0) AS return_value
        FROM returns_credit_notes;
    """)

    result = cursor.fetchone()

    connection.close()

    return {
        "return_lines": result[0],
        "return_qty": result[1],
        "return_value": result[2],
    }


def calculate_returns_by_reason():
    """
    Return value grouped by return reason.
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            return_reason_code,
            COUNT(*) AS return_lines,
            COALESCE(SUM(return_qty), 0) AS return_qty,
            COALESCE(SUM(credit_note_value_inr), 0) AS return_value
        FROM returns_credit_notes
        GROUP BY return_reason_code
        ORDER BY return_value DESC;
    """)

    results = cursor.fetchall()

    connection.close()

    return [
        {
            "reason": row[0],
            "return_lines": row[1],
            "return_qty": row[2],
            "return_value": row[3],
        }
        for row in results
    ]


def calculate_returns_by_category():
    """
    Illustrative question 3: which categories drive the largest value of
    returns, AND what is the leading reason code for each. The original
    version only answered the first half (category totals); this adds the
    leading reason per category using a window function, so the question is
    actually answered as asked, not just partially.
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT category, return_reason_code AS leading_reason,
               return_lines, return_value
        FROM (
            SELECT
                p.category,
                rc.return_reason_code,
                COUNT(*) AS return_lines,
                SUM(rc.credit_note_value_inr) AS return_value,
                ROW_NUMBER() OVER (
                    PARTITION BY p.category
                    ORDER BY SUM(rc.credit_note_value_inr) DESC
                ) AS rnk
            FROM returns_credit_notes rc
            JOIN products p ON rc.product_id = p.product_id
            GROUP BY p.category, rc.return_reason_code
        )
        WHERE rnk = 1
        ORDER BY return_value DESC;
    """)

    results = cursor.fetchall()

    connection.close()

    return [
        {
            "category": row[0],
            "leading_reason": row[1],
            "return_lines": row[2],
            "return_value": round(row[3], 2),
        }
        for row in results
    ]


def calculate_discontinued_sku_orders():
    """
    Illustrative question 8: which outlets ordered a discontinued SKU after
    its discontinuation date. Excludes closed/test/deleted outlets, same rule
    as everywhere else.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            ot.outlet_code, ot.outlet_name, ot.city,
            p.sku_code, p.product_name, p.discontinued_date,
            o.order_date, ol.ordered_qty, ol.qty_uom
        FROM order_lines ol
        JOIN orders o ON ol.order_id = o.order_id
        JOIN products p ON ol.product_id = p.product_id
        JOIN outlets ot ON o.outlet_id = ot.outlet_id
        WHERE p.discontinued_date IS NOT NULL
          AND o.order_date > p.discontinued_date
          AND ot.status = 'ACTIVE'
          AND ot.is_deleted = 0
          AND ot.outlet_id NOT IN (721, 722, 723)
        ORDER BY o.order_date DESC;
    """)

    results = cursor.fetchall()
    connection.close()

    return [
        {
            "outlet_code": row[0], "outlet_name": row[1], "city": row[2],
            "sku_code": row[3], "product_name": row[4], "discontinued_date": row[5],
            "order_date": row[6], "ordered_qty": row[7], "qty_uom": row[8],
        }
        for row in results
    ]


def calculate_excursions_by_month():
    """
    Illustrative question 4: temperature excursions per hundred chilled
    deliveries, by month. "Chilled deliveries" = deliveries of any order
    line for a product flagged is_chilled=1.

    Bug found and fixed: the original version joined deliveries down to
    order_lines to filter for chilled products, then summed
    temperature_excursion_flag directly on the joined result. Since a single
    delivery can have several chilled order lines, that join fans out one
    delivery into several rows, and summing the flag over those rows counts
    the same excursion multiple times. Verified directly: Jan 2025 reported
    194 excursions under the buggy version; the real, deduplicated count is
    89. The denominator (COUNT DISTINCT delivery_id) was already correct;
    only the numerator was affected. Fixed by reducing to one row per
    delivery (MAX(temperature_excursion_flag), which is 0/1 so MAX is
    equivalent to a boolean OR) before summing.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        WITH chilled_deliveries AS (
            SELECT
                d.delivery_id,
                SUBSTR(d.dispatch_datetime, 1, 7) AS month,
                MAX(d.temperature_excursion_flag) AS excursion
            FROM deliveries d
            JOIN orders o ON d.order_id = o.order_id
            JOIN order_lines ol ON o.order_id = ol.order_id
            JOIN products p ON ol.product_id = p.product_id
            WHERE p.is_chilled = 1
              AND d.dispatch_datetime IS NOT NULL
            GROUP BY d.delivery_id, SUBSTR(d.dispatch_datetime, 1, 7)
        )
        SELECT
            month,
            COUNT(*) AS chilled_deliveries,
            SUM(excursion) AS excursions
        FROM chilled_deliveries
        GROUP BY month
        ORDER BY month;
    """)

    results = cursor.fetchall()
    connection.close()

    output = []
    for month, chilled, excursions in results:
        rate = (excursions / chilled * 100) if chilled else 0
        output.append({
            "month": month,
            "chilled_deliveries": chilled,
            "excursions": excursions,
            "excursions_per_100": round(rate, 2),
        })
    return output


def calculate_late_routes(min_late_pct=10):
    """
    Illustrative question 5: routes where more than min_late_pct% of
    deliveries are more than 2 hours (120 min) late.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            r.route_code, r.route_name, w.warehouse_name,
            COUNT(*) AS total_deliveries,
            SUM(CASE WHEN d.delay_minutes > 120 THEN 1 ELSE 0 END) AS late_deliveries
        FROM deliveries d
        JOIN routes r ON d.route_id = r.route_id
        JOIN warehouses w ON d.warehouse_id = w.warehouse_id
        WHERE d.delay_minutes IS NOT NULL
        GROUP BY r.route_id, r.route_code, r.route_name, w.warehouse_name
        HAVING total_deliveries >= 10;
    """)

    results = cursor.fetchall()
    connection.close()

    output = []
    for route_code, route_name, warehouse_name, total, late in results:
        late_pct = late / total * 100 if total else 0
        if late_pct > min_late_pct:
            output.append({
                "route_code": route_code, "route_name": route_name,
                "warehouse_name": warehouse_name, "total_deliveries": total,
                "late_deliveries": late, "late_pct": round(late_pct, 1),
            })
    output.sort(key=lambda r: r["late_pct"], reverse=True)
    return output


_OTIF_GRAIN_CONFIG = {
    "region":    {"id_col": "region_id",    "table": "regions",    "alias": "r",  "name_col": "region_name"},
    "warehouse": {"id_col": "warehouse_id", "table": "warehouses", "alias": "w",  "name_col": "warehouse_name"},
    "route":     {"id_col": "route_id",     "table": "routes",     "alias": "rt", "name_col": "route_name"},
    "outlet":    {"id_col": "outlet_id",    "table": "outlets",    "alias": "ot", "name_col": "outlet_name"},
}


def calculate_otif_by(grain, in_full_threshold=90, start_date="2026-04-01", end_date="2026-06-30", limit=None):
    """
    OTIF at any of the four grains the brief asks for: region, warehouse,
    route, outlet, all with the same definition, same 90% documented threshold, same Q1
    default, one shared query instead of four near-duplicate ones.
    OTIF = delivered in full (eaches fill >= in_full_threshold%) AND on time
    (delay_minutes <= 120). An order with no matching delivery record counts
    as NOT on time, not as a pass. See calculate_otif_by_region's original
    docstring (kept below as a thin wrapper) for the reasoning behind 90%.
    `limit` restricts to the worst N by OTIF%, useful for outlet-grain,
    where there are hundreds of rows and "worst performers visible
    immediately" (the brief's own phrase) matters more than a full list.
    """
    if grain not in _OTIF_GRAIN_CONFIG:
        raise ValueError(f"grain must be one of {list(_OTIF_GRAIN_CONFIG)}")
    cfg = _OTIF_GRAIN_CONFIG[grain]

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(f"""
        WITH active_outlets AS (
            SELECT outlet_id FROM outlets
            WHERE status = 'ACTIVE' AND is_deleted = 0
              AND outlet_id NOT IN (721, 722, 723)
        ),
        q_orders AS (
            SELECT o.order_id, o.{cfg['id_col']} AS grain_id
            FROM orders o
            WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
              AND o.order_date >= '{start_date}' AND o.order_date <= '{end_date}'
              AND o.outlet_id IN (SELECT outlet_id FROM active_outlets)
        ),
        order_fill AS (
            SELECT ol.order_id,
                100.0 * SUM(CASE WHEN ol.qty_uom = 'EACH' THEN ol.delivered_qty
                            ELSE ol.delivered_qty * ol.case_pack_at_order END)
                / NULLIF(SUM(CASE WHEN ol.qty_uom = 'EACH' THEN ol.ordered_qty
                            ELSE ol.ordered_qty * ol.case_pack_at_order END), 0) AS fill_pct
            FROM order_lines ol
            JOIN q_orders q ON ol.order_id = q.order_id
            GROUP BY ol.order_id
        )
        SELECT
            g.{cfg['name_col']},
            COUNT(DISTINCT q.order_id) AS total_orders,
            SUM(CASE WHEN of.fill_pct >= {in_full_threshold}
                     AND d.delay_minutes IS NOT NULL AND d.delay_minutes <= 120
                     THEN 1 ELSE 0 END) AS otif_orders
        FROM q_orders q
        JOIN order_fill of ON q.order_id = of.order_id
        LEFT JOIN deliveries d ON q.order_id = d.order_id
        JOIN {cfg['table']} g ON q.grain_id = g.{cfg['id_col']}
        GROUP BY g.{cfg['id_col']}, g.{cfg['name_col']}
        ORDER BY g.{cfg['name_col']};
    """)

    results = cursor.fetchall()
    connection.close()

    output = []
    for name, total, otif in results:
        pct = otif / total * 100 if total else 0
        output.append({grain: name, "total_orders": total, "otif_orders": otif, "otif_pct": round(pct, 1)})

    if limit:
        output.sort(key=lambda r: r["otif_pct"])
        output = output[:limit]
    return output


def calculate_otif_by_region(in_full_threshold=90, start_date="2026-04-01", end_date="2026-06-30"):
    """
    Illustrative question 2: OTIF by region for the last complete quarter.
    Thin wrapper around calculate_otif_by("region", ...) kept for backward
    compatibility with existing callers; the shared logic lives in
    calculate_otif_by, which also covers warehouse/route/outlet.

    IMPORTANT judgement call: a literal 100% "in full" threshold makes OTIF
    permanently 0% for every region. Checked directly: zero order lines in
    the whole dataset ever have delivered_qty == ordered_qty. 90% is the
    lowest round threshold that produces real differentiation between orders;
    documented in DECISIONS.md as a judgement call, not a fact.
    """
    output = calculate_otif_by("region", in_full_threshold, start_date, end_date)
    return [{"region": r["region"], "total_orders": r["total_orders"],
              "otif_orders": r["otif_orders"], "otif_pct": r["otif_pct"]} for r in output]


def calculate_returns_pct_of_dispatch():
    """
    Explicit pillar-3 ask: "Returns and credit notes as a percentage of
    dispatch value." Dispatch value = order_value_net_inr on delivered/
    partial orders. Returns value = credit_note_value_inr (the real credited
    amount, not a qty*price reconstruction; see DECISIONS.md).
    Both sides now filter to active/non-test outlets, matching fill rate and
    OTIF elsewhere; the original version didn't apply this filter (found
    during review), which was inconsistent even though the effect on the
    resulting percentage was small.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            r.region_name,
            disp.dispatch_value,
            COALESCE(ret.return_value, 0) AS return_value
        FROM regions r
        JOIN (
            SELECT o.region_id, SUM(o.order_value_net_inr) AS dispatch_value
            FROM orders o
            JOIN outlets ot ON o.outlet_id = ot.outlet_id
            WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
              AND ot.status = 'ACTIVE' AND ot.is_deleted = 0
              AND ot.outlet_id NOT IN (721, 722, 723)
            GROUP BY o.region_id
        ) disp ON r.region_id = disp.region_id
        LEFT JOIN (
            SELECT o.region_id, SUM(rc.credit_note_value_inr) AS return_value
            FROM returns_credit_notes rc
            JOIN orders o ON rc.order_id = o.order_id
            JOIN outlets ot ON o.outlet_id = ot.outlet_id
            WHERE ot.status = 'ACTIVE' AND ot.is_deleted = 0
              AND ot.outlet_id NOT IN (721, 722, 723)
            GROUP BY o.region_id
        ) ret ON r.region_id = ret.region_id
        ORDER BY r.region_name;
    """)

    results = cursor.fetchall()
    connection.close()

    output = []
    for region_name, dispatch, returns in results:
        pct = returns / dispatch * 100 if dispatch else 0
        output.append({
            "region": region_name, "dispatch_value": round(dispatch, 2),
            "return_value": round(returns, 2), "return_pct": round(pct, 2),
        })
    return output


def calculate_cold_chain_returns():
    """
    Pillar-2 explicit ask: returns caused by cold-chain failures specifically
    (return_reason_code = 'RT06_COLD_CHAIN_BREACH'), by category.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            p.category,
            COUNT(*) AS return_lines,
            SUM(rc.credit_note_value_inr) AS return_value
        FROM returns_credit_notes rc
        JOIN products p ON rc.product_id = p.product_id
        WHERE rc.return_reason_code = 'RT06_COLD_CHAIN_BREACH'
        GROUP BY p.category
        ORDER BY return_value DESC;
    """)

    results = cursor.fetchall()
    connection.close()

    return [
        {"category": row[0], "return_lines": row[1], "return_value": round(row[2], 2)}
        for row in results
    ]


def calculate_worst_outlets_by_case_fill_rate(start_date, end_date, n=5):
    """
    Illustrative question 1, answered exactly as asked: worst N outlets by
    CASE fill rate (not eaches), for a given month, excluding closed/test
    outlets. Built specifically to answer this question literally; the rest
    of the dashboard reports eaches as primary (Rakesh's override), and this
    is the one place cases is computed and shown.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(f"""
        SELECT ot.outlet_code, ot.outlet_name, ot.city,
            SUM(CASE WHEN ol.qty_uom='CASE' THEN ol.ordered_qty
                     ELSE ol.ordered_qty * 1.0 / ol.case_pack_at_order END) AS ordered_cases,
            SUM(CASE WHEN ol.qty_uom='CASE' THEN ol.delivered_qty
                     ELSE ol.delivered_qty * 1.0 / ol.case_pack_at_order END) AS delivered_cases
        FROM order_lines ol
        JOIN orders o ON ol.order_id = o.order_id
        JOIN outlets ot ON o.outlet_id = ot.outlet_id
        WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
          AND o.order_date >= '{start_date}' AND o.order_date <= '{end_date}'
          AND ot.status = 'ACTIVE' AND ot.is_deleted = 0
          AND ot.outlet_id NOT IN (721, 722, 723)
        GROUP BY ot.outlet_id, ot.outlet_code, ot.outlet_name, ot.city
        HAVING ordered_cases > 0
        ORDER BY delivered_cases * 1.0 / ordered_cases ASC
        LIMIT {n};
    """)

    results = cursor.fetchall()
    connection.close()

    output = []
    for outlet_code, outlet_name, city, ordered, delivered in results:
        fill_rate = delivered / ordered * 100 if ordered else 0
        output.append({
            "outlet_code": outlet_code, "outlet_name": outlet_name, "city": city,
            "ordered_cases": round(ordered, 1), "delivered_cases": round(delivered, 1),
            "case_fill_rate_pct": round(fill_rate, 2),
        })
    return output