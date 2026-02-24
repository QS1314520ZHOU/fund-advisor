
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(os.getcwd())))

try:
    from backend.services.data_fetcher import DataFetcher
    from backend.services.watchlist_service import WatchlistService
    
    fetcher = DataFetcher()
    ws = WatchlistService()
    
    # 1. Test WatchlistService
    print("Testing WatchlistService...")
    test_code = "000001"
    test_name = "华夏成长混合"
    ws.add_to_watchlist(test_code, test_name)
    items = ws.get_watchlist()
    print(f"Watchlist items: {len(items)}")
    found = any(item['code'] == test_code for item in items)
    print(f"Add success: {found}")
    
    # 2. Test DataFetcher Real-time
    print("\nTesting DataFetcher Real-time Valuation...")
    codes = [item['code'] for item in items]
    valuations = fetcher.get_realtime_valuation_batch(codes)
    print(f"Valuations fetched: {len(valuations)}")
    if test_code in valuations:
        print(f"Valuation for {test_code}: {valuations[test_code]}")
    else:
        print(f"Valuation for {test_code} NOT FOUND in cache!")

    # 3. Test Estimation Chart
    print("\nTesting Estimation Chart...")
    chart = fetcher.get_realtime_estimation_chart(test_code)
    print(f"Chart data points: {len(chart)}")
    if chart:
        print(f"First point: {chart[0]}")
        print(f"Last point: {chart[-1]}")

    # Cleanup (optional)
    # ws.remove_from_watchlist(test_code)
    # print("\nCleanup: Removed test code.")

except Exception as e:
    print(f"Error during verification: {e}")
    import traceback
    traceback.print_exc()
