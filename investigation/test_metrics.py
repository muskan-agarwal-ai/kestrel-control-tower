import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from metrics import (
    calculate_returns_metrics,
    calculate_returns_by_reason,
    calculate_returns_by_category,
)

from metrics import (
    calculate_returns_metrics,
    calculate_returns_by_reason,
    calculate_returns_by_category,
)


print("Returns")
print("=" * 60)

returns = calculate_returns_metrics()

print(f"Return lines: {returns['return_lines']:,}")
print(f"Return quantity: {returns['return_qty']:,.0f}")
print(f"Return value: ₹{returns['return_value']:,.2f}")


print("\nReturns by Reason")
print("=" * 60)

for row in calculate_returns_by_reason():
    print(
        f"{row['reason']:25} "
        f"₹{row['return_value']:,.2f}"
    )


print("\nReturns by Category")
print("=" * 60)

for row in calculate_returns_by_category():
    print(
        f"{row['category']:20} "
        f"₹{row['return_value']:,.2f}"
    )