import requests
import json

def test_fund_analysis(code="012414"):
    url = f"http://localhost:8000/analyze/{code}"
    print(f"Testing URL: {url}")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                metrics = data.get('metrics', {})
                print("Analysis Result:")
                print(f"Name: {data.get('name')}")
                print(f"Nav: {metrics.get('nav')}")
                print(f"Latest Nav: {metrics.get('latest_nav')}")
                print(f"Change Percent: {metrics.get('change_percent')}")
                print(f"Return 1d: {metrics.get('return_1d')}")
                
                # Check if fields exist
                missing = []
                if 'nav' not in metrics: missing.append('nav')
                if 'change_percent' not in metrics: missing.append('change_percent')
                
                if not missing:
                    print("\nSUCCESS: All required fields found in metrics.")
                else:
                    print(f"\nFAILURE: Missing fields: {', '.join(missing)}")
            else:
                print(f"Error in response: {data.get('error')}")
        else:
            print(f"HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_fund_analysis()
