
import akshare as ak
import sys

sys.setrecursionlimit(2000)

try:
    with open('cols_repr.txt', 'w', encoding='utf-8') as f:
        f.write("Fetching...\n")
        df = ak.fund_value_estimation_em()
        if df is not None:
            f.write("COLUMNS:\n")
            f.write(repr(df.columns.tolist()) + "\n")
            
            if not df.empty:
                f.write("ROW:\n")
                f.write(repr(df.iloc[0].tolist()) + "\n")
            
except Exception as e:
    with open('cols_repr.txt', 'w', encoding='utf-8') as f:
        f.write(f"Error: {e}\n")
