
import asyncio
import logging
import os
import sys
import pandas as pd

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from backend.services.data_fetcher import DataFetcher

logging.basicConfig(level=logging.INFO)

async def test_indices():
    fetcher = DataFetcher()
    
    # Test 1: CSI 300 (SH)
    print("Testing 000300 (SH)...")
    df_300 = fetcher.get_benchmark_data("000300")
    if df_300 is not None:
        print(f"Success: 000300 fetched {len(df_300)} rows.")
    else:
        print("Failed: 000300.")

    # Test 2: Gem Index (SZ 399006)
    print("\nTesting 399006 (SZ)...")
    df_gem = fetcher.get_benchmark_data("399006")
    if df_gem is not None:
        print(f"Success: 399006 fetched {len(df_gem)} rows.")
    else:
        print("Failed: 399006.")

if __name__ == "__main__":
    asyncio.run(test_indices())
