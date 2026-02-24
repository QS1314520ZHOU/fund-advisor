
import akshare as ak
import json

try:
    df = ak.fund_value_estimation_em()
    if df is not None:
        columns = df.columns.tolist()
        print(json.dumps(columns, ensure_ascii=False))
        
        # Also dump first row to see data
        if not df.empty:
            print(json.dumps(df.iloc[0].to_dict(), ensure_ascii=False, default=str))
            
except Exception as e:
    print(f"Error: {e}")
