import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.roi_review_service import get_roi_service

async def test_roi_structure():
    print("Testing ROI Review Data Structure...")
    service = get_roi_service()
    result = await service.get_historical_roi(limit=5)
    
    if result.get('success'):
        print("✅ ROI fetch success")
        data = result.get('data', {})
        print(f"Total dates found: {len(data)}")
        
        for date, categories in list(data.items())[:1]:
            print(f"Sample Date: {date}")
            for cat, funds in categories.items():
                print(f"  Category {cat}: {len(funds)} funds")
                for f in funds:
                    print(f"    - {f['fund_name']} ({f['fund_code']}): Return {f['return_since_recommend']}%")
    else:
        print(f"❌ ROI fetch failed: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_roi_structure())
