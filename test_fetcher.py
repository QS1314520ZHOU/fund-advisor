
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(os.getcwd())))
sys.path.insert(0, str(Path(os.getcwd()) / "backend"))

try:
    from backend.services.data_fetcher import DataFetcher
    fetcher = DataFetcher()
    code = "024452"
    print(f"Testing get_fund_nav for {code}...")
    df = fetcher.get_fund_nav(code)
    
    if df is not None:
        print(f"Got {len(df)} rows.")
        print("Columns:", df.columns.tolist())
        print("Last row:")
        print(df.iloc[-1].to_dict())
        print("Daily Return Type:", df['daily_return'].dtype)
        
        # Check for future dates
        import datetime
        last_date = df['date'].iloc[-1]
        print(f"Last Date: {last_date}")
        if last_date > datetime.datetime.now() + datetime.timedelta(days=1):
            print("ERROR: Future date detected!")
        else:
            print("Date check passed.")
            
        # Check daily_return value
        ret = df['daily_return'].iloc[-1]
        print(f"Latest Daily Return: {ret}")
    else:
        print("Failed to get data.")

except Exception as e:
    print(f"Error: {e}")
