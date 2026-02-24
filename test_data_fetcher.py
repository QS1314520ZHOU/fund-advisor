
import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

# Setup logging
logging.basicConfig(level=logging.INFO)

try:
    from backend.services.data_fetcher import get_data_fetcher
    
    fetcher = get_data_fetcher()
    print("Fetcher initialized.")
    
    codes = ['014943']
    print(f"Fetching valuation for {codes}...")
    
    result = fetcher.get_realtime_valuation_batch(codes)
    
    print("\nResult:")
    print(result)
    
    if '014943' in result:
        print("\nData for 014943:")
        print(result['014943'])
    else:
        print("\n014943 not found in result.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
