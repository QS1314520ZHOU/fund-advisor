
import akshare as ak
import pandas as pd

try:
    print("Fetching fund info sample...")
    df = ak.fund_name_em()
    print("Columns in fund_name_em:")
    print(df.columns)
    print(df.head(1))

    print("\nFetching fund NAV sample (000001)...")
    nav = ak.fund_open_fund_info_em(fund="000001", indicator="单位净值走势")
    print("Columns in fund_open_fund_info_em (NAV):")
    print(nav.columns)
    print(nav.head(1))
    
    print("\nFetching real-time estimation if available...")
    # Trying to find a function for real-time estimation in akshare
    # Usually it is fund_portfolio_hold_em or similar, but let's check what we have.
    # Actually, often 'fund_name_em' might have it, or we need 'fund_em_value_estimation' 
    
    try:
        est = ak.fund_value_estimation_em(symbol="000001")
        print("Columns in fund_value_estimation_em:")
        print(est.columns)
        print(est.head(1))
    except Exception as e:
        print(f"fund_value_estimation_em failed: {e}")

except Exception as e:
    print(f"Error: {e}")
