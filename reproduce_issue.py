
import sys
import os
import asyncio
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Redirect output to file
log_file = open('d:/fund-advisor/debug_output_3.txt', 'w', encoding='utf-8')
sys.stdout = log_file
sys.stderr = log_file

# Setup logging
logging.basicConfig(level=logging.INFO, stream=log_file)
logger = logging.getLogger(__name__)

from backend.database import get_db
from backend.services.data_fetcher import get_data_fetcher
from backend.services.snapshot import get_snapshot_service

async def test_homepage_stats():
    print("\n=== Testing Homepage Stats ===")
    db = get_db()
    
    # 1. Latest Snapshot
    snapshot = db.get_latest_snapshot()
    if snapshot:
        print(f"Latest Snapshot: date={snapshot['snapshot_date']}, id={snapshot['id']}, status={snapshot.get('status')}")
    else:
        print("Latest Snapshot: None")
        
    # 2. Fund Count
    count = db.get_fund_count()
    print(f"Fund Count in DB: {count}")
    
    # 3. Check Data Fetcher raw count
    fetcher = get_data_fetcher()
    try:
        df = fetcher.get_all_fund_info()
        print(f"Akshare raw fund count: {len(df)}")
        
        # Check unique types
        if '基金类型' in df.columns:
            print(f"Unique types in raw data: {df['基金类型'].unique()}")

        candidates = fetcher.filter_candidate_funds(progress_callback=lambda *args: print(f"Progress: {args}"))
        print(f"Filtered candidates count: {len(candidates)}")
        
    except Exception as e:
        print(f"Data Fetcher Error: {e}")
        import traceback
        traceback.print_exc()

async def test_pk_functionality():
    print("\n=== Testing PK Functionality ===")
    # Simulate valid codes
    codes = "001234,005678" 
    
    # We need to find valid codes first maybe
    db = get_db()
    funds = db.search_funds("", limit=2)
    if len(funds) >= 2:
        codes = f"{funds[0]['code']},{funds[1]['code']}"
        print(f"Using codes: {codes}")
    else:
        print("Not enough funds in DB for PK test")
        return

    # Test logic from query.py's /fund/compare
    try:
        from backend.services.snapshot import get_snapshot_service
        snapshot_service = get_snapshot_service()
        
        code_list = codes.split(',')
        results = []
        for code in code_list:
            print(f"Analyzing {code}...")
            # Simulate what the API does
            analysis = snapshot_service.analyze_single_fund(code)
            if analysis.get('success') or analysis.get('status') == 'success':
                 print(f"Analysis for {code} successful")
            else:
                 print(f"Analysis for {code} failed: {analysis}")
            
    except Exception as e:
        print(f"PK Test Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(test_homepage_stats())
        asyncio.run(test_pk_functionality())
    except Exception as e:
        print(f"Top level error: {e}")
    finally:
        log_file.close()
