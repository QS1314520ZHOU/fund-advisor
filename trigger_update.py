
import sys
import os
import logging
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(os.getcwd())))
sys.path.insert(0, str(Path(os.getcwd()) / "backend"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("="*60)
    print("   FundAdvisor Data Repair Tool")
    print("="*60)
    print("This script will force a full update of all fund data.")
    print("It will skip name filters to ensure ALL funds are captured.")
    print("This may take a few minutes depending on network speed.")
    print("-" * 60)
    
    try:
        from backend.services.snapshot import get_snapshot_service
        service = get_snapshot_service()
        
        print("Starting update... (Target: All Funds, No Filter)")
        
        # Use skip_filter=False to use the new relaxed type filter + name filter (approx 4600 funds)
        # detailed enough for homepage stats but faster than full 10k+ sync
        success, message, _ = service.create_full_snapshot(skip_filter=False)
        
        if success:
            print("\n[SUCCESS] Update completed successfully!")
            print(f"Message: {message}")
            print("Please refresh your web page to see the correct data.")
        else:
            print(f"\n[FAILED] Update failed: {message}")
            
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Make sure you are running this from the project root (d:\\fund-advisor).")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
