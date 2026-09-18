import sys
import os
sys.path.insert(0, os.path.expanduser("~/trading_ai"))
from app import resolve_to_valid_nse_ticker, NSE_UNIVERSE

print(f"Total Tickers in Catalog: {len(NSE_UNIVERSE)}")

test_queries = [
    "zomto", "paytm", "hal", "bel", "trent", "maggi", "fevicol",
    "royal enfield", "tanisq", "airtel", "adani power", "dmart",
    "muthoot", "irctc", "bhel", "siemens", "polycab", "indigo", "vedl"
]
print("\n--- Auto-Correction Tests ---")
for q in test_queries:
    t, c, n = resolve_to_valid_nse_ticker(q)
    print(f"{q:15} -> {t:15} (Auto-corrected: {c})")

