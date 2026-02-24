
import akshare as ak
try:
    df = ak.fund_value_estimation_em()
    print("Columns:", df.columns.tolist())
    print("First row:", df.iloc[0].to_dict())
except Exception as e:
    print("Error:", e)
