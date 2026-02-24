
import akshare as ak
import pandas as pd
import time

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

print("Testing ak.fund_value_estimation_em()...")
try:
    df = ak.fund_value_estimation_em()
    print("Columns:", df.columns.tolist())
    
    match = df[df.iloc[:, 0].astype(str) == '014943'] # Assuming first col is code usually, or check columns
    
    # Try finding code column dynamically like the service does
    cols = df.columns.tolist()
    code_col = next((c for c in cols if '代码' in c), '基金代码')
    print(f"Identified code column: {code_col}")
    
    match = df[df[code_col].astype(str) == '014943']
    
    if not match.empty:
        print("\nFound 014943 row:")
        print(match.iloc[0].to_dict())
    else:
        print("\n014943 not found")
        print("First 3 rows:")
        print(df.head(3))

except Exception as e:
    print(f"Error: {e}")
