
import akshare as ak
import pandas as pd

def test_valuation(code):
    print(f"Testing valuation for {code}...")
    try:
        # Some versions of akshare use fund_em_value_estimation
        # Let's try to find the correct function
        try:
            df = ak.fund_value_estimation_em()
            print("Found fund_value_estimation_em (all funds)")
            if df is not None:
                match = df[df['基金代码'] == code]
                if not match.empty:
                    print("Match found for code:")
                    print(match.to_dict(orient='records')[0])
                else:
                    print(f"No match found for code {code}")
            else:
                print("No data returned.")
        except Exception as e:
            print(f"Error calling fund_value_estimation_em: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_valuation("000001") # Huaxia Growth
