"""
Live versions of the freight and price-position analysis, refactored from
investigation/freight_metrics.py and investigation/top20_price_position.py
into reusable functions the dashboard can call directly instead of using a
frozen, hand-copied snapshot of their output.

Both are slow relative to a normal page load (the freight pull walks ~7,100
real invoices through the Partner API's deliberate rate-limiting; the price
pull re-parses the BazaarPulse HTML), so app.py wraps these in
st.cache_data(ttl=...) and a manual refresh button rather than calling them on
every rerun.
"""
import re
import sqlite3
from html import unescape
from pathlib import Path

from integrations.freight_api import fetch_all_invoices

DB_PATH = "data/kestrel_ops.db"
BAZAAR_DIR = Path("bazaarpulse_site/city/mumbai")


# ─── FREIGHT ────────────────────────────────────────────────────────────────

def get_freight_invoices(date_from="2026-04-01", date_to="2026-06-30"):
    """
    Do the actual (slow) Partner API pull once. Both the by-warehouse and
    by-carrier breakdowns are computed from this same result, so the
    dashboard only has to wait through the ~2 minute pull one time, not once
    per breakdown.
    """
    try:
        return fetch_all_invoices(date_from=date_from, date_to=date_to)
    except Exception as e:
        raise ConnectionError(
            f"Could not reach the Partner API at localhost:8088 ({e}). "
            f"Start it with: python partner_api/server.py"
        )


def get_freight_cost_by_warehouse(invoices, date_from="2026-04-01", date_to="2026-06-30"):
    """
    Real, reconciled freight cost per delivered case by warehouse for the given
    date range. Takes an already-fetched invoices list (see
    get_freight_invoices) rather than pulling the API itself.

    Date-basis note (methodological choice, not a bug): the Partner API's
    from/to filter is applied against invoice_date. Delivered cases (the SQL
    below) are filtered on order_date for the same Q1 window. The API also
    exposes a separate service_date (0-4 days before invoice_date) that would
    arguably line up more precisely with when the delivery actually
    happened. Not switched to service_date without a specific reason to,
    per DECISIONS.md; documented here so the mismatch is visible rather than
    assumed away.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            w.warehouse_code,
            w.warehouse_name,
            w.city,
            SUM(
                CASE
                    WHEN ol.qty_uom = 'CASE' THEN ol.delivered_qty
                    ELSE ol.delivered_qty * 1.0 / ol.case_pack_at_order
                END
            ) AS delivered_cases
        FROM order_lines ol
        JOIN orders o ON ol.order_id = o.order_id
        JOIN warehouses w ON o.warehouse_id = w.warehouse_id
        JOIN outlets ot ON o.outlet_id = ot.outlet_id
        WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
          AND o.order_date >= ? AND o.order_date <= ?
          AND ot.status = 'ACTIVE' AND ot.is_deleted = 0
          AND ot.outlet_id NOT IN (721, 722, 723)
        GROUP BY w.warehouse_code, w.warehouse_name, w.city
        ORDER BY delivered_cases DESC;
    """, (date_from, date_to))

    delivered_rows = cursor.fetchall()
    connection.close()

    freight_by_warehouse = {}
    for invoice in invoices:
        wc = invoice["warehouse_code"]
        freight_by_warehouse[wc] = freight_by_warehouse.get(wc, 0) + invoice["amount_inr"]

    results = []
    for warehouse_code, warehouse_name, city, cases in delivered_rows:
        freight = freight_by_warehouse.get(warehouse_code, 0)
        cost_per_case = freight / cases if cases else 0
        results.append({
            "warehouse": warehouse_name,
            "city": city,
            "freight_inr": round(freight, 2),
            "delivered_cases": round(cases, 0),
            "cost_per_case": round(cost_per_case, 2),
        })

    results.sort(key=lambda r: r["cost_per_case"])
    return results


def get_freight_cost_by_carrier(invoices):
    """
    Pillar-3 explicit ask: leakage "by category and by carrier." Category is
    covered elsewhere (metrics.py); this is the carrier half, which was entirely
    missing before, "carrier" only appeared in a caption sentence, not as
    real data, even though every invoice already carries carrier_name.
    Takes an already-fetched invoices list, no second API pull.
    """
    by_carrier = {}
    for invoice in invoices:
        name = invoice["carrier_name"]
        row = by_carrier.setdefault(name, {"invoice_count": 0, "total_freight_inr": 0.0, "detention_inr": 0.0})
        row["invoice_count"] += 1
        row["total_freight_inr"] += invoice["amount_inr"]
        row["detention_inr"] += invoice["detention_charge_inr"]

    results = []
    for carrier, stats in by_carrier.items():
        results.append({
            "carrier": carrier,
            "invoice_count": stats["invoice_count"],
            "total_freight_inr": round(stats["total_freight_inr"], 2),
            "detention_inr": round(stats["detention_inr"], 2),
            "avg_invoice_inr": round(stats["total_freight_inr"] / stats["invoice_count"], 2),
        })
    results.sort(key=lambda r: r["total_freight_inr"], reverse=True)
    return results



# ─── PRICE POSITION ─────────────────────────────────────────────────────────

def _normalize(text):
    text = unescape(text).upper()
    text = re.sub(r"\bPACK OF \d+\b", "", text)
    text = re.sub(r"\bCOMBO\b", "", text)
    text = re.sub(r"\bNEW\b", "", text)
    text = re.sub(r"\bBEST BEFORE \d+M\b", "", text)
    text = re.sub(r"\bFAMILY PACK\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_pack_size(name):
    name = name.upper()
    match = re.search(r"(\d+(?:\.\d+)?)\s*(ML|G|KG|L)", name)
    if not match:
        return None, None
    value = float(match.group(1))
    unit = match.group(2)
    if unit == "KG":
        value *= 1000
        unit = "G"
    elif unit == "L":
        value *= 1000
        unit = "ML"
    return unit, value


def _extract_listings():
    listings = []
    for page in range(1, 18):
        path = BAZAAR_DIR / "page" / f"{page}.html"
        if not path.exists():
            continue
        html = path.read_text(encoding="utf-8")
        cards = re.findall(r'<div class="card product-item".*?</div></div>', html, re.DOTALL)
        for card in cards:
            product_match = re.search(r'<a href="/product/(\d+)\.html"><strong>(.*?)</strong>', card, re.DOTALL)
            retailer_match = re.search(r'<div class="muted">(.*?) &middot;', card)
            price_match = re.search(r'<span class="price">&#8377;([\d.]+)', card)
            stock_match = re.search(r'MRP &#8377;[\d.]+ &middot; (.*?) &middot;', card)
            last_seen_match = re.search(r'Last seen: (\d{4}-\d{2}-\d{2})', card)
            if not product_match or not price_match:
                continue
            name = unescape(product_match.group(2)).strip()
            unit, pack_size = _extract_pack_size(name)
            listings.append({
                "product_id": int(product_match.group(1)),
                "name": name,
                "normalized": _normalize(name),
                "retailer": retailer_match.group(1).strip() if retailer_match else "",
                "price": float(price_match.group(1)),
                "stock": stock_match.group(1).strip() if stock_match else "",
                "last_seen": last_seen_match.group(1) if last_seen_match else "",
                "pack_unit": unit,
                "pack_size": pack_size,
            })
    return listings


def get_top20_price_position():
    """
    Kestrel SKUs within the Top-20 (by Q1 sales value) matched against
    BazaarPulse Mumbai listings. Scope is intentionally limited to Mumbai and
    the Top-20 SKU cohort, matching investigation/top20_price_position.py
    exactly (see DECISIONS.md for why). Match requires same pack unit + size
    AND >=75% overlap of significant name words (brand words excluded). A
    single-generic-word match (e.g. just "ATTA") can still pass this bar and
    should be read as directional, not definitive; flagged per-row below.
    Returns a list of dicts, one per Kestrel SKU in the Top 20.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT
            p.sku_code, p.product_name, p.brand, p.category,
            p.list_price_inr, p.mrp_inr,
            SUM(ol.line_value_inr) AS sales_value
        FROM order_lines ol
        JOIN products p ON ol.product_id = p.product_id
        JOIN orders o ON ol.order_id = o.order_id
        WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
          AND o.order_date >= '2026-04-01' AND o.order_date <= '2026-06-30'
        GROUP BY p.product_id, p.sku_code, p.product_name, p.brand, p.category,
                 p.list_price_inr, p.mrp_inr
        ORDER BY sales_value DESC
        LIMIT 20
    """)
    top20 = cursor.fetchall()
    connection.close()

    listings = _extract_listings()
    results = []

    for sku, name, brand, category, list_price, mrp, sales_value in top20:
        if "KESTREL" not in brand.upper():
            continue

        unit, pack_size = _extract_pack_size(name)
        name_words = [
            w for w in _normalize(name).split()
            if len(w) >= 4 and w not in {"KESTREL", "SELECT"}
        ]

        candidates = []
        for listing in listings:
            if unit != listing["pack_unit"] or pack_size != listing["pack_size"]:
                continue
            if not name_words:
                continue
            matched = sum(1 for w in name_words if w in listing["normalized"])
            score = matched / len(name_words)
            if score >= 0.75:
                candidates.append((score, listing))

        candidates.sort(key=lambda x: x[1]["price"])

        row = {
            "sku": sku, "product_name": name, "sales_value": round(sales_value, 2),
            # Brief says "our MRP against what competitors are actually
            # charging", explicitly, twice. The original version compared
            # against list_price_inr (Kestrel's trade/wholesale price) instead
            # of mrp_inr (the consumer-facing ceiling price), which is the
            # wrong basis for a shelf-price comparison: list_price isn't what
            # any shopper ever pays. Fixed to use mrp_inr as the primary
            # comparison price; list_price kept alongside for reference.
            "kestrel_mrp": round(mrp, 2), "kestrel_list_price": round(list_price, 2),
            "pack": f"{pack_size} {unit}" if unit else None,
            # Flag when the only real distinguishing word is a category/generic
            # term, not a second signal beyond pack size. "200ML" as a "word"
            # is just re-encoding the pack size already matched on separately,
            # so it doesn't count as real specificity here.
            "single_generic_word_match": len([w for w in name_words if not re.match(r"^\d+(ML|G|KG|L)$", w)]) <= 1,
            "best_match": None, "market_price": None, "gap_pct": None,
            "match_retailer": None, "match_score": None,
        }
        if candidates:
            score, best = candidates[0]
            gap = (best["price"] - mrp) / mrp * 100
            row.update({
                "best_match": best["name"],
                "market_price": round(best["price"], 2),
                "gap_pct": round(gap, 2),
                "match_retailer": best["retailer"],
                "match_score": round(score * 100, 0),
            })
        results.append(row)

    return results