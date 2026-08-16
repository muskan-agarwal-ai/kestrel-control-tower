"""
Kestrel Supply Chain Control Tower
Final Investigation Findings

Data through: 30 June 2026

Purpose:
    Consolidated, evidence-backed findings from the investigation scripts.
    This file is intended to be the single source of truth for the final
    dashboard, recommendations, and FDE presentation.
"""


# ============================================================
# 1. SERVICE PERFORMANCE
# ============================================================

SERVICE = {
    "eligible_orders": 76889,
    "on_time_orders": 48845,
    "on_time_rate_pct": 63.53,

    "ordered_eaches": 97604355,
    "delivered_eaches": 83541379,
    "fill_rate_pct": 85.59,

    "regions": {
        "Central": 85.60,
        "East": 85.61,
        "North": 85.58,
        "South": 85.60,
        "West": 85.57,
    },

    "warehouses": {
        "Bhiwadi DC": 85.58,
        "Bhiwandi DC": 85.61,
        "Butibori DC": 85.53,
        "Chakan DC": 85.67,
        "Dankuni DC": 85.62,
        "Hoskote DC": 85.52,
        "Hyderabad DC": 85.57,
        "Sriperumbudur DC": 85.63,
    },

    "worst_routes": [
        ("Route 123", 84.83),
        ("Route 113", 85.02),
        ("Route 16", 85.08),
        ("Route 15", 85.10),
        ("Route 135", 85.11),
    ],

    "worst_outlets": [
        ("OUT00074", "Anand Mart", 83.73),
        ("OUT00621", "Royal Trading Co", 84.01),
        ("OUT00580", "Green Provision", 84.20),
        ("OUT00717", "Nova Trading Co", 84.23),
        ("OUT00289", "Shree Mart", 84.26),
    ],

    "worst_june_outlets": [
        ("OUT00127", "Metro Supermarket", 74.37),
        ("OUT00113", "Green Enterprises", 74.78),
        ("OUT00698", "Anand Supermarket", 76.74),
        ("OUT00102", "Sri Stores", 78.07),
        ("OUT00092", "Royal Provision", 78.18),
    ],
}


# ============================================================
# 2. OTIF
# ============================================================

OTIF = {
    "eligible_orders": 76889,
    "on_time_orders": 48845,
    "in_full_orders": 0,
    "otif_orders": 0,

    "on_time_rate_pct": 63.53,
    "in_full_rate_pct": 0.00,
    "otif_rate_pct": 0.00,

    "finding": (
        "Every eligible order currently has a quantity shortfall under "
        "the strict equality definition used in the analysis. Therefore "
        "the calculated in-full rate and OTIF rate are 0%. An explicit "
        "business tolerance is required before using OTIF as an operational KPI."
    ),
}


# ============================================================
# 3. RETURNS
# ============================================================

RETURNS = {
    "return_lines": 14000,
    "return_quantity": 154386,
    "return_value_inr": 9580522.97,

    "by_reason": {
        "RT01_NEAR_EXPIRY": 3203099.63,
        "RT02_DAMAGE_TRANSIT": 2070798.69,
        "RT05_OVERSUPPLY": 1563282.32,
        "RT04_QUALITY": 1133934.40,
        "RT03_WRONG_SKU": 1040086.95,
        "RT06_COLD_CHAIN_BREACH": 569320.98,
    },

    "finding": (
        "Near-expiry is the largest return reason by value, followed by "
        "damage in transit."
    ),
}


# ============================================================
# 4. NEAR-EXPIRY INVENTORY
# ============================================================

NEAR_EXPIRY = {
    "inventory_rows": 18894,
    "on_hand_cases": 8525381,
    "available_cases": 6819874,

    "warehouse_available_cases": {
        "Bhiwadi DC": 880827,
        "Bhiwandi DC": 872611,
        "Hoskote DC": 867420,
        "Hyderabad DC": 858985,
        "Butibori DC": 852533,
        "Dankuni DC": 847882,
        "Sriperumbudur DC": 821690,
        "Chakan DC": 817926,
    },

    "finding": (
        "A substantial near-expiry inventory exposure exists. "
        "Available cases are the operationally relevant quantity for "
        "potential sell-through or redistribution actions."
    ),
}


# ============================================================
# 5. COLD CHAIN
# ============================================================

COLD_CHAIN = {
    "total_deliveries": 76889,
    "reefer_deliveries": 17001,
    "temperature_excursions": 2371,
    "reefer_excursions": 537,
    "non_reefer_excursions": 1834,

    "reefer_excursion_rate_pct": 3.16,

    "finding": (
        "537 temperature excursions occurred on reefer deliveries. "
        "However, 1,834 temperature excursion flags are recorded against "
        "non-reefer deliveries, creating a significant data-quality/control "
        "issue that should be investigated before interpreting all excursion "
        "flags as genuine cold-chain failures."
    ),
}


# ============================================================
# 6. FREIGHT
# ============================================================

FREIGHT = {
    "period": "Q1 FY2027 (2026-04-01 to 2026-06-30)",
    "invoice_count": 7113,

    "cost_per_case": {
        "Bhiwandi DC": 276.46,
        "Butibori DC": 280.72,
        "Dankuni DC": 296.20,
        "Chakan DC": 318.83,
        "Hoskote DC": 347.72,
        "Sriperumbudur DC": 363.76,
        "Hyderabad DC": 437.13,
        "Bhiwadi DC": 464.17,
    },

    "finding": (
        "Freight cost per delivered case varies materially across warehouses. "
        "Bhiwadi has the highest observed cost per case and Bhiwandi the lowest. "
        "This is a prioritization signal, not proof of inefficiency, because "
        "route distance, shipment weight, service mix and network design should "
        "be considered before attributing the difference to carrier performance."
    ),
}


# ============================================================
# 7. PRICE POSITION
# ============================================================

PRICE_POSITION = {
    "top_20_sales_value_skus": 20,

    "kestrel_top_20": [
        {
            "sku": "SKU00226",
            "product": "Kestrel Atta 200ml",
            "sales_value_inr": 25483659.88,
            "list_price_inr": 322.20,
            "market_match": "Combo Coastline Atta 200Ml",
            "market_price_inr": 112.40,
            "price_gap_pct": -65.11,
            "confidence": "Directional",
        },
        {
            "sku": "SKU00099",
            "product": "Kestrel Select Juice 400ml",
            "sales_value_inr": 24074588.49,
            "list_price_inr": 341.98,
            "market_match": None,
            "market_price_inr": None,
            "price_gap_pct": None,
            "confidence": "No validated match",
        },
        {
            "sku": "SKU00257",
            "product": "Kestrel Pulses 750ml",
            "sales_value_inr": 23689637.21,
            "list_price_inr": 261.82,
            "market_match": None,
            "market_price_inr": None,
            "price_gap_pct": None,
            "confidence": "No validated match",
        },
    ],

    "finding": (
        "Price-position evidence is currently directional. Only one of the "
        "three Kestrel SKUs in the top-20 sales-value cohort produced a "
        "validated market match, and that match was a combo listing. "
        "Therefore price position should not be presented as a definitive "
        "pricing problem without cleaner like-for-like market matches."
    ),
}


# ============================================================
# 8. DATA QUALITY
# ============================================================

DATA_QUALITY = [
    "1,834 temperature excursion flags are associated with non-reefer deliveries.",
    "Strict OTIF equality produces 0% in-full because every eligible order has a shortfall.",
    "The OTIF metric therefore requires an explicit business tolerance before operational use.",
    "Some product master records contain unusual pack-size values and should be validated before using them for commercial comparisons.",
    "Price comparisons should use like-for-like pack sizes and exclude ambiguous combo listings.",
]


# ============================================================
# 9. PRIORITIZED BUSINESS FINDINGS
# ============================================================

PRIORITIES = [
    {
        "priority": 1,
        "issue": "Low service / fill performance",
        "evidence": "85.59% overall fill rate and 63.53% on-time rate.",
        "action": (
            "Investigate chronic order-line shortages and prioritize the "
            "lowest-performing routes/outlets, especially June deterioration."
        ),
    },
    {
        "priority": 2,
        "issue": "Near-expiry inventory and returns",
        "evidence": (
            "6.82M available near-expiry cases and ₹3.20M of returns "
            "attributed to near-expiry."
        ),
        "action": (
            "Prioritize FEFO execution, inventory redistribution and "
            "sell-through plans for high-risk SKU/warehouse combinations."
        ),
    },
    {
        "priority": 3,
        "issue": "Cold-chain data/control quality",
        "evidence": (
            "537 reefer excursions and 1,834 non-reefer excursion flags."
        ),
        "action": (
            "Validate the excursion logic and telematics mapping before "
            "launching corrective cold-chain interventions."
        ),
    },
    {
        "priority": 4,
        "issue": "Freight cost variation",
        "evidence": (
            "₹276.46–₹464.17 freight cost per delivered case across warehouses."
        ),
        "action": (
            "Benchmark high-cost warehouses against distance, weight, "
            "vehicle type, carrier and route mix."
        ),
    },
]


# ============================================================
# 10. PRINT EXECUTIVE SUMMARY
# ============================================================

def print_summary():

    print("=" * 80)
    print("KESTREL FINAL INVESTIGATION SUMMARY")
    print("=" * 80)

    print("\nSERVICE")
    print(
        f"Fill rate: {SERVICE['fill_rate_pct']:.2f}%"
    )
    print(
        f"On-time rate: {SERVICE['on_time_rate_pct']:.2f}%"
    )

    print("\nINVENTORY / RETURNS")
    print(
        f"Near-expiry available: "
        f"{NEAR_EXPIRY['available_cases']:,} cases"
    )
    print(
        f"Return value: "
        f"₹{RETURNS['return_value_inr']:,.2f}"
    )
    print(
        f"Near-expiry return value: "
        f"₹{RETURNS['by_reason']['RT01_NEAR_EXPIRY']:,.2f}"
    )

    print("\nCOLD CHAIN")
    print(
        f"Reefer excursion rate: "
        f"{COLD_CHAIN['reefer_excursion_rate_pct']:.2f}%"
    )
    print(
        f"Non-reefer excursion flags: "
        f"{COLD_CHAIN['non_reefer_excursions']:,}"
    )

    print("\nFREIGHT")
    print(
        f"Lowest cost/case: "
        f"₹{min(FREIGHT['cost_per_case'].values()):.2f}"
    )
    print(
        f"Highest cost/case: "
        f"₹{max(FREIGHT['cost_per_case'].values()):.2f}"
    )

    print("\nOTIF")
    print(
        f"OTIF rate under strict equality definition: "
        f"{OTIF['otif_rate_pct']:.2f}%"
    )

    print("\nTOP PRIORITIES")

    for item in PRIORITIES:

        print(
            f"\n{item['priority']}. {item['issue']}"
        )

        print(
            f"   Evidence: {item['evidence']}"
        )

        print(
            f"   Action:   {item['action']}"
        )


if __name__ == "__main__":
    print_summary()