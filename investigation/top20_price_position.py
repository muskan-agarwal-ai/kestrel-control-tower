import sqlite3
import re
from pathlib import Path
from html import unescape


DB_PATH = "data/kestrel_ops.db"
BAZAAR_DIR = Path("bazaarpulse_site/city/mumbai")


def normalize(text):
    text = unescape(text).upper()

    text = re.sub(r"\bPACK OF \d+\b", "", text)
    text = re.sub(r"\bCOMBO\b", "", text)
    text = re.sub(r"\bNEW\b", "", text)
    text = re.sub(r"\bBEST BEFORE \d+M\b", "", text)
    text = re.sub(r"\bFAMILY PACK\b", "", text)

    text = re.sub(r"\s+", " ", text).strip()

    return text


def extract_pack_size(name):

    name = name.upper()

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(ML|G|KG|L)",
        name
    )

    if not match:
        return None, None

    value = float(match.group(1))
    unit = match.group(2)

    # Normalize units to base units.
    if unit == "KG":
        value *= 1000
        unit = "G"

    elif unit == "L":
        value *= 1000
        unit = "ML"

    return unit, value


def extract_listings():

    listings = []

    for page in range(1, 18):

        path = BAZAAR_DIR / "page" / f"{page}.html"

        if not path.exists():
            continue

        html = path.read_text(encoding="utf-8")

        cards = re.findall(
            r'<div class="card product-item".*?</div></div>',
            html,
            re.DOTALL
        )

        for card in cards:

            product_match = re.search(
                r'<a href="/product/(\d+)\.html"><strong>(.*?)</strong>',
                card,
                re.DOTALL
            )

            retailer_match = re.search(
                r'<div class="muted">(.*?) &middot;',
                card
            )

            price_match = re.search(
                r'<span class="price">&#8377;([\d.]+)',
                card
            )

            stock_match = re.search(
                r'MRP &#8377;[\d.]+ &middot; (.*?) &middot;',
                card
            )

            last_seen_match = re.search(
                r'Last seen: (\d{4}-\d{2}-\d{2})',
                card
            )

            if not product_match or not price_match:
                continue

            name = unescape(
                product_match.group(2)
            ).strip()

            unit, pack_size = extract_pack_size(name)

            listings.append({
                "product_id": int(product_match.group(1)),
                "name": name,
                "normalized": normalize(name),
                "retailer": (
                    retailer_match.group(1).strip()
                    if retailer_match else ""
                ),
                "price": float(price_match.group(1)),
                "stock": (
                    stock_match.group(1).strip()
                    if stock_match else ""
                ),
                "last_seen": (
                    last_seen_match.group(1)
                    if last_seen_match else ""
                ),
                "pack_unit": unit,
                "pack_size": pack_size,
            })

    return listings


def get_top20():

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            p.sku_code,
            p.product_name,
            p.brand,
            p.category,
            p.list_price_inr,
            p.mrp_inr,
            SUM(ol.line_value_inr) AS sales_value

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
            p.brand,
            p.category,
            p.list_price_inr,
            p.mrp_inr

        ORDER BY
            sales_value DESC

        LIMIT 20
    """)

    rows = cursor.fetchall()

    connection.close()

    return rows


def main():

    print("\nTop 20 SKU Price Position Investigation")
    print("=" * 100)

    listings = extract_listings()
    top20 = get_top20()

    print(f"Mumbai listings: {len(listings):,}")
    print(f"Top-20 SKUs:     {len(top20):,}")

    print("\nKestrel SKUs in Top 20")
    print("=" * 100)

    for row in top20:

        sku, name, brand, category, list_price, mrp, sales_value = row

        if "KESTREL" not in brand.upper():
            continue

        unit, pack_size = extract_pack_size(name)

        print(
            f"\n{sku} | {name}"
        )

        print(
            f"Sales value: ₹{sales_value:,.2f}"
        )

        print(
            f"Kestrel list price: ₹{list_price:,.2f}"
        )

        print(
            f"Pack: {pack_size} {unit}"
        )

        candidates = []

        name_words = [
            w
            for w in normalize(name).split()
            if len(w) >= 4
            and w not in {
                "KESTREL",
                "SELECT"
            }
        ]

        for listing in listings:

            # Pack size must match.
            if (
                unit != listing["pack_unit"]
                or pack_size != listing["pack_size"]
            ):
                continue

            matched = sum(
                1
                for word in name_words
                if word in listing["normalized"]
            )

            if not name_words:
                continue

            score = matched / len(name_words)

            if score >= 0.75:

                candidates.append(
                    (score, listing)
                )

        candidates.sort(
            key=lambda x: x[1]["price"]
        )

        if not candidates:

            print("No validated Mumbai market matches found.")
            continue

        print("\nValidated market matches:")

        for score, listing in candidates[:5]:

            gap = (
                (listing["price"] - list_price)
                / list_price
                * 100
            )

            print(
                f"  {listing['name']}"
            )

            print(
                f"    Retailer: {listing['retailer']}"
            )

            print(
                f"    Market price: ₹{listing['price']:,.2f}"
            )

            print(
                f"    Price gap: {gap:+.2f}%"
            )

            print(
                f"    Match score: {score:.0%}"
            )

            print(
                f"    Stock: {listing['stock']}"
            )

            print(
                f"    Last seen: {listing['last_seen']}"
            )


if __name__ == "__main__":
    main()