
try:
    print("Attempting to import akshare...")
    import akshare as ak
    print("Import successful. Version:", ak.__version__)
    
    print("Attempting to fetch fund name list...")
    df = ak.fund_name_em()
    print(f"Success! Fetched {len(df)} funds.")
except ImportError as e:
    print("ImportError Details:", e)
except Exception as e:
    print("Other Error:", e)
