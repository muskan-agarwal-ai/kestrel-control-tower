import time
import requests


API_URL = "http://localhost:8088"
API_KEY = "kp_live_7f3a9c21"

HEADERS = {
    "X-API-Key": API_KEY
}


def fetch_all_invoices(
    date_from=None,
    date_to=None,
    limit=200
):
    """
    Fetch all freight invoices from the Kestrel partner API.

    Handles:
    - cursor pagination
    - 429 rate limiting
    - Retry-After
    - 503 temporary failures
    - paise -> INR conversion
    """

    invoices = []
    cursor = None

    while True:

        params = {
            "limit": limit
        }

        if cursor:
            params["cursor"] = cursor

        if date_from:
            params["from"] = date_from

        if date_to:
            params["to"] = date_to

        print(f"Requesting page... cursor={cursor}")

        response = requests.get(
            f"{API_URL}/v1/freight_invoices",
            headers=HEADERS,
            params=params,
            timeout=60
        )

        # Rate limited
        if response.status_code == 429:

            retry_after = int(
                response.headers.get("Retry-After", "2")
            )

            print(
                f"Rate limited. Waiting {retry_after} seconds..."
            )

            time.sleep(retry_after)
            continue

        # Temporary upstream failure
        if response.status_code == 503:

            print(
                "Partner API temporarily unavailable. "
                "Waiting 2 seconds..."
            )

            time.sleep(2)
            continue

        response.raise_for_status()

        payload = response.json()

        page = payload.get("data", [])

        invoices.extend(page)

        print(
            f"Received {len(page)} invoices. "
            f"Total: {len(invoices)}"
        )

        cursor = payload.get("next_cursor")

        if not cursor:
            break

    # Convert paise to INR
    for invoice in invoices:

        invoice["amount_inr"] = (
            invoice["amount"] / 100
        )

        invoice["detention_charge_inr"] = (
            invoice["detention_charge"] / 100
        )

    return invoices


if __name__ == "__main__":

    invoices = fetch_all_invoices()

    print("\n" + "=" * 70)
    print("FREIGHT API TEST")
    print("=" * 70)

    print(f"Total invoices: {len(invoices):,}")

    if invoices:

        invoice = invoices[0]

        print("\nFirst invoice:")

        for key, value in invoice.items():
            print(f"{key}: {value}")