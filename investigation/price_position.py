import sqlite3
import re
from pathlib import Path
from html import unescape


DB_PATH = "data/kestrel_ops.db"
BAZAAR_DIR = Path("bazaarpulse_site/city/mumbai")


def clean_name(name):
    """
    Normalize product names while KEEPING pack size information.
    """
    name = unescape(name).upper()

    # Normalize common marketplace abbreviations.
    name = name.replace(" SEL.", " SELECT ")
    name = name.replace(" SEL ", " SELECT ")

    # Remove marketplace-only wording.
    name = re.sub(r"\bPACK OF \d+\b", "", name)
    name = re.sub(r"\bCOMBO\b", "", name)
    name = re.sub(r"\bNEW\b", "", name)
    name = re.sub(r"\bBEST BEFORE \d+M\b", "", name)
    name = re.sub(r"\bFAMILY PACK\b", "", name)

    # Normalize whitespace.
    name = re.sub(r"[^A-Z0-9. ]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()

    return name


def extract_pack_size(name):
    """
    Extract pack size and normalize it.

    Examples:
        400g   -> ("WEIGHT", 400)
        1kg    -> ("WEIGHT", 1000)
        500ml  -> ("VOLUME", 500)
        1L     -> ("VOLUME", 1000)
    """

    name = unescape(name).upper()

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(KG|G|ML|L)\b",
        name
    )

    if not match:
        return None

    value = float(match.group(1))
    unit = match.group(2)

    if unit == "KG":
        return "WEIGHT", value * 1000

    if unit == "G":
        return "WEIGHT", value

    if unit == "L":
        return "VOLUME", value * 1000

    if unit == "ML":
        return "VOLUME", value

    return None


def product_words(name):
    """
    Return meaningful product words.

    Brand and SELECT are deliberately ignored because
    BazaarPulse uses abbreviations such as 'Sel.'.
    """

    cleaned = clean_name(name)

    words = cleaned.split()

    ignored = {
        "KESTREL",
        "SELECT",
        "SEL",
    }

    # Remove pack-size tokens.
    result = []

    for word in words:

        if word in ignored:
            continue

        if re.fullmatch(
            r"\d+(?:\.\d+)?(KG|G|ML|L)",
            word
        ):
            continue

        if len(word) >= 3:
            result.append(word)

    return result


def extract_mumbai_listings():

    listings = []

    for page in range(1, 18):

        path = (
            BAZAAR_DIR
            / "page"
            / f"{page}.html"
        )

        if not path.exists():
            continue

        html = path.read_text(
            encoding="utf-8"
        )

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

            mrp_match = re.search(
                r'MRP &#8377;([\d.]+)',
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

            product_id = int(
                product_match.group(1)
            )

            product_name = unescape(
                product_match.group(2)
            ).strip()

            retailer = (
                retailer_match.group(1).strip()
                if retailer_match
                else ""
            )

            price = float(
                price_match.group(1)
            )

            mrp = (
                float(mrp_match.group(1))
                if mrp_match
                else None
            )

            stock = (
                stock_match.group(1).strip()
                if stock_match
                else ""
            )

            last_seen = (
                last_seen_match.group(1)
                if last_seen_match
                else ""
            )

            listings.append({
                "product_id": product_id,
                "product_name": product_name,
                "clean_name": clean_name(product_name),
                "product_words": product_words(product_name),
                "pack_size": extract_pack_size(product_name),
                "retailer": retailer,
                "price": price,
                "mrp": mrp,
                "stock": stock,
                "last_seen": last_seen,
            })

    return listings


def get_kestrel_products():

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            product_id,
            sku_code,
            product_name,
            category,
            list_price_inr,
            mrp_inr
        FROM products
        WHERE
            UPPER(product_name) LIKE '%KESTREL%'
            OR UPPER(brand) LIKE '%KESTREL%'
        ORDER BY product_id
    """)

    rows = cursor.fetchall()

    connection.close()

    return rows


def is_valid_match(
    kestrel_name,
    listing
):
    """
    Strict product matching.

    Requirements:
    1. Pack size must match exactly after unit normalization.
    2. Product words must match.
    3. SELECT is allowed to be abbreviated/omitted by marketplace.
    """

    kestrel_size = extract_pack_size(
        kestrel_name
    )

    listing_size = listing["pack_size"]

    # Pack size is mandatory.
    if not kestrel_size or not listing_size:
        return False

    # 400g must not match 400ml.
    if kestrel_size != listing_size:
        return False

    kestrel_words = product_words(
        kestrel_name
    )

    listing_words = listing["product_words"]

    # Every meaningful Kestrel product word
    # must appear in the BazaarPulse name.
    for word in kestrel_words:

        if word not in listing_words:
            return False

    return True


def main():

    print(
        "BazaarPulse Mumbai Price Investigation"
    )
    print("=" * 80)

    listings = extract_mumbai_listings()

    print(
        f"Mumbai listings found: {len(listings):,}"
    )

    products = get_kestrel_products()

    print(
        f"Kestrel products found: {len(products):,}"
    )

    print(
        "\nValidated Kestrel Price Comparisons"
    )
    print("=" * 80)

    total_matches = 0

    for (
        product_id,
        sku_code,
        product_name,
        category,
        list_price,
        mrp
    ) in products:

        candidates = []

        for listing in listings:

            if not is_valid_match(
                product_name,
                listing
            ):
                continue

            candidates.append(
                listing
            )

        # Lowest observed competitor price
        # is the commercially useful comparison.
        candidates.sort(
            key=lambda x: x["price"]
        )

        for listing in candidates[:3]:

            if list_price:

                gap_pct = (
                    (
                        listing["price"]
                        - list_price
                    )
                    / list_price
                ) * 100

            else:
                gap_pct = None

            total_matches += 1

            print(
                f"\n{sku_code} | {product_name}"
            )

            print(
                f"  BazaarPulse: "
                f"{listing['product_name']}"
            )

            print(
                f"  Retailer:    "
                f"{listing['retailer']}"
            )

            print(
                f"  Kestrel:     "
                f"₹{list_price:.2f}"
            )

            print(
                f"  Market:      "
                f"₹{listing['price']:.2f}"
            )

            if gap_pct is not None:

                print(
                    f"  Price gap:   "
                    f"{gap_pct:+.2f}%"
                )

            print(
                f"  Pack size:   "
                f"{listing['pack_size']}"
            )

            print(
                f"  Stock:       "
                f"{listing['stock']}"
            )

            print(
                f"  Last seen:   "
                f"{listing['last_seen']}"
            )

    print(
        "\n"
        + "=" * 80
    )

    print(
        f"Validated matches: {total_matches:,}"
    )


if __name__ == "__main__":
    main()