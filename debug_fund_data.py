
import akshare as ak
import pandas as pd
import datetime

code = "024452"
print(f"Fetching data for {code}...")

try:
    df = ak.fund_open_fund_info_em(
        symbol=code, 
        indicator="单位净值走势",
        period="成立来"
    )
    
    print("COLUMNS_START")
    print(str(list(df.columns)))
    print("COLUMNS_END")
    
    if len(df) > 0:
        print("FIRST_ROW_START")
        print(str(df.iloc[0].to_dict()))
        print("FIRST_ROW_END")

        
except Exception as e:
    print(f"Error: {e}")
