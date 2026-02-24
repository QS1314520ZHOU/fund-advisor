import requests
import json
import time

def test_v1_endpoints():
    base_url = "http://localhost:8000/v1"
    
    # Wait for server to be ready
    for i in range(10):
        try:
            requests.get("http://localhost:8000/recommend")
            break
        except:
            time.sleep(2)

    # 1. Test rankings
    print("Testing /v1/rankings...")
    try:
        res = requests.get(f"{base_url}/rankings?sort_by=sharpe&limit=5")
        if res.status_code == 200:
            data = res.json()
            if data.get('status') == 'success':
                print(f"SUCCESS: Received {len(data['data'])} ranked funds.")
                if data['data']:
                    print(f"Top 1: {data['data'][0].get('name')} (Sharpe: {data['data'][0].get('sharpe')})")
            else:
                print(f"API Error: {data.get('message')}")
        else:
            print(f"FAILED: {res.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

    # 2. Test sectors
    print("\nTesting /v1/sectors/hot...")
    try:
        res = requests.get(f"{base_url}/sectors/hot")
        if res.status_code == 200:
            data = res.json()
            if data.get('status') == 'success':
                print(f"SUCCESS: Received {len(data['data'])} hot sectors.")
                if data['data']:
                    print(f"Top Sector: {data['data'][0].get('sector')} (Avg Return: {data['data'][0].get('avg_return')}%)")
            else:
                print(f"API Error: {data.get('message')}")
        else:
            print(f"FAILED: {res.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

    # 3. Test hotspots
    print("\nTesting /v1/market/hotspots...")
    try:
        res = requests.get(f"{base_url}/market/hotspots")
        if res.status_code == 200:
            data = res.json()
            if data.get('status') == 'success':
                print("SUCCESS: Received AI market hotspots summary.")
                print(f"Summary: {data.get('summary', '')[:200]}...")
            else:
                print(f"API Error: {data.get('message')}")
        else:
            print(f"FAILED: {res.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_v1_endpoints()
